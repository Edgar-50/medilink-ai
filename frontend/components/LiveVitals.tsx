"use client";
import { useEffect, useMemo, useState } from "react";
import { Activity, BatteryMedium, Bluetooth, HeartPulse, Thermometer, Wind } from "lucide-react";
import { getLiveVitals, type LiveVitalsResponse } from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function LiveVitals({ compact=false }: { compact?: boolean }) {
  const [data,setData]=useState<LiveVitalsResponse|null>(null); const [connected,setConnected]=useState(true);
  useEffect(()=>{ let alive=true; const load=async()=>{ const t=getToken(); if(!t||!connected)return; try{const d=await getLiveVitals(t); if(alive)setData(d);}catch{}}; load(); const id=setInterval(load,5000); return()=>{alive=false;clearInterval(id)};},[connected]);
  const points=useMemo(()=>data?.trend ?? [70,72,71,74,73,72,75,72,71,73,72,74],[data]);
  const path=points.map((v,i)=>`${i===0?"M":"L"} ${i*(220/(points.length-1))} ${60-(v-60)*1.8}`).join(" ");
  return <div className={`liveVitals ${compact?"compact":""}`}>
    <div className="cardTop"><div><span className="eyebrow"><Activity size={14}/> MEDILINK WATCH</span><h2>Live vitals</h2></div><button className={`deviceStatus ${connected?"connected":""}`} onClick={()=>setConnected(v=>!v)}><Bluetooth size={14}/>{connected?"Connected":"Connect"}</button></div>
    <div className="vitalTiles">
      <div><HeartPulse/><span>Heart rate</span><b>{data?.heart_rate ?? 72}<small> bpm</small></b><em>Normal</em></div>
      <div><Wind/><span>SpO₂</span><b>{data?.spo2 ?? 98}<small>%</small></b><em>Normal</em></div>
      <div><Thermometer/><span>Temperature</span><b>{data?.temperature_c ?? 36.6}<small>°C</small></b><em>Normal</em></div>
      <div><Activity/><span>Blood pressure</span><b>{data?.blood_pressure ?? "118/76"}<small> mmHg</small></b><em></em></div>
    </div>
    {!compact && <svg className="vitalChart" viewBox="0 0 220 64" preserveAspectRatio="none"><path d={path}/></svg>}
    <div className="deviceMeta"><span><BatteryMedium size={14}/>{data?.battery ?? 84}% battery</span><span>Last sync {data?.last_sync ?? "just now"}</span><span className="Tag"> IoT stream</span></div>
  </div>;
}
