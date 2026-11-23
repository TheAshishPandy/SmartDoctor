"use client";
import Link from "next/link";
import { LogOut, UserRound } from "lucide-react";
import { useAuth } from "./auth-provider";

export function SessionControls() {
  const { user, loading, signOut } = useAuth();
  if (loading) return <span className="session-loading" aria-label="Loading session" />;
  if (!user) return <Link className="signin-link" href="/login">Sign in</Link>;
  return (
    <div className="session-controls">
      <span className="session-user"><UserRound size={14}/>{user.display_name || user.email}</span>
      <button className="signout-button" onClick={() => void signOut()} title="Sign out" aria-label="Sign out"><LogOut size={15}/></button>
    </div>
  );
}

export function SignOutButton() {
  const { signOut } = useAuth();
  return <button className="signout-button" onClick={() => void signOut()}><LogOut size={15}/> Sign out</button>;
}
