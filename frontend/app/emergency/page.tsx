"use client";
import { Ambulance, HeartPulse, LayoutDashboard, MapPin, PhoneCall, ShieldAlert } from "lucide-react";
import ProtectedDashboard from "@/components/ProtectedDashboard";
import AppShell,{type NavItem} from "@/components/AppShell";
import EmergencyPanel from "@/components/EmergencyPanel";
const nav:NavItem[]=[{href:"/dashboard/patient",label:"Dashboard",icon:LayoutDashboard},{href:"/emergency",label:"Emergency SOS",icon:ShieldAlert}];
export default function Emergency(){return <ProtectedDashboard>{(user,logout)=><AppShell user={user} logout={logout} nav={nav} active="/emergency" title="Emergency support" subtitle="Fast access to emergency actions without asking AI to make the decision."><div className="grid"><section className="span2"><EmergencyPanel/></section><section className="card"><h2>Emergency card</h2><div className="emergencyInfo"><span><HeartPulse/> Blood type <b>: O+</b></span><span><Ambulance/> Emergency contact <b> contact</b></span><span><MapPin/> Location sharing <b>Off</b></span></div><p className="muted">These are sample fields. Production emergency profiles should be explicitly consented and verified.</p></section></div></AppShell>}</ProtectedDashboard>}
