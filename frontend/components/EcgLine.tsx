const UNIT = "L40 50 L48 44 L56 50 L70 50 L76 57 L84 6 L92 82 L100 50 L120 50 L134 36 L148 50 L200 50";
const PERIODS = 6; // two identical halves of 3 periods -> seamless loop

export default function EcgLine({ className = "", duration = 7 }: { className?: string; duration?: number }) {
  let d = "M0 50";
  for (let i = 0; i < PERIODS; i++) d += " " + UNIT.replace(/L(\d+) (\d+)/g, (_, x, y) => `L${Number(x) + i * 200} ${y}`);
  return (
    <div className={`ecg ${className}`} aria-hidden="true">
      <svg viewBox={`0 0 ${PERIODS * 200} 100`} preserveAspectRatio="none" style={{ animationDuration: `${duration}s` }}>
        <path d={d} className="ecgGlow" />
        <path d={d} className="ecgTrace" />
      </svg>
    </div>
  );
}
