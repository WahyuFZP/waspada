// Logo WASPADA: kentongan (alat peringatan dini pos ronda). Celah tengah = mulut sumber bunyi; tali gantung emas.
export function LogoMark({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 64" role="img" aria-label="WASPADA" className={className}>
      <path
        className="fill-siber-bright"
        fillRule="evenodd"
        d="M32 3a3 3 0 0 1 3 3v3h3a11 11 0 0 1 11 11v30a11 11 0 0 1-11 11H26a11 11 0 0 1-11-11V20A11 11 0 0 1 26 9h3V6a3 3 0 0 1 3-3zM28 20v30a4 4 0 0 0 8 0V20a4 4 0 0 0-8 0z"
      />
      <rect className="fill-gold" x="3" y="24" width="6" height="22" rx="3" />
      <rect className="fill-gold" x="55" y="24" width="6" height="22" rx="3" />
    </svg>
  );
}
