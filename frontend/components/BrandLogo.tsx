export default function BrandLogo({ compact = false }: { compact?: boolean }) {
  return (
    <span className="brandLockup" aria-label="MediLink AI">
      <span className="asclepiusMark" aria-hidden="true">
        <svg viewBox="0 0 64 64" role="img">
          <path d="M32 7v50" className="rod" />
          <path d="M43 13c-15-5-22 3-17 10 4 5 18 3 18 11 0 7-15 7-18 12-3 5 2 10 12 9" className="snake" />
          <circle cx="44" cy="13" r="3.5" className="snakeHead" />
        </svg>
      </span>
      {!compact && <span className="brandWords">MediLink <b>AI</b><small>Care. Anywhere. Always.</small></span>}
    </span>
  );
}
