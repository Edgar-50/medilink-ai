import { useId } from "react";

export default function ScoreRing({ value, size = 84, stroke = 7, label, sub, tone = "violet" }: { value: number; size?: number; stroke?: number; label?: string; sub?: string; tone?: "violet" | "cyan" | "pulse" }) {
  const id = useId().replace(/:/g, "");
  const r = (size - stroke) / 2, c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, value));
  const stops = tone === "cyan" ? ["#25E0FF", "#7C5CFF"] : tone === "pulse" ? ["#FF3D77", "#FF9A5C"] : ["#7C5CFF", "#25E0FF"];
  return (
    <div className="ring" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <defs><linearGradient id={id} x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor={stops[0]} /><stop offset="1" stopColor={stops[1]} /></linearGradient></defs>
        <circle className="ringTrack" cx={size / 2} cy={size / 2} r={r} strokeWidth={stroke} fill="none" />
        <circle className="ringValue" cx={size / 2} cy={size / 2} r={r} strokeWidth={stroke} fill="none" stroke={`url(#${id})`} strokeLinecap="round" strokeDasharray={`${(c * pct) / 100} ${c}`} transform={`rotate(-90 ${size / 2} ${size / 2})`} />
      </svg>
      <div className="ringLabel"><b>{label ?? Math.round(pct)}</b>{sub && <small>{sub}</small>}</div>
    </div>
  );
}
