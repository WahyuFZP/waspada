"use client";

import { animate } from "animejs";
import { motion, useReducedMotion } from "motion/react";
import { useEffect, useRef, type ReactNode } from "react";

// Angka naik dari 0: menunjukkan skor adalah jumlah bobot aturan yang terkumpul, bukan angka tetap.
// Memakai anime.js seperti angka ringkasan di landing, agar satu teknik untuk semua hitung naik.
export function CountUp({ value, className }: { value: number; className?: string }) {
  const reduce = useReducedMotion();
  const ref = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    if (reduce || !ref.current) return;
    let run: ReturnType<typeof animate> | undefined;
    // mulai di frame pertama: bila browser belum menggambar (tab di latar), angka asli tetap tampil, bukan 0
    const id = requestAnimationFrame(() => {
      run = animate(ref.current!, {
        innerHTML: [0, value],
        modifier: (v: number) => Math.round(v),
        duration: 1800,
        ease: "outExpo",
      });
    });
    return () => {
      cancelAnimationFrame(id);
      run?.revert();
    };
  }, [value, reduce]);
  return (
    <span ref={ref} className={className}>
      {value}
    </span>
  );
}

// Section naik halus sekali saat pertama masuk layar (DESIGN.md: scroll reveal), tidak berulang saat digulir balik.
export function Reveal({ children, className, delay = 0 }: { children: ReactNode; className?: string; delay?: number }) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      className={className}
      initial={reduce ? false : { opacity: 0, y: 56, scale: 0.97 }}
      whileInView={{ opacity: 1, y: 0, scale: 1 }}
      viewport={{ once: true, amount: 0.15 }}
      transition={{ duration: 0.85, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}
