"use client";

import { AnimatePresence, motion, useReducedMotion } from "motion/react";

// Jaring pertahanan: bola dunia berjaring (motif lambang Pussiberad). Simpul di permukaan = sumber data,
// garis ke inti = korelasi. Paket bergerak hanya saat stream hidup; inti berdenyut sekali per alert baru.
const C = 300;
const R = 230;
const NODES = [
  [-150, -120], [-40, -205], [95, -170], [185, -60], [200, 70], [110, 175], [-20, 215], [-150, 140], [-210, 20], [-95, -15], [60, -55], [30, 95],
].map(([x, y]) => ({ x: C + x, y: C + y }));
const MESH = [
  [0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 8], [8, 0], [0, 9], [9, 10], [10, 2], [10, 3], [9, 7], [9, 11], [11, 5], [11, 4], [8, 9], [1, 10], [6, 11],
];

export function NetworkGlobe({ live, pulseKey }: { live: boolean; pulseKey: string | null }) {
  const reduce = useReducedMotion();
  const moving = live && !reduce;

  return (
    <svg viewBox="0 0 600 600" aria-hidden className="h-full w-full">
      <defs>
        <radialGradient id="globe-fill" cx="50%" cy="45%" r="55%">
          <stop offset="0%" stopColor="#3f7a40" stopOpacity="0.35" />
          <stop offset="100%" stopColor="#070d08" stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* bola dunia: lingkar luar, garis lintang & bujur */}
      <circle cx={C} cy={C} r={R} fill="url(#globe-fill)" stroke="#d6af58" strokeOpacity="0.35" strokeWidth="1.5" />
      {[0.35, 0.7].map((k) => (
        <ellipse key={`lat${k}`} cx={C} cy={C} rx={R} ry={R * k} fill="none" stroke="#60b45f" strokeOpacity="0.18" />
      ))}
      {[0.3, 0.65].map((k) => (
        <ellipse key={`lon${k}`} cx={C} cy={C} rx={R * k} ry={R} fill="none" stroke="#60b45f" strokeOpacity="0.18" />
      ))}

      {/* jaring antarsimpul */}
      {MESH.map(([a, b]) => (
        <line key={`${a}-${b}`} x1={NODES[a].x} y1={NODES[a].y} x2={NODES[b].x} y2={NODES[b].y} stroke="#60b45f" strokeOpacity="0.22" />
      ))}
      {/* jalur korelasi ke inti */}
      {NODES.map((n, i) => (
        <line key={`c${i}`} x1={n.x} y1={n.y} x2={C} y2={C} stroke="#d6af58" strokeOpacity="0.12" strokeDasharray="3 6" />
      ))}
      {NODES.map((n, i) => (
        <circle key={`n${i}`} cx={n.x} cy={n.y} r="4" fill="#60b45f" fillOpacity={live ? 0.9 : 0.35} />
      ))}

      {/* paket data: dari simpul ke inti, bergiliran */}
      {moving &&
        NODES.map((n, i) => (
          <motion.circle
            key={`p${i}`}
            r="3"
            fill="#d6af58"
            initial={{ cx: n.x, cy: n.y, opacity: 0 }}
            animate={{ cx: [n.x, C], cy: [n.y, C], opacity: [0, 1, 0] }}
            transition={{ duration: 2.4, delay: i * 0.55, repeat: Infinity, repeatDelay: NODES.length * 0.55 - 2.4, ease: "easeIn" }}
          />
        ))}

      {/* inti korelasi */}
      <circle cx={C} cy={C} r="16" fill="#0d170f" stroke="#d6af58" strokeWidth="2" />
      <circle cx={C} cy={C} r="6" fill={live ? "#60b45f" : "#a7b8a6"} />
      <AnimatePresence>
        {pulseKey && !reduce && (
          <motion.circle
            key={pulseKey}
            cx={C}
            cy={C}
            fill="none"
            stroke="#f05252"
            strokeWidth="2"
            initial={{ r: 16, opacity: 0.9 }}
            animate={{ r: R, opacity: 0 }}
            transition={{ duration: 1.6, ease: "easeOut" }}
          />
        )}
      </AnimatePresence>
    </svg>
  );
}
