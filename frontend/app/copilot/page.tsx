"use client";

import Link from "next/link";
import {useEffect,useState} from "react";
import {BrainCircuit,CalendarDays,ChevronRight,History,LayoutDashboard,Send,ShieldCheck,Sparkles,Stethoscope} from "lucide-react";
import ProtectedDashboard from "@/components/ProtectedDashboard";
import AppShell,{type NavItem} from "@/components/AppShell";
import {chatWithCopilot,getCopilotConversation,getCopilotConversations,getCopilotStatus,type CopilotConversation,type CopilotSource,type CopilotStatus,type SuggestedDoctor} from "@/lib/api";
import {getToken} from "@/lib/auth";

const nav:NavItem[]=[
  {href:"/dashboard/patient",label:"Dashboard",icon:LayoutDashboard},
  {href:"/copilot",label:"MediLink Copilot",icon:BrainCircuit,badge:"AI"},
];

type Msg={
  role:"user"|"assistant";
  content:string;
  sources?:CopilotSource[];
  highlights?:string[];
  nextSteps?:string[];
  doctors?:SuggestedDoctor[];
  specialties?:string[];
  urgent?:boolean;
  engine?:string;
  model?:string|null;
};

const quickPrompts=[
  "Explain my latest blood results",
  "Which doctor should I see for headaches and dizziness?",
  "Prepare me for my next appointment",
  "What medicines am I currently taking?",
  "Do I have any referrals?",
];

export default function Copilot(){
  const [convos,setConvos]=useState<CopilotConversation[]>([]);
  const [cid,setCid]=useState<number|null>(null);
  const [msgs,setMsgs]=useState<Msg[]>([{role:"assistant",content:"Tell me what you want to understand. I can explain results, review your recorded medicines, prepare you for an appointment, check referrals and suggest the most relevant clinician pathway using your MediLink record."}]);
  const [draft,setDraft]=useState("");
  const [busy,setBusy]=useState(false);
  const [status,setStatus]=useState<CopilotStatus|null>(null);

  const load=async()=>{const t=getToken();if(t)setConvos(await getCopilotConversations(t))};
  useEffect(()=>{load().catch(()=>{});const t=getToken();if(t)getCopilotStatus(t).then(setStatus).catch(()=>{})},[]);

  const open=async(id:number)=>{
    const t=getToken();if(!t)return;
    const rows=await getCopilotConversation(t,id);
    setCid(id);
    setMsgs(rows.map(x=>({role:x.role as "user"|"assistant",content:x.content,sources:x.sources})));
  };

  const send=async(override?:string)=>{
    const text=(override??draft).trim();
    if(!text||busy)return;
    setDraft("");
    setMsgs(m=>[...m,{role:"user",content:text}]);
    setBusy(true);
    try{
      const t=getToken();if(!t)return;
      const r=await chatWithCopilot(t,text,cid);
      setCid(r.conversation_id);
      setMsgs(m=>[...m,{
        role:"assistant",
        content:r.answer,
        sources:r.sources,
        highlights:r.highlights,
        nextSteps:r.next_steps,
        doctors:r.suggested_doctors,
        specialties:r.suggested_specialties,
        urgent:r.urgent,
        engine:r.engine,
        model:r.model,
      }]);
      await load();
    }finally{setBusy(false)}
  };

  return <ProtectedDashboard requiredRole="patient">{(user,logout)=><AppShell user={user} logout={logout} nav={nav} active="/copilot" title="MediLink Copilot" subtitle="Understand your record, plan next steps and navigate to the right care.">
    <div className="copilotWorkspace">
      <aside className="conversationRail">
        <button className="btn primary" onClick={()=>{setCid(null);setMsgs([{role:"assistant",content:"What would you like to understand about your care today?"}])}}><Sparkles size={16}/> New conversation</button>
        <h3><History size={15}/> Recent</h3>
        {convos.map(c=><button key={c.id} className={cid===c.id?"active":""} onClick={()=>open(c.id)}>{c.title}</button>)}
      </aside>

      <section className="copilotChat">
        <div className="copilotIntelligenceBar">
          <div><Sparkles size={16}/><span>MediLink Intelligence</span></div>
          <strong>{status?.provider==="openai"?"LLM connected":status?.provider==="ollama"?"Local LLM connected":"Record-grounded reasoning"}</strong>
          {status?.model&&<small>{status.model}</small>}
        </div>
        <div className="copilotQuickPrompts">
          {quickPrompts.map(p=><button key={p} onClick={()=>send(p)} disabled={busy}>{p}</button>)}
        </div>

        <div className="copilotMessages">
          {msgs.map((m,i)=><article key={i} className={`copilotBubble ${m.role} ${m.urgent?"urgentBubble":""}`}>
            <div className="bubbleIcon">{m.role==="assistant"?<BrainCircuit size={17}/>:user.full_name[0]}</div>
            <div className="copilotBubbleBody">
              <p>{m.content}</p>
              {m.role==="assistant"&&m.engine&&<div className="copilotEngineTag"><Sparkles size={12}/>{m.engine==="openai"?"LLM enhanced":m.engine==="ollama"?"Local LLM":"Record grounded"}{m.model?` · ${m.model}`:""}</div>}

              {m.specialties&&m.specialties.length>0&&<div className="copilotSpecialties">
                <span>Suggested pathway</span>
                {m.specialties.map(s=><b key={s}>{s}</b>)}
              </div>}

              {m.highlights&&m.highlights.length>0&&<div className="copilotHighlights">
                {m.highlights.map((h,j)=><div key={`${j}-${h}`}>{h}</div>)}
              </div>}

              {m.doctors&&m.doctors.length>0&&<div className="copilotDoctorGrid">
                {m.doctors.map(d=><article key={d.doctor_id} className="copilotDoctorCard">
                  <div className="panelHeader"><div><span className="eyebrow">CLINICIAN MATCH</span><h3>{d.full_name}</h3></div><strong>{Math.round(d.match_score)}/100</strong></div>
                  <p><Stethoscope size={15}/> {d.specialty} · {d.clinic}</p>
                  <p className="muted">{d.reason}</p>
                  <div className="metric"><span>Consultation</span><strong>{d.consultation_type}</strong></div>
                  <div className="metric"><span>Open slots</span><strong>{d.open_slots}</strong></div>
                  <Link href="/doctors" className="btn primary">View & book <ChevronRight size={15}/></Link>
                </article>)}
              </div>}

              {m.nextSteps&&m.nextSteps.length>0&&<div className="copilotNextSteps">
                <h4><CalendarDays size={15}/> Suggested next steps</h4>
                {m.nextSteps.map((s,j)=><button key={`${j}-${s}`} onClick={()=>setDraft(s)}>{s}</button>)}
              </div>}

              {m.sources&&m.sources.length>0&&<details className="copilotSources">
                <summary>Record sources ({m.sources.length})</summary>
                <div className="sourceGrid">{m.sources.map((s,j)=><div key={`${s.kind}-${s.title}-${j}`}><b>{s.title}</b><span>{s.kind}</span><small>{s.excerpt}</small></div>)}</div>
              </details>}
            </div>
          </article>)}
          {busy&&<article className="copilotBubble assistant"><div className="bubbleIcon"><BrainCircuit size={17}/></div><div><p>Reviewing your MediLink record and care options…</p></div></article>}
        </div>

        <div className="copilotComposer">
          <textarea value={draft} onChange={e=>setDraft(e.target.value)} onKeyDown={e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();send()}}} placeholder="Ask about symptoms, results, medicines, referrals, appointments or which clinician to see…"/>
          <button className="btn primary" onClick={()=>send()} disabled={busy}><Send size={17}/>{busy?"Thinking…":"Send"}</button>
          <small><ShieldCheck size={13}/> Copilot uses information available in your MediLink record and routes urgent concerns away from routine AI guidance.</small>
        </div>
      </section>
    </div>
  </AppShell>}</ProtectedDashboard>;
}
