"use client";
import { useState } from "react";
import { BrainCircuit, Send, Sparkles } from "lucide-react";
import { askRecordCopilot, type RAGResponse } from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function AICopilotPanel({role="patient"}:{role?:"patient"|"doctor"}){
 const prompts=role==="doctor"?["Summarise my clinical worklist","What needs review today?","Prepare a patient handover"]:["Explain my latest lab results","Prepare me for my next appointment","Summarise my watch trends","What medicines are on my record?"];
 const [q,setQ]=useState(""); const [res,setRes]=useState<RAGResponse|null>(null); const [loading,setLoading]=useState(false); const [err,setErr]=useState("");
 async function ask(text=q){const token=getToken();if(!token||!text.trim())return;setLoading(true);setErr("");try{setRes(await askRecordCopilot(token,text));setQ("");}catch(e:any){setErr(e?.message||"Could not reach MediLink Copilot.");}finally{setLoading(false)}}
 return <section className="copilotPanel"><div className="cardTop"><div><span className="eyebrow"><Sparkles size={13}/> MEDILINK COPILOT</span><h2>Ask your care record</h2></div><span className="onlinePill"><i/>Grounded</span></div>
 {!res?<div className="botBubble"><BrainCircuit/><div><b>{role==="doctor"?"Clinical context, on demand":"Your record, made easier to understand"}</b><p>{role==="doctor"?"Retrieve relevant notes, monitoring and worklist context without leaving the clinical workspace.":"Ask about your appointments, results, medicines and connected-health trends. Answers are retrieved from information available to your account."}</p></div></div>:<div className="ragAnswer"><p>{res.answer}</p><div className="sourceRow">{res.sources.map((s,i)=><span key={i} title={s.excerpt}>{s.title}</span>)}</div><div className="ragActions">{res.suggested_actions.map(a=><small key={a}>→ {a}</small>)}</div><em>{res.safety_note}</em></div>}
 <div className="verticalPrompts">{prompts.map(p=><button key={p} onClick={()=>ask(p)} disabled={loading}>{p}</button>)}</div>{err&&<small className="formError">{err}</small>}
 <div className="copilotInput"><input value={q} onChange={e=>setQ(e.target.value)} onKeyDown={e=>{if(e.key==="Enter")ask()}} placeholder="Ask MediLink…"/><button onClick={()=>ask()} disabled={loading||!q.trim()} aria-label="Send">{loading?<span className="spinner"/>:<Send size={17}/>}</button></div></section>
}
