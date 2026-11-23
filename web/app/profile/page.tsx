"use client";

import Link from "next/link";
import { ArrowLeft, ShieldCheck, UserRound } from "lucide-react";
import { SignOutButton } from "../../components/session-controls";
import { useAuth } from "../../components/auth-provider";

export default function ProfilePage() {
  const { user, loading } = useAuth();
  const name = user?.display_name || "Local demo patient";
  const email = user?.email || "Synthetic demo identity";
  const authenticated = Boolean(user);
  return (
    <main className="simple-page">
      <Link href="/" className="back-link"><ArrowLeft size={15}/> Workspace</Link>
      <div className="simple-heading">
        <span className="simple-icon"><UserRound/></span>
        <p className="eyebrow">YOUR ACCOUNT</p><h1>My profile</h1>
        <p>Your SmartDoctor account and access details.</p>
      </div>
      <section className="simple-card">
        <div><UserRound/><span><b>{loading ? "Loading account…" : name}</b><small>{email}</small></span><strong className="status-chip">{authenticated ? "Authenticated" : "Development demo"}</strong></div>
        {user && <div><ShieldCheck/><span><b>Account role</b><small>{user.role.charAt(0).toUpperCase() + user.role.slice(1)}</small></span></div>}
        <div><ShieldCheck/><span><b>Session security</b><small>{authenticated ? "FastAPI-issued access token in an HTTP-only cookie with a rotating refresh session." : "Development-only synthetic identity. Do not use real patient information."}</small></span></div>
        {authenticated && <div><span><b>Sign out</b><small>End this session on the current device.</small></span><SignOutButton/></div>}
      </section>
    </main>
  );
}
