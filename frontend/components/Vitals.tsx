"use client";
import { useEffect, useState } from "react";
import { Droplets, HeartPulse, Thermometer, Wind } from "lucide-react";
import EcgLine from "@/components/EcgLine";

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));

/** Presentation helper for vital-sign cards. */
export default function Vitals({ title = "Live vitals", name }: { title?: string; name?: string }) {
  const [v, setV] = useState({ hr: 72, spo2: 98, temp: 36.6, rr: 15 });
  useEffect(() => {
    const t = setInterval(() => setV(p => ({
      hr: Math.round(clamp(p.hr + (Math.random() - 0.5) * 4, 64, 84)),
      spo2: Math.round(clamp(p.spo2 + (Math.random() - 0.5) * 1.4, 96, 99)),
      temp: Math.round(clamp(p.temp + (Math.random() - 0.5) * 0.1, 36.4, 36.9) * 10) / 10,
      rr: Math.round(clamp(p.rr + (Math.random() - 0.5) * 2, 13, 18)),
    })), 1400);
    return () => clearInterval(t);
  }, []);
  const items = [
    { icon: HeartPulse, label: "Heart rate", value: v.hr, unit: "bpm", tone: "pulse" },
    { icon: Droplets, label: "Oxygen", value: v.spo2, unit: "%", tone: "cyan" },
    { icon: Thermometer, label: "Temperature", value: v.temp.toFixed(1), unit: "°C", tone: "violet" },
    { icon: Wind, label: "Respiration", value: v.rr, unit: "/min", tone: "cyan" },
  ];
  return (
    <div className="vitals">
      <div className="vitalsHead">
        <div><b>{title}</b>{name && <span>{name}</span>}</div>
        <span className="sampleTag"><i /> Sample data</span>
      </div>
      <EcgLine className="vitalsEcg" duration={6} />
      <div className="vitalsGrid">
        {items.map(({ icon: Icon, label, value, unit, tone }) => (
          <div className={`vital ${tone}`} key={label}>
            <Icon size={16} /><span>{label}</span>
            <strong>{value}<small>{unit}</small></strong>
          </div>
        ))}
      </div>
    </div>
  );
}
