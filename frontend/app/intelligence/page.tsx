"use client";
import {useEffect,useState} from "react";
import {Activity,BrainCircuit,ChartNoAxesCombined,ShieldCheck} from "lucide-react";
import ProtectedDashboard from "@/components/ProtectedDashboard";
import AppShell,{type NavItem} from "@/components/AppShell";
import {getModelRegistry,getModelDrift,type ModelRegistryItem} from "@/lib/api";
import {getToken} from "@/lib/auth";
const nav:NavItem[]=[{href:"/dashboard/admin",label:"Operations",icon:Activity},{href:"/intelligence",label:"Model intelligence",icon:BrainCircuit},{href:"/platform",label:"Platform",icon:ShieldCheck}];
export default function Intelligence(){const [models,setModels]=useState<ModelRegistryItem[]>([]);const [drift,setDrift]=useState<any[]>([]);useEffect(()=>{const t=getToken();if(t){getModelRegistry(t).then(setModels);getModelDrift(t).then(setDrift)}},[]);return <ProtectedDashboard requiredRole="admin">{(u,l)=><AppShell user={u} logout={l} nav={nav} active="/intelligence" title="Clinical intelligence" subtitle="Registry, calibration, deployment state and drift monitoring."><div className="grid"><section className="card span2"><div className="cardTop"><h2>Model registry</h2><BrainCircuit size={18}/></div><div className="modelTable">{models.map(m=><article key={m.name}><div><b>{m.name}</b><span>{m.task} · v{m.version}</span></div><strong>{Math.round(m.accuracy*100)}%</strong><small>F1 {m.macro_f1.toFixed(2)} · ECE {m.calibration_error.toFixed(3)}</small><em>{m.status}</em></article>)}</div></section><section className="card"><div className="cardTop"><h2>Drift watch</h2><ChartNoAxesCombined size={18}/></div>{drift.map(d=><div className="metric" key={d.model}><span>{d.model}</span><strong>{d.status}</strong></div>)}</section></div></AppShell>}</ProtectedDashboard>}
