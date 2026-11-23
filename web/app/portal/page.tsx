"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/auth-provider";
import Image from "next/image";
import {
  Activity, CalendarDays, ClipboardList, FileText, HeartPulse, LayoutDashboard,
  Search, ShieldCheck, Stethoscope, Users, UserRound, Clock3,
  Pill, Settings, Bell, ArrowUpRight, CheckCircle2, AlertCircle,
  Building2, ClipboardCheck, UserPlus, CalendarCheck, ChartNoAxesCombined,
  GripVertical, Plus, X, RefreshCw, BarChart3, PieChart, TrendingUp, PanelLeftClose, PanelLeftOpen,
} from "lucide-react";

type Role = "patient" | "doctor" | "admin" | "receptionist";
type Section = "overview" | "patients" | "appointments" | "records" | "team" | "audit";

const roles: { id: Role; label: string; icon: typeof UserRound; greeting: string; subtitle: string }[] = [
  { id: "patient", label: "Patient", icon: UserRound, greeting: "Good morning, Alex", subtitle: "Your personal health overview and upcoming care." },
  { id: "doctor", label: "Doctor", icon: Stethoscope, greeting: "Good morning, Dr. Chen", subtitle: "Your clinical workspace, patient panel and today's schedule." },
  { id: "admin", label: "Admin", icon: ShieldCheck, greeting: "Good morning, Jordan", subtitle: "Clinic operations, team activity and platform overview." },
  { id: "receptionist", label: "Receptionist", icon: ClipboardCheck, greeting: "Good morning, Taylor", subtitle: "Front desk overview, patient check-ins and appointment coordination." },
];

const appointments = [
  { id:"APT-2041", patient:"Olivia Bennett", initials:"OB", doctor:"Dr. Maya Chen", date:"Today · 09:30 AM", type:"Follow-up", status:"Confirmed" },
  { id:"APT-2042", patient:"Noah Williams", initials:"NW", doctor:"Dr. Ethan Patel", date:"Today · 10:15 AM", type:"Consultation", status:"Checked in" },
  { id:"APT-2043", patient:"Ava Thompson", initials:"AT", doctor:"Dr. Maya Chen", date:"Today · 11:00 AM", type:"Lab review", status:"Pending" },
  { id:"APT-2044", patient:"Liam Garcia", initials:"LG", doctor:"Dr. Sarah Kim", date:"Today · 01:30 PM", type:"Follow-up", status:"Confirmed" },
  { id:"APT-2045", patient:"Sophia Martin", initials:"SM", doctor:"Dr. Ethan Patel", date:"Tomorrow · 09:00 AM", type:"Consultation", status:"Confirmed" },
  { id:"APT-2046", patient:"Ethan Davis", initials:"ED", doctor:"Dr. Sarah Kim", date:"Tomorrow · 10:30 AM", type:"New patient", status:"Pending" },
];
const patients = [
  { name:"Olivia Bennett", initials:"OB", id:"PT-10042", age:34, last:"Today, 09:30 AM", doctor:"Maya Chen", status:"Active" },
  { name:"Noah Williams", initials:"NW", id:"PT-10039", age:51, last:"Today, 10:15 AM", doctor:"Ethan Patel", status:"Active" },
  { name:"Ava Thompson", initials:"AT", id:"PT-10035", age:27, last:"Yesterday", doctor:"Maya Chen", status:"Review" },
  { name:"Liam Garcia", initials:"LG", id:"PT-10028", age:43, last:"Yesterday", doctor:"Sarah Kim", status:"Active" },
  { name:"Sophia Martin", initials:"SM", id:"PT-10021", age:62, last:"Nov 18, 2026", doctor:"Ethan Patel", status:"Active" },
];
const records = [
  { title:"Complete Blood Count", patient:"Olivia Bennett", kind:"Lab report", date:"Nov 20, 2026", status:"Reviewed" },
  { title:"Annual health assessment", patient:"Noah Williams", kind:"Clinical note", date:"Nov 20, 2026", status:"Pending" },
  { title:"Lipid panel", patient:"Ava Thompson", kind:"Lab report", date:"Nov 19, 2026", status:"Reviewed" },
  { title:"Medication reconciliation", patient:"Liam Garcia", kind:"Medication", date:"Nov 19, 2026", status:"Reviewed" },
];
const staff = [
  { name:"Maya Chen", initials:"MC", role:"Cardiology", email:"maya.chen@smartdoctor-demo.com", status:"Active" },
  { name:"Ethan Patel", initials:"EP", role:"Internal medicine", email:"ethan.patel@smartdoctor-demo.com", status:"Active" },
  { name:"Sarah Kim", initials:"SK", role:"Family medicine", email:"sarah.kim@smartdoctor-demo.com", status:"Active" },
  { name:"Taylor Reed", initials:"TR", role:"Receptionist", email:"taylor.reed@smartdoctor-demo.com", status:"Active" },
  { name:"Morgan Lee", initials:"ML", role:"Receptionist", email:"morgan.lee@smartdoctor-demo.com", status:"Invited" },
];
const audit = [
  { action:"Patient appointment checked in", actor:"Taylor Reed", scope:"PT-10039", time:"Today, 10:12 AM", status:"Allowed" },
  { action:"Clinical record viewed", actor:"Dr. Maya Chen", scope:"PT-10042", time:"Today, 09:42 AM", status:"Allowed" },
  { action:"Consent verified for record access", actor:"System", scope:"PT-10042", time:"Today, 09:41 AM", status:"Allowed" },
  { action:"Role change attempted", actor:"Taylor Reed", scope:"User management", time:"Yesterday, 04:18 PM", status:"Denied" },
];

const navByRole: Record<Role, { id: Section; label: string; icon: typeof LayoutDashboard }[]> = {
  patient: [{id:"overview",label:"Overview",icon:LayoutDashboard},{id:"appointments",label:"My appointments",icon:CalendarDays},{id:"records",label:"Medical records",icon:FileText}],
  doctor: [{id:"overview",label:"Overview",icon:LayoutDashboard},{id:"patients",label:"My patients",icon:Users},{id:"appointments",label:"Schedule",icon:CalendarDays},{id:"records",label:"Clinical records",icon:FileText}],
  admin: [{id:"overview",label:"Overview",icon:LayoutDashboard},{id:"patients",label:"Patients",icon:Users},{id:"appointments",label:"Appointments",icon:CalendarDays},{id:"team",label:"Team & roles",icon:Building2},{id:"records",label:"Clinical records",icon:FileText},{id:"audit",label:"Audit activity",icon:ShieldCheck}],
  receptionist: [{id:"overview",label:"Front desk",icon:LayoutDashboard},{id:"patients",label:"Patient directory",icon:Users},{id:"appointments",label:"Appointments",icon:CalendarDays}],
};

const metrics: Record<Role, { label:string; value:string; note:string; icon:string }[]> = {
  patient:[{label:"Upcoming appointments",value:"2",note:"Next: Today at 09:30 AM",icon:"calendar"},{label:"Medical records",value:"8",note:"2 added this month",icon:"records"},{label:"Active medications",value:"3",note:"Last reconciled Nov 18",icon:"pill"},{label:"Care team",value:"2",note:"Your connected clinicians",icon:"team"}],
  doctor:[{label:"Assigned patients",value:"48",note:"+4 this month",icon:"patients"},{label:"Appointments today",value:"12",note:"4 remaining",icon:"calendar"},{label:"Records to review",value:"7",note:"3 marked priority",icon:"records"},{label:"Care plan follow-ups",value:"9",note:"Across 6 patients",icon:"activity"}],
  admin:[{label:"Total patients",value:"1,284",note:"+8.2% this quarter",icon:"patients"},{label:"Clinical staff",value:"24",note:"21 active · 3 invited",icon:"team"},{label:"Appointments today",value:"86",note:"72 confirmed",icon:"calendar"},{label:"Pending reviews",value:"18",note:"Across 4 departments",icon:"records"}],
  receptionist:[{label:"Today's appointments",value:"86",note:"Across 8 clinicians",icon:"calendar"},{label:"Checked in",value:"24",note:"6 currently waiting",icon:"patients"},{label:"Awaiting confirmation",value:"11",note:"4 need a call back",icon:"activity"},{label:"New registrations",value:"5",note:"Since clinic opened",icon:"team"}],
};

function MetricIcon({name}:{name:string}) {
  if(name==="calendar") return <CalendarDays size={15}/>;
  if(name==="records") return <FileText size={15}/>;
  if(name==="pill") return <Pill size={15}/>;
  if(name==="team") return <Users size={15}/>;
  if(name==="activity") return <Activity size={15}/>;
  return <UserRound size={15}/>;
}
function Status({value}:{value:string}) {
  const cls=value==="Pending"||value==="Invited"?"pending":value==="Review"?"review":value==="Cancelled"?"cancelled":"";
  return <span className={`portal-status ${cls}`}>{value}</span>;
}

type WidgetLayout = { width:number; height:number; order:number };
function EditableWidget({id,editMode,layout,onResize,onMove,children,className=""}:{id:string;editMode:boolean;layout:WidgetLayout;onResize:(id:string,axis:"width"|"height",delta:number)=>void;onMove:(from:string,to:string)=>void;children:React.ReactNode;className?:string}) {
  return <div className={"portal-editable "+(editMode?"is-editing ":"")+className} style={{"--widget-width":layout.width,"--widget-height":layout.height,order:layout.order} as React.CSSProperties} draggable={editMode}
    onDragStart={e=>{e.dataTransfer.setData("text/smartdoctor-widget",id);e.dataTransfer.effectAllowed="move";}}
    onDragOver={e=>{if(editMode)e.preventDefault();}}
    onDrop={e=>{if(!editMode)return;e.preventDefault();const from=e.dataTransfer.getData("text/smartdoctor-widget");if(from&&from!==id)onMove(from,id);}}>
    {editMode&&<div className="portal-widget-tools"><span className="portal-drag-grip">⠿ <small>Move</small></span><span className="portal-size-tools"><button type="button" onClick={()=>onResize(id,"width",-1)}>−W</button><button type="button" onClick={()=>onResize(id,"width",1)}>+W</button><button type="button" onClick={()=>onResize(id,"height",-1)}>−H</button><button type="button" onClick={()=>onResize(id,"height",1)}>+H</button></span></div>}
    <div className="portal-editable-content">{children}</div>
  </div>;
}


type ChartKind = "activity" | "appointments" | "patients" | "care" | "records" | "status";
type ChartSlot = { id:string; kind:ChartKind; width?:number; height?:number };
const chartCatalog:{kind:ChartKind;title:string;description:string;icon:typeof BarChart3}[]=[
 {kind:"activity",title:"Activity trend",description:"Weekly clinic activity over time",icon:TrendingUp},
 {kind:"appointments",title:"Appointment volume",description:"Appointments by day of the week",icon:BarChart3},
 {kind:"patients",title:"Patient growth",description:"New patient registrations over time",icon:TrendingUp},
 {kind:"care",title:"Care plan completion",description:"Completed, active and attention-needed plans",icon:PieChart},
 {kind:"records",title:"Medical records",description:"Records grouped by document type",icon:BarChart3},
 {kind:"status",title:"Appointment status",description:"Confirmed, pending and checked-in visits",icon:PieChart}
];
const chartSamples:Record<ChartKind,{labels:string[];values:number[];secondary?:number[]}>={
 activity:{labels:["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],values:[28,42,36,58,49,67,74],secondary:[18,26,31,35,42,47,53]},
 appointments:{labels:["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],values:[18,24,21,30,27,16,12]},
 patients:{labels:["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],values:[5,8,7,12,10,14,18]},
 care:{labels:["Complete","In progress","Attention"],values:[68,22,10]},
 records:{labels:["Lab","Clinical","Medication","Imaging"],values:[42,28,18,12]},
 status:{labels:["Confirmed","Pending","Checked in","Cancelled"],values:[58,14,22,6]}
};
function ChartVisual({kind}:{kind:ChartKind}){
 const sample=chartSamples[kind],max=Math.max(1,...sample.values);
 if(kind==="care"||kind==="status"||kind==="records")return <div className="sd-chart-bars">{sample.labels.map((label,i)=><div className="sd-chart-bar-row" key={label}><span>{label}</span><div><i style={{width:(sample.values[i]/max*100)+"%"}}/></div><b>{sample.values[i]}{kind==="care"||kind==="status"?"%":""}</b></div>)}</div>;
 const points=sample.values.map((v,i)=>({x:30+i*75,y:142-v/max*105,v,label:sample.labels[i]}));
 const path=points.map((p,i)=>(i?"L":"M")+p.x+" "+p.y).join(" ");
 return <svg className="sd-chart-svg" viewBox="0 0 520 190" role="img" aria-label={chartCatalog.find(c=>c.kind===kind)?.title}>
  {[35,85,135].map(y=><line key={y} x1="25" y1={y} x2="500" y2={y} className="sd-chart-gridline"/>)}
  <path d={path+" L "+points[points.length-1].x+" 150 L "+points[0].x+" 150 Z"} className="sd-chart-area"/>
  <path d={path} className="sd-chart-line"/>
  {points.map(p=><g key={p.label}><circle cx={p.x} cy={p.y} r="4" className="sd-chart-point"/><text x={p.x} y="174" textAnchor="middle">{p.label}</text></g>)}
 </svg>;
}
function DashboardChartStudio({role}:{role:Role}){
 const [slots,setSlots]=useState<ChartSlot[]>([{id:"chart-activity",kind:"activity"},{id:"chart-care",kind:"care"}]);
 const [ready,setReady]=useState(false),[drawer,setDrawer]=useState(false),[target,setTarget]=useState<string|null>(null);
 useEffect(()=>{try{const saved=localStorage.getItem("smartdoctor-chart-layout-v1:"+role);if(saved!==null)setSlots(JSON.parse(saved));}catch{}setReady(true)},[role]);
 useEffect(()=>{if(ready)try{localStorage.setItem("smartdoctor-chart-layout-v1:"+role,JSON.stringify(slots))}catch{}},[slots,ready,role]);
 const choose=(kind:ChartKind)=>{setSlots(prev=>target?prev.map(x=>x.id===target?{...x,kind}:x):[...prev,{id:"chart-"+Date.now(),kind}]);setDrawer(false);setTarget(null)};
 const open=(id:string|null)=>{setTarget(id);setDrawer(true)};
 const resize=(id:string,axis:"width"|"height",delta:number)=>setSlots(prev=>prev.map(x=>x.id===id?{...x,[axis]:Math.max(1,Math.min(axis==="width"?2:3,(x[axis]||1)+delta))}:x));
 const remove=(id:string)=>{setSlots(prev=>prev.filter(x=>x.id!==id));open(null)};
 const move=(from:string,to:string)=>setSlots(prev=>{const a=prev.findIndex(x=>x.id===from),b=prev.findIndex(x=>x.id===to);if(a<0||b<0||a===b)return prev;const next=[...prev];const [item]=next.splice(a,1);next.splice(b,0,item);return next});
 return <section className="sd-chart-studio">
  <div className="sd-chart-studio-head"><div><h3>Dashboard analytics</h3><p>Drag cards to rearrange. Replace or remove a chart at any time.</p></div><button className="sd-chart-add" onClick={()=>open(null)}><Plus size={14}/> Add chart</button></div>
  <div className="sd-chart-grid">{slots.map(slot=>{const def=chartCatalog.find(x=>x.kind===slot.kind)!;const Icon=def.icon;return <article key={slot.id} className="sd-chart-card" style={{gridColumn:"span "+(slot.width||1),minHeight:220+(slot.height||1)*35}} draggable onDragStart={e=>{e.dataTransfer.setData("text/sd-chart",slot.id);e.dataTransfer.effectAllowed="move"}} onDragOver={e=>e.preventDefault()} onDrop={e=>{e.preventDefault();move(e.dataTransfer.getData("text/sd-chart"),slot.id)}}>
   <header><span className="sd-chart-grip" title="Drag to reorder"><GripVertical size={17}/></span><span className="sd-chart-icon"><Icon size={15}/></span><div className="sd-chart-title"><b>{def.title}</b><small>{def.description}</small></div><button title="Narrow chart" aria-label="Narrow chart" onClick={()=>resize(slot.id,"width",-1)}>-W</button><button title="Widen chart" aria-label="Widen chart" onClick={()=>resize(slot.id,"width",1)}>+W</button><button title="Shorter chart" aria-label="Shorter chart" onClick={()=>resize(slot.id,"height",-1)}>-H</button><button title="Taller chart" aria-label="Taller chart" onClick={()=>resize(slot.id,"height",1)}>+H</button><button title="Replace chart" aria-label="Replace chart" onClick={()=>open(slot.id)}><RefreshCw size={14}/></button><button title="Remove chart" aria-label="Remove chart" onClick={()=>remove(slot.id)}><X size={16}/></button></header>
   <ChartVisual kind={slot.kind}/><footer><span>Demo analytics</span><span>{role} workspace</span></footer>
  </article>})}{slots.length===0&&<div className="sd-chart-empty"><BarChart3 size={25}/><b>No charts on your dashboard</b><span>Add a chart from the library to get started.</span><button className="sd-chart-add" onClick={()=>open(null)}><Plus size={14}/> Add chart</button></div>}</div>
  <div className={"sd-chart-backdrop "+(drawer?"open":"")} onClick={()=>setDrawer(false)}/>
  <aside className={"sd-chart-drawer "+(drawer?"open":"")} aria-hidden={!drawer}><header><div><h3>Chart library</h3><p>Choose a visualization for this dashboard.</p></div><button onClick={()=>setDrawer(false)} aria-label="Close chart library"><X size={18}/></button></header><div className="sd-chart-library">{chartCatalog.map(item=>{const Icon=item.icon;return <button key={item.kind} onClick={()=>choose(item.kind)}><span><Icon size={19}/></span><div><b>{item.title}</b><small>{item.description}</small></div><Plus size={15}/></button>})}</div></aside>
 </section>;
}

export default function RoleDashboardPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [role,setRole]=useState<Role>("admin");
  const [sidebarCollapsed,setSidebarCollapsed]=useState(false);
  useEffect(()=>{try{setSidebarCollapsed(window.localStorage.getItem("smartdoctor-sidebar-collapsed")==="true")}catch{}},[]);
  const toggleSidebar=()=>setSidebarCollapsed(v=>{const next=!v;try{window.localStorage.setItem("smartdoctor-sidebar-collapsed",String(next))}catch{}return next});
  const [section,setSection]=useState<Section>("overview");
  const navigateSection=(next:Section)=>{setSection(next);router.push(next==="overview"?"/portal":"/portal/"+next);};
  useEffect(()=>{const sync=()=>{const value=new URLSearchParams(window.location.search).get("section");const allowed:Section[]=["overview","patients","appointments","records","team","audit"];setSection(allowed.includes(value as Section)?value as Section:"overview");};sync();window.addEventListener("popstate",sync);return()=>window.removeEventListener("popstate",sync);},[]);
  const [query,setQuery]=useState("");
  const [editMode,setEditMode]=useState(false);
  const [layoutReady,setLayoutReady]=useState(false);
  const [widgetLayouts,setWidgetLayouts]=useState<Record<string,WidgetLayout>>({});
  useEffect(()=>{try{const saved=window.localStorage.getItem("smartdoctor-dashboard-layout-v1");if(saved)setWidgetLayouts(JSON.parse(saved));}catch{}setLayoutReady(true);},[]);
  useEffect(()=>{if(layoutReady)try{window.localStorage.setItem("smartdoctor-dashboard-layout-v1",JSON.stringify(widgetLayouts));}catch{}},[widgetLayouts,layoutReady]);
  const defaultOrder=(id:string)=>{if(id.startsWith("metric-")||id.startsWith("quick-"))return Number(id.split("-")[1])||0;if(id==="workflow-chart")return 1;if(id.startsWith("menu-"))return Math.max(0,visibleNav.findIndex(item=>"menu-"+item.id===id));return 0;};
  const getLayout=(id:string):WidgetLayout=>widgetLayouts[role+":"+id]||{width:id.startsWith("menu-")?4:1,height:1,order:defaultOrder(id)};
  const resizeWidget=(id:string,axis:"width"|"height",delta:number)=>setWidgetLayouts(prev=>{const key=role+":"+id,current=prev[key]||{width:1,height:1,order:0};return {...prev,[key]:{...current,[axis]:Math.max(1,Math.min(axis==="width"?4:3,current[axis]+delta))}};});
  const moveWidget=(from:string,to:string)=>setWidgetLayouts(prev=>{const a=role+":"+from,b=role+":"+to,la=prev[a]||{width:from.startsWith("menu-")?4:1,height:1,order:defaultOrder(from)},lb=prev[b]||{width:to.startsWith("menu-")?4:1,height:1,order:defaultOrder(to)};return {...prev,[a]:{...la,order:lb.order},[b]:{...lb,order:la.order}};});
  const resetLayout=()=>setWidgetLayouts(prev=>Object.fromEntries(Object.entries(prev).filter(([key])=>!key.startsWith(role+":"))));
  const widget=(id:string,children:React.ReactNode,className="")=><EditableWidget key={id} id={id} editMode={editMode} layout={getLayout(id)} onResize={resizeWidget} onMove={moveWidget} className={className}>{children}</EditableWidget>;

  const activeRole=roles.find(r=>r.id===role)!;
  const visibleNav=navByRole[role];
  const setActiveRole=(next:Role)=>{setRole(next);navigateSection("overview");setQuery("");};
  const filteredPatients=useMemo(()=>patients.filter(p=>[p.name,p.id,p.doctor].join(" ").toLowerCase().includes(query.toLowerCase())),[query]);
  const filteredAppointments=useMemo(()=>appointments.filter(a=>[a.patient,a.doctor,a.type,a.id].join(" ").toLowerCase().includes(query.toLowerCase())),[query]);
  const heading=section==="overview"?(role==="receptionist"?"Front desk overview":"Overview"):visibleNav.find(n=>n.id===section)?.label||"Overview";
  const kpis=metrics[role];

  const showTable=()=>{
    if(section==="patients") return <div className="portal-card"><div className="portal-card-title"><div><h3>{role==="doctor"?"Assigned patients":"Patient directory"}</h3><p>Synthetic patient profiles for interface testing.</p></div><label className="portal-search"><Search size={13}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search patients"/></label></div><div className="portal-table-wrap"><table className="portal-table"><thead><tr><th>Patient</th><th>Patient ID</th><th>Age</th><th>Care team</th><th>Last visit</th><th>Status</th></tr></thead><tbody>{filteredPatients.map(p=><tr key={p.id}><td><div className="portal-person"><span className="portal-avatar">{p.initials}</span><b>{p.name}</b></div></td><td>{p.id}</td><td>{p.age}</td><td>{p.doctor}</td><td>{p.last}</td><td><Status value={p.status}/></td></tr>)}</tbody></table>{filteredPatients.length===0&&<div className="portal-empty">No matching demo patients.</div>}</div></div>;
    if(section==="appointments") return <div className="portal-card"><div className="portal-card-title"><div><h3>{role==="patient"?"My appointments":"Appointment schedule"}</h3><p>Example clinic bookings · all names and details are synthetic.</p></div><label className="portal-search"><Search size={13}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search appointments"/></label></div><div className="portal-table-wrap"><table className="portal-table"><thead><tr><th>Appointment</th><th>Patient</th><th>Clinician</th><th>Date & time</th><th>Type</th><th>Status</th></tr></thead><tbody>{filteredAppointments.map(a=><tr key={a.id}><td>{a.id}</td><td><div className="portal-person"><span className="portal-avatar">{a.initials}</span><b>{a.patient}</b></div></td><td>{a.doctor}</td><td>{a.date}</td><td>{a.type}</td><td><Status value={a.status}/></td></tr>)}</tbody></table>{filteredAppointments.length===0&&<div className="portal-empty">No matching appointments.</div>}</div></div>;
    if(section==="records") return <div className="portal-card"><div className="portal-card-title"><div><h3>{role==="patient"?"My medical records":"Recent clinical records"}</h3><p>Sample records with review states; no real clinical data.</p></div><span className="portal-period">All records</span></div><div className="portal-table-wrap"><table className="portal-table"><thead><tr><th>Record</th><th>Patient</th><th>Type</th><th>Added</th><th>Status</th></tr></thead><tbody>{records.map((r,i)=><tr key={i}><td><div className="portal-person"><span className="portal-avatar"><FileText size={13}/></span><b>{r.title}</b></div></td><td>{r.patient}</td><td>{r.kind}</td><td>{r.date}</td><td><Status value={r.status}/></td></tr>)}</tbody></table></div></div>;
    if(section==="team") return <div className="portal-card"><div className="portal-card-title"><div><h3>Clinic team & role assignments</h3><p>Role assignment preview; real changes require protected admin APIs.</p></div><span className="portal-period">5 sample users</span></div><div className="portal-table-wrap"><table className="portal-table"><thead><tr><th>Team member</th><th>Specialty / role</th><th>Email</th><th>Status</th></tr></thead><tbody>{staff.map(s=><tr key={s.email}><td><div className="portal-person"><span className="portal-avatar">{s.initials}</span><b>{s.name}</b></div></td><td>{s.role}</td><td>{s.email}</td><td><Status value={s.status}/></td></tr>)}</tbody></table></div></div>;
    if(section==="audit") return <div className="portal-card"><div className="portal-card-title"><div><h3>Security & audit activity</h3><p>Illustrative access events, including a denied role-management attempt.</p></div><span className="portal-period">Recent events</span></div><div className="portal-table-wrap"><table className="portal-table"><thead><tr><th>Action</th><th>Actor</th><th>Resource</th><th>Time</th><th>Outcome</th></tr></thead><tbody>{audit.map((a,i)=><tr key={i}><td>{a.action}</td><td>{a.actor}</td><td>{a.scope}</td><td>{a.time}</td><td><Status value={a.status}/></td></tr>)}</tbody></table></div></div>;
    return null;
  };

  return <main className="portal-shell">
    <header className="portal-top">
      <Link href="/" className="portal-brand"><span className="portal-brand-mark"><HeartPulse size={19}/></span>smartdoctor</Link>
      <div className="portal-top-right"><span className="portal-env"><i/> Synthetic demo environment</span>{user?.role==="patient"&&<Link href="/portal/clinic-assistant" className="portal-link">Clinic assistant</Link>}{user?.role==="admin"&&<Link href="/portal/organization" className="portal-link">My Clinic</Link>}<Link href="/portal/manage" className="portal-link">Manage workspace</Link>{user?.role==="super_admin"&&<Link href="/portal/super-admin" className="portal-link">Super Admin</Link>}<Bell size={16}/><Link href="/profile" aria-label="Profile"><UserRound size={17}/></Link></div>
    </header>
    <div className="portal-body">
      <div className="portal-intro"><div><div className="portal-role-label">ROLE-BASED WORKSPACE PREVIEW</div><h1>{activeRole.greeting}</h1><p>{activeRole.subtitle}</p></div>
        <div className="portal-intro-actions"><div className="portal-role-switch" aria-label="Preview dashboard role">{roles.map(r=><button key={r.id} className={role===r.id?"active":""} onClick={()=>setActiveRole(r.id)}><r.icon size={14}/>{r.label}</button>)}</div><div className="portal-editor-actions"><button className={editMode?"active":""} onClick={()=>setEditMode(v=>!v)}><Settings size={13}/>{editMode?"Finish editing":"Customize layout"}</button>{editMode&&<button onClick={resetLayout}>Reset layout</button>}</div></div>
      </div>
      {editMode&&<div className="portal-edit-hint"><b>⠿ Drag widgets to rearrange.</b> Use −W / +W and −H / +H to resize. Layout is saved separately for each role in this browser.</div>}<div className="portal-demo-warning"><AlertCircle size={16}/><div><b>Demo data only — not connected to real patient records.</b>Role switching here previews each dashboard layout. It does not grant permissions or change your account role. Production access must be enforced by FastAPI using verified roles, organization membership, patient relationships and consent.</div></div>

      <div className={"portal-layout "+(sidebarCollapsed?"sidebar-collapsed":"")}>
        <aside className="portal-nav" aria-label="Workspace navigation">
          <div className="portal-nav-heading"><div className="portal-nav-title">{activeRole.label.toUpperCase()} MENU</div><button type="button" className="portal-nav-toggle" onClick={toggleSidebar} aria-label={sidebarCollapsed?"Expand sidebar":"Collapse sidebar"} title={sidebarCollapsed?"Expand sidebar":"Collapse sidebar"}>{sidebarCollapsed?<PanelLeftOpen size={17}/>:<PanelLeftClose size={17}/>}</button></div>
          {visibleNav.map(item=>widget("menu-"+item.id,<Link href={item.id==="overview"?"/portal":"/portal/"+item.id} key={item.id} title={item.label} className="portal-nav-link"><item.icon size={16}/><span className="portal-nav-label">{item.label}</span><ArrowUpRight className="portal-nav-arrow" size={12}/></Link>,"portal-menu-editable"))}
          <div className="portal-nav-divider">INSIGHTS & TOOLS</div>
          {[{label:"Reports",href:"/portal/reports",icon:ChartNoAxesCombined},{label:"Observability",href:"/portal/observability",icon:Activity},{label:"Knowledge base",href:"/portal/knowledge",icon:ClipboardList},{label:"AI assistant",href:"/portal/assistant",icon:Stethoscope},{label:"Workspace settings",href:"/portal/settings",icon:Settings}].map(item=><Link key={item.href} href={item.href} title={item.label} className="portal-nav-route"><item.icon size={16}/><span className="portal-nav-label">{item.label}</span><ArrowUpRight className="portal-nav-arrow" size={12}/></Link>)}
          <div className="portal-nav-foot"><ShieldCheck size={14}/> <span className="portal-nav-label">Access should be limited by role, organization and patient consent.</span></div>
        </aside>
        <section className="portal-main">
                {widget("hero-banner",<section className="portal-hero">
        <div className="portal-hero-copy">
          <span className="portal-hero-kicker"><span/> SMARTER CARE, CONNECTED</span>
          <h2>{role==="patient"?"Your health journey, all in one place":role==="doctor"?"Make every patient interaction count":role==="admin"?"A clearer view of your clinic": "A smoother day starts at the front desk"}</h2>
          <p>{role==="patient"?"Stay on top of appointments, records and the people supporting your care.":role==="doctor"?"Your patients, schedule and clinical work — organized in one workspace.":role==="admin"?"Monitor clinic activity, support your teams and keep operations moving.":"Coordinate appointments, welcome patients and keep the clinic running smoothly."}</p>
          <div className="portal-hero-actions"><button onClick={()=>navigateSection(role==="patient"?"appointments":role==="doctor"||role==="receptionist"?"patients":"team")}>{role==="patient"?"View appointments":role==="doctor"?"Open patient panel":role==="admin"?"Manage clinic team":"Open patient directory"} <ArrowUpRight size={14}/></button><span><ShieldCheck size={14}/> Privacy-first workspace</span></div>
        </div>
        <div className="portal-hero-art" aria-label="Healthcare team illustration">
          <div className="portal-hero-orbit orbit-a"/><div className="portal-hero-orbit orbit-b"/>
          <div className="portal-doctor-photo portal-brain-art"><Image src="/images/brain-dna.jpg" alt="Glowing blue 3D medical brain with DNA illustration" width={720} height={420} priority/><span className="portal-photo-glow"/></div>
          <div className="portal-hero-float float-top"><span><CalendarCheck size={16}/></span><div><b>Care, coordinated</b><small>One connected workspace</small></div></div>
          <div className="portal-hero-float float-bottom"><span><CheckCircle2 size={16}/></span><div><b>Secure by design</b><small>Role-based access</small></div></div>
          <div className="portal-glass-chip"><HeartPulse size={15}/><span>Connected care</span><i/></div>
        </div>
      </section>)}
          <div className="portal-section-head"><div><h2>{heading}</h2><p>Clinic workspace · Friday, November 21, 2026</p></div><span className="portal-period"><Clock3 size={11} style={{display:"inline",marginRight:5}}/>Last 30 days</span></div>
          {section==="overview"&&<>
            <div className="portal-kpis">{kpis.map((k,i)=>widget("metric-"+i,<article className="portal-kpi"><div className="portal-kpi-top">{k.label}<span className="portal-kpi-icon"><MetricIcon name={k.icon}/></span></div><strong>{k.value}</strong><small className={i===0&&role==="admin"?"up":""}>{k.note}</small></article>))}</div>
            <DashboardChartStudio role={role}/>
            <div className="portal-quick-grid">
              {(role==="patient"?[[CalendarCheck,"Book an appointment","Request a clinic visit","appointments"],[FileText,"View medical records","Browse your documents","records"],[Pill,"Medication list","Review current medications","records"]]:role==="doctor"?[[Users,"Open patient panel","Review assigned patients","patients"],[CalendarDays,"View schedule","Manage today's appointments","appointments"],[ClipboardList,"Review clinical records","Check pending documentation","records"]]:role==="admin"?[[UserPlus,"Manage users","Review staff and roles","team"],[ChartNoAxesCombined,"Clinic analytics","View operational trends","overview"],[ShieldCheck,"Audit activity","Inspect access events","audit"]]:[[UserPlus,"Register patient","Create a patient intake","patients"],[CalendarDays,"Book appointment","Schedule a clinic visit","appointments"],[ClipboardCheck,"Check-in queue","Review arrivals and waiting list","appointments"]]).map(([Icon,title,desc,target],i)=>widget("quick-"+i,<button className="portal-quick" onClick={()=>navigateSection(target as Section)}><span className="portal-quick-icon"><Icon size={16}/></span><span><b>{String(title)}</b><small>{String(desc)}</small></span><ArrowUpRight size={13} style={{marginLeft:"auto",color:"#9aabb1"}}/></button>))}
            </div>
            <div className="portal-section-head"><div><h2>{role==="patient"?"Upcoming appointments":"Recent appointments"}</h2><p>Sample bookings from the synthetic clinic dataset.</p></div><button className="portal-link" onClick={()=>navigateSection("appointments")}>View all →</button></div>
            {widget("recent-appointments",<div className="portal-card"><div className="portal-table-wrap"><table className="portal-table"><thead><tr><th>Patient</th><th>Clinician</th><th>Date & time</th><th>Visit type</th><th>Status</th></tr></thead><tbody>{appointments.slice(0,4).map(a=><tr key={a.id}><td><div className="portal-person"><span className="portal-avatar">{a.initials}</span><b>{a.patient}</b></div></td><td>{a.doctor}</td><td>{a.date}</td><td>{a.type}</td><td><Status value={a.status}/></td></tr>)}</tbody></table></div></div>)}
          </>}
          {section!=="overview"&&widget("section-table",showTable())}
          <footer className="portal-footer"><span>SmartDoctor · Role-based dashboard preview</span><span>Fictional sample data · No real patient information</span></footer>
        </section>
      </div>
    </div>
  </main>;
}
