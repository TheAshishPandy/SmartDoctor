"use client";
import Link from "next/link";
import { signOut, useSession } from "next-auth/react";
import { LogOut, UserRound } from "lucide-react";

export function SessionControls() {
  const { data, status } = useSession();
  if (status === "loading") return <span className="session-loading" aria-label="Loading session"/>;
  if (!data?.user) return <Link className="signin-link" href="/login">Sign in</Link>;
  return (
    <div className="session-controls">
      <span className="session-user"><UserRound size={14}/>{data.user.name || data.user.email || "Account"}</span>
      <button className="signout-button" onClick={() => void signOut({ callbackUrl: "/login" })} title="Sign out" aria-label="Sign out"><LogOut size={15}/></button>
    </div>
  );
}

export function SignOutButton() {
  return <button className="signout-button" onClick={() => void signOut({ callbackUrl: "/login" })}><LogOut size={15}/> Sign out</button>;
}