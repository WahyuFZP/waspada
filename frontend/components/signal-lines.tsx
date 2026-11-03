"use client";

import { animate } from "animejs";
import { useEffect, useRef } from "react";

const COUNT = 14;
const rand = (min: number, max: number) => min + Math.random() * (max - min);

// Latar "sinyal": garis pendek melintas di jalur horizontal/vertikal secara acak, menggambarkan sinyal dari banyak
// sumber yang diolah WASPADA (Wide-Area Signal Processing). Hijau = sinyal, emas = paket data (warna yang sama dengan
// paket di jaring hero). Redup agar teks tetap terbaca, dan tidak bergerak sama sekali saat reduce motion.
export function SignalLines() {
  const root = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let alive = true;
    const runs: (ReturnType<typeof animate> | undefined)[] = [];
    const lines = [...root.current!.children] as HTMLElement[];

    const fly = (el: HTMLElement, i: number, first: boolean) => {
      if (!alive) return;
      const vertical = Math.random() < 0.5;
      const back = Math.random() < 0.5; // arah: kiri->kanan/atas->bawah atau sebaliknya
      const lane = Math.round(rand(1, 19)) * 5; // jalur kelipatan 5%: garis tetap sejajar seperti jalur sirkuit
      const len = rand(90, 240);
      const color = Math.random() < 0.2 ? "var(--color-gold)" : "var(--color-siber-bright)";
      const side = vertical ? (back ? "to top" : "to bottom") : back ? "to left" : "to right";
      const span = (vertical ? innerHeight : innerWidth) + len;
      el.style.cssText = `${vertical ? "left" : "top"}:${lane}%;${vertical ? "top" : "left"}:0;${
        vertical ? `width:1px;height:${len}px` : `height:1px;width:${len}px`
      };background:linear-gradient(${side},transparent,${color});opacity:0.45`;
      runs[i] = animate(el, {
        [vertical ? "translateY" : "translateX"]: back ? [span, -len] : [-len, span],
        duration: rand(3500, 8000),
        delay: first ? rand(0, 5000) : rand(400, 3000),
        ease: "linear",
        onComplete: () => fly(el, i, false),
      });
    };

    lines.forEach((el, i) => fly(el, i, true));
    return () => {
      alive = false;
      runs.forEach((r) => r?.pause());
    };
  }, []);

  return (
    <div ref={root} aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      {Array.from({ length: COUNT }, (_, i) => (
        <span key={i} className="absolute block opacity-0" />
      ))}
    </div>
  );
}
