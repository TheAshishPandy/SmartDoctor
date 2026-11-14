"use client";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowLeft,ArrowRight,Activity,Eye,EyeOff,HeartPulse,LockKeyhole,Mail,ShieldCheck,Sparkles,Stethoscope } from "lucide-react";
import { useState } from "react";
import { ThemeToggle } from "./theme-toggle";
type Mode="login"|"register"|"forgot";
export function AuthScreen({mode}:{mode:Mode}) {
 const [show,setShow]=useState(false); const [notice,setNotice]=useState("");
 const copy={login:["Welcome back","Your health story, all in one place."],register:["Create your account","A calmer, clearer way to manage health information."],forgot:["Reset your password","We’ll help you get back to your workspace."]};
 const heading=copy[mode];
 return <main className="auth-layout">
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
    <div className="auth-icon"><Stethoscope size={21}/></div><p className="auth-eyebrow">SMARTDOCTOR WORKSPACE</p><h2>{heading[0]}</h2><p className="auth-subtitle">{heading[1]}</p>
    {mode==="login"&&<><form className="auth-form" onSubmit={e=>{e.preventDefault();setNotice("This build is configured for local demo access. Use the demo button below to open the synthetic patient workspace.");}}>
      <label>Email address<div className="input-wrap"><Mail size={17}/><input type="email" placeholder="you@example.com" required/></div></label>
      <label>Password<div className="input-wrap"><LockKeyhole size={17}/><input type={show?"text":"password"} placeholder="Enter your password" required minLength={8}/><button type="button" className="reveal-button" onClick={()=>setShow(!show)} aria-label="Toggle password visibility">{show?<EyeOff size={16}/>:<Eye size={16}/>}</button></div></label>
      <div className="auth-inline"><label className="remember"><input type="checkbox"/> Remember me</label><Link href="/forgot-password">Forgot password?</Link></div>
      <button className="primary-button full-button" type="submit">Sign in <ArrowRight size={16}/></button>
     </form>{notice&&<div className="auth-notice">{notice}</div>}<div className="auth-divider"><span>OR</span></div><Link className="demo-button" href="/">Continue with local demo <ArrowRight size={16}/></Link><p className="auth-switch">New to SmartDoctor? <Link href="/register">Create an account</Link></p></>}
    {mode==="register"&&<><form className="auth-form" onSubmit={e=>{e.preventDefault();setNotice("Registration is not connected yet. Configure an OIDC identity provider before creating real accounts.");}}>
      <label>Full name<div className="input-wrap"><input placeholder="Your full name" required/></div></label><label>Email address<div className="input-wrap"><Mail size={17}/><input type="email" placeholder="you@example.com" required/></div></label><label>Create password<div className="input-wrap"><LockKeyhole size={17}/><input type="password" placeholder="At least 8 characters" minLength={8} required/></div></label><button className="primary-button full-button" type="submit">Create account <ArrowRight size={16}/></button>
     </form>{notice&&<div className="auth-notice">{notice}</div>}<p className="auth-switch">Already have an account? <Link href="/login">Sign in</Link></p></>}
    {mode==="forgot"&&<><form className="auth-form" onSubmit={e=>{e.preventDefault();setNotice("Password recovery is not enabled in this development build. Connect an OIDC provider to activate recovery.");}}><label>Email address<div className="input-wrap"><Mail size={17}/><input type="email" placeholder="you@example.com" required/></div></label><button className="primary-button full-button" type="submit">Send recovery link <ArrowRight size={16}/></button></form>{notice&&<div className="auth-notice">{notice}</div>}<p className="auth-switch"><Link href="/login">Back to sign in</Link></p></>}
    <div className="auth-trust"><ShieldCheck size={15}/><span>Your information stays private to your authorized workspace.</span></div>
   </motion.div>
   <p className="auth-legal">By continuing, you agree to our <a href="#terms">Terms</a> and <a href="#privacy">Privacy Policy</a>.</p>
  </section>
 </main>;
}