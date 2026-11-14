import Link from "next/link";
import { ArrowLeft, ShieldCheck, UserRound } from "lucide-react";
import { auth } from "../../auth";
import { SignOutButton } from "../../components/session-controls";

export default async function ProfilePage() {
  const session = await auth();
  const name = session?.user?.name || "Local demo patient";
  const email = session?.user?.email || "Synthetic demo identity";
  const authenticated = Boolean(session?.user);
  return (
    <main className="simple-page">
      <Link href="/" className="back-link"><ArrowLeft size={15}/> Workspace</Link>
      <div className="simple-heading">
        <span className="simple-icon"><UserRound/></span>
        <p className="eyebrow">YOUR ACCOUNT</p><h1>My profile</h1>
        <p>Identity details from your configured sign-in provider.</p>
      </div>
      <section className="simple-card">
        <div><UserRound/><span><b>{name}</b><small>{email}</small></span><strong className="status-chip">{authenticated ? "Authenticated" : "Local demo"}</strong></div>
        <div><ShieldCheck/><span><b>Session security</b><small>{authenticated ? "Signed in through OpenID Connect. Tokens are held in an encrypted, HTTP-only server session." : "Development-only synthetic identity. Do not use real patient information."}</small></span></div>
        {authenticated && <div><span><b>Sign out</b><small>End this session on the current device.</small></span><SignOutButton/></div>}
      </section>
    </main>
  );
}