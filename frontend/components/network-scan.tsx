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

// garis bertingkat siku (gaya piksel): mendatar dari hub, lalu tegak ke perangkat
const link = (n: { x: number; y: number }) => `M${HUB.x} ${HUB.y} H${n.x} V${n.y}`;

// Ilustrasi: perangkat satuan terhubung ke WASPADA, paket data mengalir, garis pindai menyapu dan menandai tiap perangkat.
export function NetworkScan() {
  const root = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const scope = createScope({
      root,
      mediaQueries: { reduce: "(prefers-reduced-motion: reduce)", small: "(max-width: 767px)" },
    }).add((self) => {
      if (self?.matches.reduce || self?.matches.small) return; // diam: jaringan tetap terlihat utuh tanpa gerak

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
    <svg
      ref={root}
      viewBox="0 0 480 360"
      role="img"
      aria-labelledby="netscan-title"
      className="h-auto w-full"
      shapeRendering="crispEdges"
    >
      <title id="netscan-title">
        Enam perangkat jaringan terhubung ke WASPADA dan dipindai berkala; satu ponsel ditandai mencurigakan.
      </title>

      {NODES.map((n) => (
        <path
          key={`l-${n.label}`}
          className="link"
          d={link(n)}
          stroke={n.threat ? "var(--color-sev-critical)" : "var(--color-ink-muted)"}
          strokeWidth="2"
          strokeDasharray={n.threat ? "6 6" : undefined}
          strokeLinecap="square"
          fill="none"
        />
      ))}

      {NODES.map((n, i) => (
        <rect key={`p-${n.label}`} className={`packet-${i}`} x="-4" y="-4" width="8" height="8" fill="var(--color-ink)" opacity="0" />
      ))}

      <g className="beam" style={{ transform: "translateY(-60px)" }}>
        <rect x="0" y="0" width="480" height="60" fill="var(--color-ink)" fillOpacity="0.06" />
        <rect x="0" y="58" width="480" height="2" fill="var(--color-ink-muted)" />
      </g>

      {NODES.map((n) => (
        <g key={n.label} transform={`translate(${n.x} ${n.y})`}>
          <rect
            className="ring"
            data-y={n.y}
            x="-30"
            y="-30"
            width="60"
            height="60"
            fill="none"
            stroke={n.threat ? "var(--color-sev-critical)" : "var(--color-ink-muted)"}
            strokeWidth="2"
            opacity="0"
            style={origin}
          />
          <rect x="-20" y="-16" width="40" height="28" fill="var(--color-surface-2)" stroke="var(--color-ink-muted)" strokeWidth="2" />
          <rect x="-14" y="-10" width="28" height="16" fill={n.threat ? "var(--color-sev-critical)" : "var(--color-line)"} />
          <rect x="-8" y="14" width="16" height="4" fill="var(--color-ink-muted)" />
          {n.threat && <rect className="threat" x="14" y="-22" width="10" height="10" fill="var(--color-sev-critical)" />}
          <text y="36" textAnchor="middle" className="font-data" fontSize="11" fill="var(--color-ink-muted)">
            {n.label}
          </text>
        </g>
      ))}

      <g transform={`translate(${HUB.x} ${HUB.y})`}>
        <rect className="hub-pulse" x="-34" y="-34" width="68" height="68" fill="var(--color-ink)" opacity="0" style={origin} />
        <rect x="-34" y="-34" width="68" height="68" fill="var(--color-bg)" stroke="var(--color-ink)" strokeWidth="2" />
        {/* perisai berpiksel, merujuk lambang satuan */}
        <path
          d="M-14 -16 H14 V2 H10 V8 H6 V12 H2 V16 H-2 V12 H-6 V8 H-10 V2 H-14 Z"
          fill="var(--color-line)"
          stroke="var(--color-ink)"
          strokeWidth="2"
        />
        <path d="M-6 0 H-2 V4 H2 V0 H6 V-4" stroke="var(--color-ink)" strokeWidth="2" fill="none" strokeLinecap="square" />
      </g>
    </svg>
  );
}
