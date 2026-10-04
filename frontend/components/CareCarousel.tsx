"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { ChevronLeft, ChevronRight, HeartPulse, ShieldCheck, Sparkles } from "lucide-react";

const slides = [
  { image:"https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=1600&q=82", eyebrow:"CONNECTED CARE", title:"Healthcare without borders", text:"Appointments, records, remote monitoring and secure virtual care in one calm workspace.", cta:"Find care", href:"/doctors" },
  { image:"https://images.unsplash.com/photo-1551076805-e1869033e561?auto=format&fit=crop&w=1600&q=82", eyebrow:"RESPONSIBLE AI", title:"Intelligence that supports care", text:"Explainable routing, record-aware assistance and clinician-reviewed workflows instead of black-box decisions.", cta:"Ask MediLink AI", href:"/ai-match" },
  { image:"https://images.unsplash.com/photo-1584515933487-779824d29309?auto=format&fit=crop&w=1600&q=82", eyebrow:"REMOTE MONITORING", title:"Vitals that travel with you", text:"Connect MediLink Watch, stream connected vitals and surface trends for patients and clinicians.", cta:"Open MediLink Watch", href:"/watch" },
];

export default function CareCarousel() {
  const [index, setIndex] = useState(0);
  useEffect(() => { const id = setInterval(() => setIndex(i => (i + 1) % slides.length), 6500); return () => clearInterval(id); }, []);
  const s = slides[index];
  return <section className="careCarousel" style={{backgroundImage:`linear-gradient(90deg, rgba(3,13,27,.92), rgba(3,13,27,.52), rgba(3,13,27,.18)), url(${s.image})`}}>
    <div className="careCarouselCopy"><span className="eyebrow"><Sparkles size={14}/>{s.eyebrow}</span><h2>{s.title}</h2><p>{s.text}</p><div className="carouselActions"><Link href={s.href} className="btn primary">{s.cta}</Link><span className="trustLine"><ShieldCheck size={15}/> Secure connected care</span></div></div>
    <button className="carouselArrow left" onClick={() => setIndex((index + slides.length - 1) % slides.length)} aria-label="Previous slide"><ChevronLeft/></button>
    <button className="carouselArrow right" onClick={() => setIndex((index + 1) % slides.length)} aria-label="Next slide"><ChevronRight/></button>
    <div className="carouselDots" aria-label="Carousel position">{slides.map((_,i)=><button key={i} className={i===index?"on":""} onClick={()=>setIndex(i)} aria-label={`Show slide ${i+1}`}/>)}</div>
    <div className="heroPulse"><HeartPulse size={18}/> Live care network</div>
  </section>;
}
