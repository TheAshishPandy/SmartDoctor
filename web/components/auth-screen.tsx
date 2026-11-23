"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { motion } from "framer-motion";
import { toast } from "sonner";
import {
  ArrowLeft, ArrowRight, Activity, HeartPulse, ShieldCheck, Sparkles,
  Stethoscope, LockKeyhole, Mail, UserRound, KeyRound,
} from "lucide-react";
import { ThemeToggle } from "./theme-toggle";
import { useAuth } from "./auth-provider";

type Mode = "login" | "register" | "forgot";

function getApiErrorMessage(data: unknown, fallback: string): string {
  if (data && typeof data === "object") {
    const value = data as { detail?: unknown; message?: unknown };
    if (typeof value.detail === "string") return value.detail;
    if (Array.isArray(value.detail)) {
      const messages = value.detail.map((item) => {
        if (item && typeof item === "object" && "msg" in item && typeof item.msg === "string") return item.msg;
        return typeof item === "string" ? item : "";
      }).filter(Boolean);
      if (messages.length) return messages.join("; ");
    }
    if (typeof value.message === "string") return value.message;
  }
  return fallback;
}

export function AuthScreen({ mode }: { mode: Mode }) {
  const router = useRouter();
  const { refreshUser } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [step, setStep] = useState<"form" | "verify" | "reset">("form");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [developmentOtp, setDevelopmentOtp] = useState("");

  const copy = {
    login: ["Welcome back", "Sign in to your private health workspace."],
    register: ["Create your account", "Register securely with your email address."],
    forgot: ["Reset your password", "We’ll email you a one-time password reset code."],
  } as const;
  const heading = copy[mode];
  const goToWorkspace = async () => {
    await refreshUser();
    const requested = new URLSearchParams(window.location.search).get("callbackUrl");
    const destination = requested?.startsWith("/") && !requested.startsWith("//") ? requested : "/";
    router.replace(destination);
  };

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNotice("");
    if (mode === "register" && step === "form" && name.trim().length < 2) { setError("Enter your full name (at least 2 characters)."); return; }
    if ((mode === "register" && step === "form" || mode === "forgot" && step === "reset") && (mode === "register" ? password : newPassword).length < 12) { setError("Password must contain at least 12 characters."); return; }
    if ((mode === "register" && step === "verify" || mode === "forgot" && step === "reset") && !/^\d{6}$/.test(otp)) { setError("Enter the 6-digit verification code."); return; }
    setBusy(true);
    try {
      if (mode === "login") {
        const response = await fetch("/api/auth/login", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(getApiErrorMessage(data, "Unable to sign in"));
        await goToWorkspace();
        return;
      }

      if (mode === "register" && step === "form") {
        const response = await fetch("/api/auth/register", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password, display_name: name }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(getApiErrorMessage(data, "Unable to create account"));
        setDevelopmentOtp(data.development_otp || "");
        if (data.development_otp) setOtp(data.development_otp);
        setStep("verify");
        setNotice(data.development_otp
          ? "Development mode: use the local verification code shown below."
          : "A verification code has been sent to your email address.");
        return;
      }

      if (mode === "register" && step === "verify") {
        const response = await fetch("/api/auth/verify-email", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, code: otp }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(getApiErrorMessage(data, "Code verification failed"));
        const loginResponse = await fetch("/api/auth/login", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });
        if (!loginResponse.ok) throw new Error("Email verified. Please sign in to continue.");
        await goToWorkspace();
        return;
      }

      if (mode === "forgot" && step === "form") {
        const response = await fetch("/api/auth/forgot-password", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(getApiErrorMessage(data, "Unable to request a reset code"));
        setDevelopmentOtp(data.development_otp || "");
        if (data.development_otp) setOtp(data.development_otp);
        setStep("reset");
        setNotice(data.development_otp
          ? "Development mode: use the local reset code shown below."
          : "If the account exists, a password reset code has been sent.");
        return;
      }

      if (mode === "forgot" && step === "reset") {
        const response = await fetch("/api/auth/reset-password", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, code: otp, new_password: newPassword }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(getApiErrorMessage(data, "Password reset failed"));
        toast.success("Password updated. Please sign in.");
        router.replace("/login");
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Something went wrong. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  async function resendCode() {
    setBusy(true);
    setError("");
    try {
      const response = await fetch("/api/auth/resend-otp", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(getApiErrorMessage(data, "Unable to resend code"));
      setDevelopmentOtp(data.development_otp || "");
      if (data.development_otp) setOtp(data.development_otp);
      setNotice(data.development_otp ? "Development code refreshed below." : "If verification is pending, a new code was sent.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to resend code");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-layout">
      <section className="auth-visual">
        <div className="auth-visual-top"><Link href="/" className="brand brand-light"><span className="brand-symbol"><HeartPulse size={19}/></span>smartdoctor</Link><span className="visual-tag"><i/> PRIVATE HEALTH WORKSPACE</span></div>
        <motion.div className="visual-copy" initial={{opacity:0,y:18}} animate={{opacity:1,y:0}} transition={{duration:.6}}>
          <span className="visual-kicker"><Sparkles size={14}/> HEALTH INFORMATION, WITH CONTEXT</span>
          <h1>Care starts with<br/><em>understanding.</em></h1>
          <p>Bring your records together. Find the details that matter. Have more informed conversations with your care team.</p>
        </motion.div>
        <motion.div className="health-illustration" initial={{opacity:0,scale:.92}} animate={{opacity:1,scale:1}} transition={{delay:.12,duration:.65}}>
          <div className="orbit orbit-one"/><div className="orbit orbit-two"/>
          <div className="float-card float-card-a"><span className="float-icon"><Activity size={17}/></span><span><b>Health overview</b><small>Your records, connected</small></span><ShieldCheck size={16}/></div>
          <div className="float-card float-card-b"><span className="float-icon purple"><Sparkles size={17}/></span><span><b>Evidence linked</b><small>Sources with every answer</small></span></div>
          <svg className="doctor-art" viewBox="0 0 430 310" role="img" aria-label="Vector illustration of a clinician and health records">
            <defs><linearGradient id="coat" x1="0" x2="1" y1="0" y2="1"><stop stopColor="#f9ffff"/><stop offset="1" stopColor="#c8e9e5"/></linearGradient><linearGradient id="screen" x1="0" x2="1"><stop stopColor="#c4f0e9"/><stop offset="1" stopColor="#e5e2ff"/></linearGradient></defs>
            <circle cx="215" cy="145" r="126" fill="#fff" opacity=".08"/><circle cx="215" cy="145" r="94" fill="#fff" opacity=".08"/>
            <rect x="34" y="86" width="113" height="115" rx="15" fill="url(#screen)" transform="rotate(-7 34 86)"/><rect x="50" y="106" width="80" height="7" rx="3" fill="#6db9b0" transform="rotate(-7 50 106)"/><rect x="50" y="124" width="58" height="5" rx="2" fill="#94c9c4" transform="rotate(-7 50 124)"/><rect x="50" y="138" width="70" height="5" rx="2" fill="#94c9c4" transform="rotate(-7 50 138)"/>
            <path d="M190 201c4-42 15-70 43-74 34-5 54 24 58 74z" fill="url(#coat)"/><path d="M221 129l15 20 15-20 13 9-13 63h-32l-13-63z" fill="#fff"/><path d="M224 126l12 17 12-17-5-12h-14z" fill="#d79a78"/>
            <ellipse cx="236" cy="92" rx="29" ry="34" fill="#dba17e"/><path d="M207 91c-3-37 18-50 42-40 20 8 23 26 15 45-2-18-12-24-22-27-7 12-19 17-35 17z" fill="#243b4b"/>
            <path d="M208 146l-24 17-17 38h30l18-31zM263 146l26 19 17 36h-30l-18-31z" fill="#e4f7f3"/><path d="M236 146v54" stroke="#75bcb4" strokeWidth="3"/><circle cx="236" cy="163" r="4" fill="#75bcb4"/>
            <rect x="302" y="112" width="75" height="88" rx="12" fill="#fff"/><path d="M323 145h34M340 128v34" stroke="#0e8b80" strokeWidth="7" strokeLinecap="round"/><path d="M318 174h42" stroke="#a5d7d0" strokeWidth="5" strokeLinecap="round"/>
          </svg>
        </motion.div>
        <div className="visual-footer"><span>Built around privacy, clarity and evidence.</span><span>01 — 03</span></div>
      </section>

      <section className="auth-panel">
        <div className="auth-panel-top"><Link href="/" className="mobile-brand"><span className="brand-symbol"><HeartPulse size={18}/></span>smartdoctor</Link><ThemeToggle/><Link href="/" className="back-link"><ArrowLeft size={15}/> Back to home</Link></div>
        <motion.div className="auth-card" initial={{opacity:0,y:14}} animate={{opacity:1,y:0}} transition={{duration:.45}}>
          <div className="auth-icon"><Stethoscope size={21}/></div>
          <p className="auth-eyebrow">SMARTDOCTOR WORKSPACE</p>
          <h2>{mode === "register" && step === "verify" ? "Verify your email" : mode === "forgot" && step === "reset" ? "Choose a new password" : heading[0]}</h2>
          <p className="auth-subtitle">{mode === "register" && step === "verify" ? "Enter the six-digit code sent to your email." : mode === "forgot" && step === "reset" ? "Enter the code from your email and set a new password." : heading[1]}</p>

          <form className="auth-form" onSubmit={submit}>
            {mode === "register" && step === "form" && <label>Full name<div className="input-wrap"><UserRound size={16}/><input autoComplete="name" required minLength={2} maxLength={160} value={name} onChange={e=>setName(e.target.value)} placeholder="Your full name"/></div></label>}
            {(step === "form" || step === "verify" || step === "reset") && <label>Email address<div className="input-wrap"><Mail size={16}/><input type="email" autoComplete="email" required value={email} onChange={e=>setEmail(e.target.value)} placeholder="you@example.com" disabled={step !== "form"}/></div></label>}
            {mode === "login" && <label>Password<div className="input-wrap"><LockKeyhole size={16}/><input type="password" autoComplete="current-password" required value={password} onChange={e=>setPassword(e.target.value)} placeholder="Your password"/></div></label>}
            {mode === "register" && step === "form" && <label>Password <span className="field-hint">(at least 12 characters)</span><div className="input-wrap"><LockKeyhole size={16}/><input type="password" autoComplete="new-password" required minLength={12} maxLength={128} value={password} onChange={e=>setPassword(e.target.value)} placeholder="Create a strong password"/></div></label>}
            {(mode === "register" && step === "verify" || mode === "forgot" && step === "reset") && <label>6-digit verification code<div className="input-wrap"><KeyRound size={16}/><input inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength={6} required value={otp} onChange={e=>setOtp(e.target.value.replace(/\D/g,"").slice(0,6))} placeholder="000000"/></div></label>}
            {mode === "forgot" && step === "reset" && <label>New password<div className="input-wrap"><LockKeyhole size={16}/><input type="password" autoComplete="new-password" minLength={12} maxLength={128} required value={newPassword} onChange={e=>setNewPassword(e.target.value)} placeholder="At least 12 characters"/></div></label>}
            {error && <div className="error-banner" role="alert">{error}</div>}
            {notice && <div className="auth-notice" role="status">{notice}{developmentOtp && <strong className="development-code">Local code: {developmentOtp}</strong>}</div>}
            <button className="primary-button full-button" type="submit" disabled={busy}>
              {busy ? "Please wait…" : mode === "login" ? "Sign in securely" : mode === "register" && step === "form" ? "Create account" : mode === "register" ? "Verify and continue" : mode === "forgot" && step === "form" ? "Send reset code" : "Reset password"}
              <ArrowRight size={16}/>
            </button>
          </form>

          {mode === "register" && step === "verify" && <button className="text-link" type="button" onClick={()=>void resendCode()} disabled={busy}>Resend verification code</button>}
          {mode === "login" && <p className="auth-inline"><span/> <Link href="/forgot-password">Forgot password?</Link></p>}
          {mode === "login" && <p className="auth-switch">New to SmartDoctor? <Link href="/register">Create an account</Link></p>}
          {mode === "register" && <p className="auth-switch">Already have an account? <Link href="/login">Sign in</Link></p>}
          {mode === "forgot" && <p className="auth-switch"><Link href="/login">Back to sign in</Link></p>}
          <div className="auth-trust"><ShieldCheck size={15}/><span>Passwords are hashed. Session tokens use secure HTTP-only cookies.</span></div>
        </motion.div>
        <p className="auth-legal">Use SmartDoctor with synthetic data only until production security and clinical validation are complete.</p>
      </section>
    </main>
  );
}
