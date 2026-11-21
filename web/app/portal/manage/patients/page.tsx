"use client";
import { useEffect,useMemo,useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { useAuth } from "@/components/auth-provider";
import { ArrowLeft,RefreshCw,Search,ShieldCheck,Users } from "lucide-react";
type Patient={id:string;display_label:string;created_at:string};
export default function PatientDirectoryPage(){
 const {user,loading}=useAuth();const [rows,setRows]=useState<Patient[]>([]);const [query,setQuery]=useState("");const [busy,setBusy]=useState(false);
 const load=async()=>{setBusy(true);try{const r=await fetch("/api/backend/api/v1/patients/",{cache:"no-store"});const data=await r.json().catch(()=>[]);if(!r.ok)throw new Error(data?.detail||"Unable to load patient directory");setRows(data);}catch(e){toast.error(e instanceof Error?e.message:"Unable to load patients");}finally{setBusy(false);}};
 useEffect(()=>{if(!loading)void load();},[loading]);
 const filtered=useMemo(()=>rows.filter(x=>(x.display_label+" "+x.id).toLowerCase().includes(query.toLowerCase())),[rows,query]);
 if(loading)return <main className="manage-shell"><div className="manage-empty">Loading…</div></main>;
 return <main className="manage-shell"><header className="manage-topbar"><Link href="/portal/manage" className="manage-brand"><span><Users size={18}/></span>SmartDoctor</Link><Link href="/portal/manage" className="manage-back"><ArrowLeft size={14}/> Workspace</Link></header>
 <div className="manage-layout"><aside className="manage-sidebar"><div className="manage-sidebar-caption">{user?.role?.toUpperCase()||"PATIENT"} WORKSPACE</div><h3>Patient directory</h3><p className="manage-hint">Patients are filtered by your role, clinic membership, care relationship and consent.</p></aside>
 <section className="manage-content"><div className="manage-heading"><div><span className="manage-eyebrow">PATIENT ACCESS</span><h1>Patient directory</h1><p>Only patients your account is authorized to access are listed.</p></div><Link href="/portal/manage" className="manage-secondary">Manage records</Link></div>
 <div className="manage-panel"><div className="manage-toolbar"><b>{rows.length} authorized patients</b><label className="manage-search"><Search size={14}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search patients"/></label><button className="manage-secondary" onClick={()=>void load()}><RefreshCw size={14}/> Refresh</button></div>
 {busy?<div className="manage-empty">Loading patient directory…</div>:!filtered.length?<div className="manage-empty"><Users size={30}/><b>No authorized patient records</b><span>New patient intake is handled by the front desk. Clinicians only see patients with an active care relationship and consent.</span></div>:<div className="manage-table-wrap"><table className="manage-table"><thead><tr><th>Patient</th><th>Patient ID</th><th>Workspace created</th><th>Access</th></tr></thead><tbody>{filtered.map(x=><tr key={x.id}><td><b>{x.display_label}</b></td><td>{x.id}</td><td>{new Date(x.created_at).toLocaleDateString()}</td><td><span className="manage-status"><ShieldCheck size={11}/> Authorized</span></td></tr>)}</tbody></table></div>}</div>
 <p className="manage-security-note"><ShieldCheck size={14}/> Patient directory is read-only here. Create a patient intake request first; verified patient account creation and consent are separate protected workflows.</p>
 </section></div></main>;
}
