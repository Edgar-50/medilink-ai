"use client";
import { useState } from "react";
import { Ambulance, MapPin, PhoneCall, X } from "lucide-react";

export default function EmergencyPanel() {
  const [confirm, setConfirm] = useState(false);
  return <>
    <section className="emergencyCard">
      <div><span className="eyebrow danger">EMERGENCY SOS</span><h3>Need urgent help?</h3><p>Use emergency services for a serious or life-threatening emergency. AI should never delay urgent care.</p></div>
      <button className="btn dangerBtn" onClick={()=>setConfirm(true)}><PhoneCall size={17}/> Emergency help</button>
    </section>
    {confirm && <div className="modalBackdrop" onMouseDown={()=>setConfirm(false)}><div className="modal dangerModal" onMouseDown={e=>e.stopPropagation()}>
      <button className="modalClose" onClick={()=>setConfirm(false)} aria-label="Close"><X/></button>
      <div className="dangerIcon"><Ambulance/></div><h2>Emergency assistance</h2><p>If someone is seriously ill, injured, unconscious, having severe chest pain or struggling to breathe, call emergency services now.</p>
      <a className="btn dangerBtn full" href="tel:999"><PhoneCall size={18}/> Call 999</a>
      <a className="btn outline full" href="https://www.nhs.uk/nhs-services/urgent-and-emergency-care-services/when-to-use-111/" target="_blank" rel="noreferrer"><MapPin size={18}/> NHS 111 guidance</a>
      <small>This button opens your device dialler; MediLink does not automatically place emergency calls.</small>
    </div></div>}
  </>;
}
