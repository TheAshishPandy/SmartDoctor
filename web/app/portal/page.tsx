"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  Activity, CalendarDays, ClipboardList, FileText, HeartPulse, LayoutDashboard,
  Search, ShieldCheck, Stethoscope, Users, UserRound, Clock3, FlaskConical,
  Pill, Settings, Bell, ChevronDown, ArrowUpRight, CheckCircle2, AlertCircle,
  Building2, ClipboardCheck, UserPlus, CalendarCheck, ChartNoAxesCombined,
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
  { name:"Maya Chen", initials:"MC", role:"Cardiology", email:"maya.chen@demo.smartdoctor.test", status:"Active" },
  { name:"Ethan Patel", initials:"EP", role:"Internal medicine", email:"ethan.patel@demo.smartdoctor.test", status:"Active" },
  { name:"Sarah Kim", initials:"SK", role:"Family medicine", email:"sarah.kim@demo.smartdoctor.test", status:"Active" },
  { name:"Taylor Reed", initials:"TR", role:"Receptionist", email:"taylor.reed@demo.smartdoctor.test", status:"Active" },
  { name:"Morgan Lee", initials:"ML", role:"Receptionist", email:"morgan.lee@demo.smartdoctor.test", status:"Invited" },
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
  admin: [{id:"overview",label:"Overview",icon:LayoutDashboard},{id:"patients",label:"Patients",icon:Users},{id:"appointments",label:"Appointments",icon:CalendarDays},{id:"team",label:"Team & roles",icon:Building2},{id:"audit",label:"Audit activity",icon:ShieldCheck}],
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

export default function RoleDashboardPage() {
  const [role,setRole]=useState<Role>("admin");
  const [section,setSection]=useState<Section>("overview");
  const [query,setQuery]=useState("");
  const [editMode,setEditMode]=useState(false);
  const [layoutReady,setLayoutReady]=useState(false);
  const [widgetLayouts,setWidgetLayouts]=useState<Record<string,WidgetLayout>>({});
  useEffect(()=>{try{const saved=window.localStorage.getItem("smartdoctor-dashboard-layout-v1");if(saved)setWidgetLayouts(JSON.parse(saved));}catch{}setLayoutReady(true);},[]);
  useEffect(()=>{if(layoutReady)try{window.localStorage.setItem("smartdoctor-dashboard-layout-v1",JSON.stringify(widgetLayouts));}catch{}},[widgetLayouts,layoutReady]);
  const getLayout=(id:string):WidgetLayout=>widgetLayouts[role+":"+id]||{width:1,height:1,order:0};
  const resizeWidget=(id:string,axis:"width"|"height",delta:number)=>setWidgetLayouts(prev=>{const key=role+":"+id,current=prev[key]||{width:1,height:1,order:0};return {...prev,[key]:{...current,[axis]:Math.max(1,Math.min(axis==="width"?4:3,current[axis]+delta))}};});
  const moveWidget=(from:string,to:string)=>setWidgetLayouts(prev=>{const a=role+":"+from,b=role+":"+to,la=prev[a]||{width:1,height:1,order:0},lb=prev[b]||{width:1,height:1,order:0};return {...prev,[a]:{...la,order:lb.order},[b]:{...lb,order:la.order}};});
  const resetLayout=()=>setWidgetLayouts(prev=>Object.fromEntries(Object.entries(prev).filter(([key])=>!key.startsWith(role+":"))));
  const widget=(id:string,children:React.ReactNode,className="")=><EditableWidget id={id} editMode={editMode} layout={getLayout(id)} onResize={resizeWidget} onMove={moveWidget} className={className}>{children}</EditableWidget>;

  const activeRole=roles.find(r=>r.id===role)!;
  const visibleNav=navByRole[role];
  const setActiveRole=(next:Role)=>{setRole(next);setSection("overview");setQuery("");};
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
      <div className="portal-top-right"><span className="portal-env"><i/> Synthetic demo environment</span><Bell size={16}/><Link href="/profile" aria-label="Profile"><UserRound size={17}/></Link></div>
    </header>
    <div className="portal-body">
      <div className="portal-intro"><div><div className="portal-role-label">ROLE-BASED WORKSPACE PREVIEW</div><h1>{activeRole.greeting}</h1><p>{activeRole.subtitle}</p></div>
        <div className="portal-intro-actions"><div className="portal-role-switch" aria-label="Preview dashboard role">{roles.map(r=><button key={r.id} className={role===r.id?"active":""} onClick={()=>setActiveRole(r.id)}><r.icon size={14}/>{r.label}</button>)}</div><div className="portal-editor-actions"><button className={editMode?"active":""} onClick={()=>setEditMode(v=>!v)}><Settings size={13}/>{editMode?"Finish editing":"Customize layout"}</button>{editMode&&<button onClick={resetLayout}>Reset layout</button>}</div></div>
      </div>
      {editMode&&<div className="portal-edit-hint"><b>⠿ Drag widgets to rearrange.</b> Use −W / +W and −H / +H to resize. Layout is saved separately for each role in this browser.</div>}<div className="portal-demo-warning"><AlertCircle size={16}/><div><b>Demo data only — not connected to real patient records.</b>Role switching here previews each dashboard layout. It does not grant permissions or change your account role. Production access must be enforced by FastAPI using verified roles, organization membership, patient relationships and consent.</div></div>
      <section className="portal-hero">
        <div className="portal-hero-copy">
          <span className="portal-hero-kicker"><span/> SMARTER CARE, CONNECTED</span>
          <h2>{role==="patient"?"Your health journey, all in one place":role==="doctor"?"Make every patient interaction count":role==="admin"?"A clearer view of your clinic": "A smoother day starts at the front desk"}</h2>
          <p>{role==="patient"?"Stay on top of appointments, records and the people supporting your care.":role==="doctor"?"Your patients, schedule and clinical work — organized in one workspace.":role==="admin"?"Monitor clinic activity, support your teams and keep operations moving.":"Coordinate appointments, welcome patients and keep the clinic running smoothly."}</p>
          <div className="portal-hero-actions"><button onClick={()=>setSection(role==="patient"?"appointments":role==="doctor"||role==="receptionist"?"patients":"team")}>{role==="patient"?"View appointments":role==="doctor"?"Open patient panel":role==="admin"?"Manage clinic team":"Open patient directory"} <ArrowUpRight size={14}/></button><span><ShieldCheck size={14}/> Privacy-first workspace</span></div>
        </div>
        <div className="portal-hero-art" aria-hidden="true">
          <div className="portal-hero-orbit orbit-a"/><div className="portal-hero-orbit orbit-b"/>
          <div className="portal-hero-cross"><HeartPulse size={54}/></div>
          <div className="portal-hero-float float-top"><span><CalendarCheck size={16}/></span><div><b>Care, coordinated</b><small>One connected workspace</small></div></div>
          <div className="portal-hero-float float-bottom"><span><CheckCircle2 size={16}/></span><div><b>Secure by design</b><small>Role-based access</small></div></div>
        </div>
      </section>
      <div className="portal-layout">
        <aside className="portal-nav"><div className="portal-nav-title">{activeRole.label.toUpperCase()} MENU</div>{visibleNav.map(item=>widget("menu-"+item.id,<button key={item.id} className={section===item.id?"active":""} onClick={()=>{setSection(item.id);setQuery("");}}><item.icon size={15}/>{item.label}</button>,"portal-menu-editable"))}<div className="portal-nav-foot"><ShieldCheck size={14}/> Access should be limited by role, organization and patient consent.</div></aside>
        <section className="portal-main">
          <div className="portal-section-head"><div><h2>{heading}</h2><p>Clinic workspace · Friday, November 21, 2026</p></div><span className="portal-period"><Clock3 size={11} style={{display:"inline",marginRight:5}}/>Last 30 days</span></div>
          {section==="overview"&&<>
            <div className="portal-kpis">{kpis.map((k,i)=>widget("metric-"+i,<article className="portal-kpi"><div className="portal-kpi-top">{k.label}<span className="portal-kpi-icon"><MetricIcon name={k.icon}/></span></div><strong>{k.value}</strong><small className={i===0&&role==="admin"?"up":""}>{k.note}</small></article>))}</div>
            <div className="portal-grid-two">
              {widget("activity-chart",<article className="portal-card"><div className="portal-card-title"><div><h3>{role==="patient"?"Your health activity":"Activity overview"}</h3><p>Illustrative activity over the last 7 days.</p></div><span className="portal-period">This week</span></div>
                <svg className="portal-chart" viewBox="0 0 520 190" role="img" aria-label="Sample weekly activity chart"><line className="gridline" x1="36" y1="25" x2="505" y2="25"/><line className="gridline" x1="36" y1="68" x2="505" y2="68"/><line className="gridline" x1="36" y1="111" x2="505" y2="111"/><line className="gridline" x1="36" y1="154" x2="505" y2="154"/>{[["Mon",65,37],["Tue",105,55],["Wed",82,46],["Thu",126,66],["Fri",151,88],["Sat",95,42],["Sun",72,31]].map(([day,a,b],i)=><g key={String(day)}><rect x={48+i*66} y={154-Number(a)} width="20" height={Number(a)} rx="4" fill="#0b8b80"/><rect x={71+i*66} y={154-Number(b)} width="14" height={Number(b)} rx="3" fill="#b7d9d5"/><text x={65+i*66} y="174" textAnchor="middle">{day}</text></g>)}</svg>
                <div className="portal-legend"><span><i/>Appointments / activity</span><span><i className="secondary"/>Completed / reviewed</span></div>
              </article>)}
              {widget("workflow-chart",<article className="portal-card"><div className="portal-card-title"><div><h3>{role==="patient"?"Care plan progress":"Operational breakdown"}</h3><p>Sample workflow completion.</p></div><ChartNoAxesCombined size={16} color="#0b8b80"/></div>
                {[["Completed",role==="patient"?78:68],["In progress",role==="patient"?16:22],["Needs attention",role==="patient"?6:10]].map(([label,val])=><div className="portal-progress-row" key={String(label)}><span className="portal-progress-label">{label}</span><div className="portal-progress-track"><i style={{width:`${val}%`,background:label==="Needs attention"?"#d9a24c":undefined}}/></div><span className="portal-progress-value">{val}%</span></div>)}
                <div style={{marginTop:22,padding:"12px",borderRadius:9,background:"#f4f8f8",fontSize:10,color:"#71848e",lineHeight:1.6}}><CheckCircle2 size={14} style={{display:"inline",verticalAlign:"middle",marginRight:6,color:"#168b72"}}/>Sample dashboard metrics only. Replace with authorized API aggregates when backend role modules are connected.</div>
              </article>)}
            </div>
            <div className="portal-quick-grid">
              {(role==="patient"?[[CalendarCheck,"Book an appointment","Request a clinic visit","appointments"],[FileText,"View medical records","Browse your documents","records"],[Pill,"Medication list","Review current medications","records"]]:role==="doctor"?[[Users,"Open patient panel","Review assigned patients","patients"],[CalendarDays,"View schedule","Manage today's appointments","appointments"],[ClipboardList,"Review clinical records","Check pending documentation","records"]]:role==="admin"?[[UserPlus,"Manage users","Review staff and roles","team"],[ChartNoAxesCombined,"Clinic analytics","View operational trends","overview"],[ShieldCheck,"Audit activity","Inspect access events","audit"]]:[[UserPlus,"Register patient","Create a patient intake","patients"],[CalendarDays,"Book appointment","Schedule a clinic visit","appointments"],[ClipboardCheck,"Check-in queue","Review arrivals and waiting list","appointments"]]).map(([Icon,title,desc,target],i)=>widget("quick-"+i,<button className="portal-quick" onClick={()=>setSection(target as Section)}><span className="portal-quick-icon"><Icon size={16}/></span><span><b>{String(title)}</b><small>{String(desc)}</small></span><ArrowUpRight size={13} style={{marginLeft:"auto",color:"#9aabb1"}}/></button>))}
            </div>
            <div className="portal-section-head"><div><h2>{role==="patient"?"Upcoming appointments":"Recent appointments"}</h2><p>Sample bookings from the synthetic clinic dataset.</p></div><button className="portal-link" onClick={()=>setSection("appointments")}>View all →</button></div>
            <div className="portal-card"><div className="portal-table-wrap"><table className="portal-table"><thead><tr><th>Patient</th><th>Clinician</th><th>Date & time</th><th>Visit type</th><th>Status</th></tr></thead><tbody>{appointments.slice(0,4).map(a=><tr key={a.id}><td><div className="portal-person"><span className="portal-avatar">{a.initials}</span><b>{a.patient}</b></div></td><td>{a.doctor}</td><td>{a.date}</td><td>{a.type}</td><td><Status value={a.status}/></td></tr>)}</tbody></table></div></div>
          </>}
          {section!=="overview"&&showTable()}
          <footer className="portal-footer"><span>SmartDoctor · Role-based dashboard preview</span><span>Fictional sample data · No real patient information</span></footer>
        </section>
      </div>
    </div>
  </main>;
}
