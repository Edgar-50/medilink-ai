"use client";
import Link from "next/link";
import {AlertTriangle,RefreshCw} from "lucide-react";
export default function ErrorPage({reset}:{error:Error&{digest?:string};reset:()=>void}){
  return <main className="standaloneState"><div className="stateCard"><AlertTriangle size={34}/><h1>Something interrupted this view</h1><p>Your MediLink session is still available. Try the view again or return to your dashboard.</p><div className="heroButtons"><button className="btn primary" onClick={reset}><RefreshCw size={16}/>Try again</button><Link className="btn secondary" href="/">Home</Link></div></div></main>;
}
