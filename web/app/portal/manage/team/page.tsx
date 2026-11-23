"use client";
import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { useAuth } from "@/components/auth-provider";
import { ArrowLeft, Building2, Plus, ShieldCheck, Trash2, Users } from "lucide-react";

type Membership={id:string;user_id:string;display_name:string;email:string|null;role:string;status:string;created_at:string};
type Account={id:string;email:string;display_name:string;role:string;is_verified:boolean;is_active:boolean};
const API="/api/backend/api/v1/workspace";
export default function TeamRolesPage(){
 const {user,loading}=useAuth();
 const [items,setItems]=useState<Membership[]>([]);
 const [accounts,setAccounts]=useState<Account[]>([]);
 const [clinic,setClinic]=useState("SmartDoctor Clinic");
 const [userId,setUserId]=useState("");
 const [role,setRole]=useState("doctor");
 const [busy,setBusy]=useState(false);
 const call=useCallback(async(path:string,init?:RequestInit)=>{const r=await fetch(API+path,{...init,headers:{...(init?.body?{"content-type":"application/json"}:{}),...init?.headers},cache:"no-store"});const data=r.status===204?null:await r.json().catch(()=>null);if(!r.ok)throw new Error(data?.detail||"Request failed");return data;},[]);
 const load=useCallback(async()=>{try{setItems(await call("/memberships"));}catch(e){if(e instanceof Error&&e.message.includes("membership"))return;toast.error(e instanceof Error?e.message:"Unable to load team");}},[call]);
 const loadAccounts=useCallback(async()=>{try{const response=await fetch("/api/auth/users",{cache:"no-store"});const data=await response.json().catch(()=>[]);if(!response.ok)throw new Error(data?.detail||"Unable to load accounts");setAccounts(data.filter((x:Account)=>x.is_verified&&x.is_active));}catch(e){toast.error(e instanceof Error?e.message:"Unable to load accounts");}},[]);
 useEffect(()=>{if(user?.role==="admin"){void load();void loadAccounts();}},[user,load,loadAccounts]);
 const setup=async(e:FormEvent)=>{e.preventDefault();setBusy(true);try{await call("/organization/bootstrap",{method:"POST",body:JSON.stringify({name:clinic})});toast.success("Clinic workspace is ready.");await load();}catch(e){toast.error(e instanceof Error?e.message:"Unable to set up clinic");}finally{setBusy(false);}};
 const add=async(e:FormEvent)=>{e.preventDefault();setBusy(true);try{const roleResponse=await fetch("/api/auth/users/"+userId+"/role",{method:"PATCH",headers:{"content-type":"application/json"},body:JSON.stringify({role})});const roleResult=await roleResponse.json().catch(()=>null);if(!roleResponse.ok)throw new Error(roleResult?.detail||"Unable to update account role");await call("/memberships",{method:"POST",body:JSON.stringify({user_id:userId,role})});setUserId("");toast.success("Account role and clinic access assigned.");await load();}catch(e){toast.error(e instanceof Error?e.message:"Unable to assign access");}finally{setBusy(false);}};
 const revoke=async(id:string)=>{if(!confirm("Revoke this clinic membership?"))return;try{await call("/memberships/"+id,{method:"DELETE"});toast.success("Membership revoked.");await load();}catch(e){toast.error(e instanceof Error?e.message:"Unable to revoke membership");}};
 if(loading)return <main className="manage-shell"><p className="manage-empty">Loading…</p></main>;
 if(user?.role!=="admin")return <main className="manage-shell"><div className="manage-panel"><h1>Administrator access required</h1><Link href="/portal">Return to dashboard</Link></div></main>;
 return <main className="manage-shell"><header className="manage-topbar"><Link href="/portal" className="manage-brand"><span><Building2 size={18}/></span>SmartDoctor</Link><Link href="/portal/manage" className="manage-back"><ArrowLeft size={14}/> Workspace</Link></header>
 <div className="manage-layout"><aside className="manage-sidebar"><div className="manage-sidebar-caption">ADMIN WORKSPACE</div><h3>People & access</h3><p className="manage-hint">Clinic team membership</p><div className="manage-sidebar-foot"><ShieldCheck size={14}/> Role and clinic access are checked by FastAPI.</div></aside>
 <section className="manage-content"><div className="manage-heading"><div><span className="manage-eyebrow">SECURITY & ACCESS</span><h1>Team & roles</h1><p>Set up your clinic and assign registered users to clinic roles.</p></div></div>
 <div className="manage-panel"><h2 className="manage-subtitle">Clinic workspace</h2><form className="manage-inline-form" onSubmit={setup}><label>Clinic name<input value={clinic} onChange={e=>setClinic(e.target.value)} required minLength={2}/></label><button className="manage-primary" disabled={busy}><Building2 size={15}/> Set up clinic</button></form><p className="manage-form-hint">The first setup creates an administrator membership for your signed-in account. Existing admin memberships are reused.</p></div>
 <div className="manage-panel" style={{marginTop:16}}><h2 className="manage-subtitle">Assign a team member</h2><form className="manage-inline-form" onSubmit={add}><label>Registered account<select value={userId} onChange={e=>setUserId(e.target.value)} required><option value="">Select a verified user</option>{accounts.map(account=><option key={account.id} value={account.id}>{account.display_name} · {account.email} · {account.role}</option>)}</select></label><label>Clinic role<select value={role} onChange={e=>setRole(e.target.value)}><option value="doctor">Doctor</option><option value="receptionist">Receptionist</option><option value="admin">Admin</option></select></label><button className="manage-primary" disabled={busy}><Plus size={15}/> Assign access</button></form><p className="manage-form-hint">The user must already have a verified account and the matching account role. Patients are not assigned clinic memberships.</p></div>
 <div className="manage-panel" style={{marginTop:16}}><div className="manage-toolbar"><h2 className="manage-subtitle"><Users size={17}/> Clinic memberships</h2><button className="manage-secondary" onClick={()=>void load()}>Refresh</button></div>{!items.length?<div className="manage-empty"><Users size={28}/><b>No memberships loaded</b><span>Set up your clinic or refresh after assigning a member.</span></div>:<div className="manage-table-wrap"><table className="manage-table"><thead><tr><th>Member</th><th>Email</th><th>Role</th><th>Status</th><th>Action</th></tr></thead><tbody>{items.map(x=><tr key={x.id}><td><b>{x.display_name}</b><small>{x.user_id}</small></td><td>{x.email||"—"}</td><td>{x.role==="clinician"?"Doctor":x.role}</td><td><span className="manage-status">{x.status}</span></td><td><button className="manage-row-actions danger" onClick={()=>void revoke(x.id)} disabled={x.user_id===user?.id} aria-label="Revoke membership"><Trash2 size={14}/></button></td></tr>)}</tbody></table></div>}</div>
 <p className="manage-security-note"><ShieldCheck size={14}/> Changing an account role is separate from granting clinic membership. Both checks must pass for staff access.</p>
 </section></div></main>;
}
