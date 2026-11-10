// Logo WASPADA: kentongan (alat peringatan dini pos ronda), digambar piksel di kisi 16×16 agar seragam dengan tema
// piksel. Celah tengah = mulut sumber bunyi; pegangan emas. Bayangan = bentuk yang sama digeser 1 piksel.
// Tampil paling tajam pada kelipatan 17px (mis. 34px), karena viewBox 17 unit termasuk bayangan.
const BODY = [
  [7, 0, 2, 2], // gantungan
  [5, 2, 6, 1],
  [4, 3, 8, 1],
  [3, 4, 10, 10], // badan
  [4, 14, 8, 1],
  [5, 15, 6, 1],
];
const HANDLES = [
  [1, 6, 2, 7],
  [13, 6, 2, 7],
];
const px = (parts: number[][], fill: string, d = 0) =>
  parts.map(([x, y, w, h]) => <rect key={`${fill}-${x}-${y}`} x={x + d} y={y + d} width={w} height={h} fill={fill} />);

export function LogoMark({ className = "", label = "WASPADA", swing = false }: { className?: string; label?: string; swing?: boolean }) {
  return (
    <svg viewBox="0 0 17 17" role="img" aria-label={label} shapeRendering="crispEdges" className={className}>
      {/* swing: ayunan sekali saat halaman dibuka (.px-swing di globals.css), hanya untuk logo besar di landing */}
      <g className={swing ? "px-swing" : undefined}>
        {px(BODY, "var(--color-siber)", 1)}
        {px(HANDLES, "var(--color-gold-deep)", 1)}
        {px(BODY, "var(--color-siber-bright)")}
        <rect x="4" y="4" width="1" height="9" fill="var(--color-ink)" fillOpacity="0.55" /> {/* kilap tepi kiri */}
        {px(HANDLES, "var(--color-gold)")}
        <rect x="7" y="5" width="2" height="8" fill="var(--color-bg)" /> {/* celah kentongan */}
      </g>
    </svg>
  );
}
