"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Activity, BrainCircuit, CalendarDays, FileHeart, HeartPulse, LayoutDashboard, MessagesSquare, Stethoscope, Video, Watch, Pill, FlaskConical, ShieldAlert, FileText, Route, Building2, Bell, Settings2 } from "lucide-react";
import ProtectedDashboard from "@/components/ProtectedDashboard";
import AppShell, { type NavItem } from "@/components/AppShell";
import CareCarousel from "@/components/CareCarousel";
import LiveVitals from "@/components/LiveVitals";
import AICopilotPanel from "@/components/AICopilotPanel";
import EmergencyPanel from "@/components/EmergencyPanel";
import { getMyAppointments, getPatientSnapshot, type Appointment, type PatientSnapshot } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { fmtDateTime, greeting } from "@/lib/format";

const nav: NavItem[] = [
  { href: "/dashboard/patient", label: "Dashboard", icon: LayoutDashboard },
  { href: "/copilot", label: "MediLink Copilot", icon: BrainCircuit, badge: "AI" },
  { href: "/dashboard/patient#appointments", label: "Appointments", icon: CalendarDays },
  { href: "/video", label: "Video consultations", icon: Video },
  { href: "/records", label: "My health records", icon: FileHeart },
  { href: "/medications", label: "Medications", icon: Pill },
  { href: "/labs", label: "Lab results", icon: FlaskConical },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/referrals", label: "Referrals", icon: Route },
  { href: "/hospitals", label: "Hospitals & clinics", icon: Building2 },
  { href: "/watch", label: "MediLink Watch", icon: Watch, badge: "Live" },
  { href: "/messages", label: "Messages", icon: MessagesSquare },
  { href: "/notifications", label: "Notifications", icon: Bell },
  { href: "/settings", label: "Settings", icon: Settings2 },
  { href: "/emergency", label: "Emergency SOS", icon: ShieldAlert },
];

export default function PatientDashboard(){
 const [appointments,setAppointments]=useState<Appointment[]>([]); const [snapshot,setSnapshot]=useState<PatientSnapshot|null>(null);
 useEffect(()=>{const t=getToken(); if(!t)return; Promise.all([getMyAppointments(t),getPatientSnapshot(t)]).then(([a,s])=>{setAppointments(a);setSnapshot(s)}).catch(()=>{});},[]);
 const next=appointments.filter(a=>a.status==="scheduled").sort((a,b)=>+new Date(a.scheduled_at)-+new Date(b.scheduled_at))[0];
 return <ProtectedDashboard requiredRole="patient">{(user,logout)=><AppShell user={user} logout={logout} nav={nav} active="/dashboard/patient" title={<>{greeting()}, {user.full_name.split(" ")[0]}.</>} subtitle="Your connected-care command centre." actions={<><Link href="/copilot" className="btn outline"><BrainCircuit size={16}/> Ask MediLink Copilot</Link><Link href="/doctors" className="btn primary"><Stethoscope size={16}/> Find care</Link></>}>
   <CareCarousel/>
   <div className="featureStrip">
     <Link href="/copilot"><BrainCircuit/><div><b>MediLink Copilot</b><span>Record-grounded care assistant</span></div></Link>
     <Link href="/video"><Video/><div><b>Video care</b><span>Private consultation rooms</span></div></Link>
     <Link href="/watch"><Watch/><div><b>IoT monitoring</b><span>Live connected vitals</span></div></Link>
     <Link href="/records"><FileHeart/><div><b>Health records</b><span>Labs, medication, timeline</span></div></Link>
   </div>
   <div className="grid v8Grid">
     <section className="card span2"><LiveVitals/></section>
     <AICopilotPanel/>
     <section className="card">
       <div className="cardTop"><h2>Next appointment</h2><CalendarDays size={18}/></div>
       {next?<><h3>{next.doctor_name}</h3><p className="muted">{fmtDateTime(next.scheduled_at)}</p><p>{next.reason}</p><div className="stackButtons"><Link className="btn primary" href="/video"><Video size={16}/> Join care room</Link><Link className="btn outline" href="/doctors">Reschedule / book</Link></div></>:<><p className="muted">Nothing upcoming.</p><Link href="/doctors" className="btn primary">Book appointment</Link></>}
     </section>
     <section className="card span2">
       <div className="cardTop"><h2>Health insights</h2><HeartPulse size={18}/></div>
       <div className="insightGrid"><div><strong>{snapshot?.health_score ?? 88}%</strong><span> health score</span></div><div><strong>{snapshot?.activity_steps?.toLocaleString() ?? "8,425"}</strong><span>Steps today</span></div><div><strong>{snapshot?.sleep ?? "7h 24m"}</strong><span>Sleep</span></div><div><strong>{snapshot?.stress ?? "Low"}</strong><span>Stress level</span></div></div>
     </section>
     <section className="card">
       <div className="cardTop"><h2>Medications</h2><Pill size={18}/></div>
       <div className="miniList">{(snapshot?.medications ?? []).map(m=><div key={m.name}><span><b>{m.name}</b><small>{m.dose} · {m.schedule}</small></span><em>{m.next_due}</em></div>)}{!snapshot&&<p className="muted">Loading…</p>}</div>
     </section>
     <section className="card span2">
       <div className="cardTop"><h2>Recent lab results</h2><FlaskConical size={18}/></div>
       <div className="miniList labs">{(snapshot?.labs ?? []).map(l=><div key={l.name}><span><b>{l.name}</b><small>{l.date} · {l.value}</small></span><em className={l.status}>{l.status}</em></div>)}</div>
     </section>
     <section className="span1"><EmergencyPanel/></section>
     <section className="card span3" id="appointments"><div className="cardTop"><h2>Your care timeline</h2><Activity size={18}/></div><div className="timelineV8"><div><i/><b>Today</b><span>MediLink Watch synced new connected vitals.</span></div><div><i/><b>2 Oct</b><span>Complete Blood Count added to your health record.</span></div><div><i/><b>28 Sep</b><span>Cholesterol panel marked for routine review.</span></div><div><i/><b>21 Sep</b><span>Medication list updated.</span></div></div></section>
   </div>
 </AppShell>}</ProtectedDashboard>
}
