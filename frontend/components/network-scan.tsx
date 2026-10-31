"use client";

import { animate, createDrawable, createMotionPath, createScope, createTimeline, stagger } from "animejs";
import { useEffect, useRef } from "react";

const HUB = { x: 240, y: 180 };
const NODES = [
  { x: 80, y: 70, label: "Server" },
  { x: 400, y: 70, label: "Router" },
  { x: 50, y: 200, label: "PC Staf" },
  { x: 430, y: 200, label: "Laptop" },
  { x: 130, y: 310, label: "Ponsel", threat: true },
  { x: 350, y: 310, label: "CCTV" },
];
const SWEEP = 3200; // ms satu kali sapuan pindai dari atas ke bawah

// Ilustrasi: perangkat satuan terhubung ke WASPADA, paket data mengalir, garis pindai menyapu dan menandai tiap perangkat.
export function NetworkScan() {
  const root = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const scope = createScope({ root, mediaQueries: { reduce: "(prefers-reduced-motion: reduce)" } }).add((self) => {
      if (self?.matches.reduce) return; // diam: jaringan tetap terlihat utuh tanpa gerak

      animate(createDrawable(".link"), { draw: ["0 0", "0 1"], duration: 1200, delay: stagger(120), ease: "outQuad" });

      root.current!.querySelectorAll<SVGPathElement>(".link").forEach((path, i) => {
        animate(`.packet-${i}`, {
          ...createMotionPath(path),
          opacity: [0, 1, 1, 0],
          duration: 2400,
          delay: 1200 + i * 400,
          loop: true,
          alternate: true,
          ease: "inOutSine",
        });
      });

      createTimeline({ loop: true, delay: 1200 })
        .add(".beam", { translateY: [-60, 380], duration: SWEEP, ease: "linear" }, 0)
        .add(
          ".ring",
          {
            opacity: [0, 0.9, 0],
            scale: [0.6, 1.4],
            duration: 900,
            delay: (el: unknown) => (Number((el as SVGElement).dataset.y) / 360) * SWEEP,
            ease: "outQuad",
          },
          0,
        );

      animate(".threat", { opacity: [1, 0.25], duration: 700, loop: true, alternate: true, ease: "inOutSine" });
      animate(".hub-pulse", { scale: [1, 1.6], opacity: [0.5, 0], duration: 2000, loop: true, ease: "outQuad" });
    });
    return () => scope.revert();
  }, []);

  const origin = { transformBox: "fill-box", transformOrigin: "center" } as const;

  return (
    <svg ref={root} viewBox="0 0 480 360" role="img" aria-labelledby="netscan-title" className="h-auto w-full">
      <title id="netscan-title">
        Enam perangkat jaringan terhubung ke WASPADA dan dipindai berkala; satu ponsel ditandai mencurigakan.
      </title>
      <defs>
        <linearGradient id="beam-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="var(--color-siber-bright)" stopOpacity="0" />
          <stop offset="1" stopColor="var(--color-siber-bright)" stopOpacity="0.28" />
        </linearGradient>
      </defs>

      {NODES.map((n) => (
        <path
          key={`l-${n.label}`}
          className="link"
          d={`M${HUB.x} ${HUB.y} L${n.x} ${n.y}`}
          stroke={n.threat ? "var(--color-sev-critical)" : "var(--color-siber)"}
          strokeWidth="1.5"
          strokeDasharray={n.threat ? "4 4" : undefined}
          fill="none"
        />
      ))}

      {NODES.map((n, i) => (
        <circle key={`p-${n.label}`} className={`packet-${i}`} r="3.5" fill="var(--color-gold)" opacity="0" />
      ))}

      <g className="beam" style={{ transform: "translateY(-60px)" }}>
        <rect x="0" y="0" width="480" height="60" fill="url(#beam-fill)" />
        <line x1="0" y1="60" x2="480" y2="60" stroke="var(--color-siber-bright)" strokeWidth="1.5" />
      </g>

      {NODES.map((n) => (
        <g key={n.label} transform={`translate(${n.x} ${n.y})`}>
          <circle
            className="ring"
            data-y={n.y}
            r="30"
            fill="none"
            stroke={n.threat ? "var(--color-sev-critical)" : "var(--color-siber-bright)"}
            strokeWidth="2"
            opacity="0"
            style={origin}
          />
          <rect x="-20" y="-16" width="40" height="27" rx="4" fill="var(--color-surface-2)" stroke="var(--color-line)" />
          <rect
            x="-16"
            y="-12"
            width="32"
            height="19"
            rx="2"
            fill={n.threat ? "var(--color-sev-critical)" : "var(--color-siber)"}
            fillOpacity="0.45"
          />
          <path d="M-6 15 H6 M0 11 V15" stroke="var(--color-line)" strokeWidth="2" />
          {n.threat && <circle className="threat" cx="18" cy="-16" r="5" fill="var(--color-sev-critical)" />}
          <text y="34" textAnchor="middle" className="font-data" fontSize="11" fill="var(--color-ink-muted)">
            {n.label}
          </text>
        </g>
      ))}

      <g transform={`translate(${HUB.x} ${HUB.y})`}>
        <circle className="hub-pulse" r="34" fill="var(--color-siber-bright)" opacity="0" style={origin} />
        <circle r="34" fill="var(--color-bg)" stroke="var(--color-gold)" strokeWidth="2" />
        {/* perisai, merujuk lambang satuan */}
        <path d="M0 -18 L15 -11 V2 C15 11 8 17 0 20 C-8 17 -15 11 -15 2 V-11 Z" fill="var(--color-siber)" stroke="var(--color-gold)" strokeWidth="1.5" />
        <path d="M-6 1 L-1 6 L7 -4" stroke="var(--color-ink)" strokeWidth="2.2" fill="none" strokeLinecap="round" />
      </g>
    </svg>
  );
}
