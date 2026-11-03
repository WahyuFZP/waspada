"use client";

import { animate, createScope, createTimeline, stagger, utils } from "animejs";
import { useEffect, useRef, type ReactNode } from "react";

// Objek 3D tanpa WebGL: wajah SVG ditumpuk `depth` lapis sepanjang sumbu Z (1px per lapis), sehingga terlihat tebal
// saat dimiringkan dengan perspektif CSS. Lapis depan berwarna terang, lapis belakang lebih gelap sebagai sisi objek.
function Stack({ depth, layer }: { depth: number; layer: (front: boolean) => ReactNode }) {
  return Array.from({ length: depth }, (_, i) => (
    <div key={i} aria-hidden className="absolute inset-0" style={{ transform: `translateZ(${-i}px)` }}>
      {layer(i === 0)}
    </div>
  ));
}

const reduceMotion = { reduce: "(prefers-reduced-motion: reduce)" };
const preserve = { transformStyle: "preserve-3d" } as const;

// Logo WASPADA sebagai kentongan pos ronda yang digantung. Saat halaman dibuka ia berayun sekali lalu diam,
// seperti baru dipukul: peringatan dibunyikan.
export function Kentongan3D({ className = "" }: { className?: string }) {
  const swing = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const scope = createScope({ root: swing, mediaQueries: reduceMotion }).add((self) => {
      if (self?.matches.reduce) return;
      animate(swing.current!, { rotateZ: [0, 24, -16, 10, -5, 2, 0], duration: 3200, delay: 450, ease: "outSine" });
    });
    return () => scope.revert();
  }, []);

  return (
    <div role="img" aria-label="Logo WASPADA: kentongan" className={className} style={{ perspective: "600px" }}>
      <div className="relative h-full w-full" style={{ ...preserve, transform: "rotateX(10deg) rotateY(-38deg)" }}>
        <div ref={swing} className="absolute inset-0" style={{ ...preserve, transformOrigin: "50% 6%" }}>
          <Stack
            depth={16}
            layer={(front) => (
              <svg viewBox="0 0 64 64" className="h-full w-full">
                <path
                  className={front ? "fill-siber-bright" : "fill-siber"}
                  fillRule="evenodd"
                  d="M32 3a3 3 0 0 1 3 3v3h3a11 11 0 0 1 11 11v30a11 11 0 0 1-11 11H26a11 11 0 0 1-11-11V20A11 11 0 0 1 26 9h3V6a3 3 0 0 1 3-3zM28 20v30a4 4 0 0 0 8 0V20a4 4 0 0 0-8 0z"
                />
                <rect className={front ? "fill-gold" : "fill-gold-deep"} x="3" y="24" width="6" height="22" rx="3" />
                <rect className={front ? "fill-gold" : "fill-gold-deep"} x="55" y="24" width="6" height="22" rx="3" />
              </svg>
            )}
          />
        </div>
      </div>
    </div>
  );
}

// Lima kelompok pemeriksaan Pemeriksa APK (aturan R01–R14), keluar-masuk dari layar ponsel. Isinya apa yang
// diperiksa, bukan hasil: halaman unggah belum punya hasil scan, jadi angka atau centang di sini akan karangan.
// x/y/z = posisi akhir relatif ke pusat layar (px): menyebar kiri/atas/bawah; kanan dibatasi agar tidak keluar halaman.
const CARDS = [
  { label: "Izin aplikasi", detail: "SMS, aksesibilitas, overlay", x: -128, y: -64, z: 70, dot: "bg-siber-bright" },
  { label: "Sertifikat", detail: "Penerbit, kunci debug", x: 30, y: -112, z: 95, dot: "bg-gold" },
  { label: "URL & domain", detail: "Bot Telegram, link pendek", x: -136, y: 20, z: 110, dot: "bg-siber-bright" },
  { label: "Kode tersembunyi", detail: "Packer, anti-emulator", x: -128, y: 104, z: 85, dot: "bg-siber-bright" },
  { label: "Judi online", detail: "Istilah taruhan, setor-tarik", x: 40, y: 176, z: 120, dot: "bg-gold" },
];

// Ponsel dengan paket APK di layarnya dan lima kartu pemeriksaan yang terus keluar-masuk dari layar.
// Hanya transform dan opacity yang dianimasikan (mulus, tanpa hitung ulang tata letak), dan opacity tidak pernah
// dipasang pada elemen 3D: opacity < 1 di elemen preserve-3d memipihkan lapisannya lalu "meloncat" saat selesai.
// Garis pindai dan titik kartu hanya bergerak saat APK benar-benar diproses, jadi menandai status nyata.
export function Phone3D({ scanning, className = "" }: { scanning: boolean; className?: string }) {
  const wrap = useRef<HTMLDivElement>(null);
  const turn = useRef<HTMLDivElement>(null);
  const beam = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const scope = createScope({ root: wrap, mediaQueries: reduceMotion }).add((self) => {
      const pops = [...wrap.current!.querySelectorAll<HTMLElement>(".pop")];
      if (self?.matches.reduce) {
        pops.forEach((el, i) => utils.set(el, { translateX: CARDS[i].x, translateY: CARDS[i].y, translateZ: CARDS[i].z, opacity: 1 }));
        return;
      }
      animate(wrap.current!, { opacity: [0, 1], duration: 700, ease: "outQuad" });
      animate(turn.current!, { rotateY: [-60, 0], duration: 1600, ease: "outExpo" });
      pops.forEach((el, i) => {
        const { x, y, z } = CARDS[i];
        // siklus tanpa henti: keluar dari layar sambil memantul, melayang ~3 detik, lalu masuk kembali ke layar.
        // Mulai berselang 700 ms, sehingga selalu ada kartu yang sedang keluar atau masuk.
        createTimeline({ loop: true, delay: 1000 + i * 700, loopDelay: 400 })
          .add(el, {
            translateX: [0, x],
            translateY: [0, y],
            translateZ: [0, z],
            scale: [0.3, 1],
            opacity: [0, 1],
            duration: 900,
            ease: "outBack(1.6)",
          })
          .add(
            el,
            {
              translateX: [x, 0],
              translateY: [y, 0],
              translateZ: [z, 0],
              scale: [1, 0.3],
              opacity: [1, 0],
              duration: 550,
              ease: "inBack(1.4)",
            },
            "+=3000",
          );
      });
      // melayang pelan di lapis dalam kartu, agar tidak bertabrakan dengan transform saat kartu muncul
      animate(".float", {
        translateY: [0, -6],
        duration: stagger(450, { start: 2000 }), // tiap kartu beda tempo, jadi tidak naik-turun serempak
        delay: 2000,
        loop: true,
        alternate: true,
        ease: "inOutSine",
      });
    });
    return () => scope.revert();
  }, []);

  useEffect(() => {
    if (!scanning || matchMedia(reduceMotion.reduce).matches) return;
    const travel = beam.current!.parentElement!.clientHeight;
    const sweep = animate(beam.current!, { translateY: [0, travel], opacity: [0, 1, 1, 0], duration: 1300, loop: true, ease: "inOutSine" });
    const blink = animate(wrap.current!.querySelectorAll(".dot"), {
      opacity: [1, 0.25],
      duration: 450,
      delay: stagger(150),
      loop: true,
      alternate: true,
    });
    return () => {
      sweep.revert();
      blink.revert();
    };
  }, [scanning]);

  return (
    <div
      ref={wrap}
      role="img"
      aria-label={
        scanning
          ? "Ponsel: APK sedang diperiksa"
          : "Ponsel dengan paket APK; kartu hal yang diperiksa (izin, sertifikat, URL dan domain, kode tersembunyi, judi online) keluar-masuk dari layarnya"
      }
      className={className}
      style={{ perspective: "900px" }}
    >
      <div className="relative h-full w-full" style={{ ...preserve, transform: "rotateX(14deg) rotateY(-28deg) rotateZ(3deg)" }}>
        <div ref={turn} className="absolute inset-0" style={{ ...preserve, willChange: "transform" }}>
          <Stack
            depth={14}
            layer={(front) => (
              <svg viewBox="0 0 66 112" className="h-full w-full" shapeRendering="geometricPrecision">
                {/* tombol daya & volume di sisi kanan, ikut tebal karena ada di semua lapis */}
                <rect x="63" y="30" width="2.5" height="13" rx="1.2" className={front ? "fill-siber" : "fill-line"} />
                <rect x="63" y="47" width="2.5" height="8" rx="1.2" className={front ? "fill-siber" : "fill-line"} />
                <rect
                  x="1"
                  y="1"
                  width="62"
                  height="110"
                  rx="11"
                  className={front ? "fill-surface-2 stroke-siber" : "fill-line"}
                  strokeWidth="1.5"
                />
                {front && (
                  <>
                    <defs>
                      <linearGradient id="phone-screen" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0" stopColor="var(--color-surface)" />
                        <stop offset="1" stopColor="var(--color-bg)" />
                      </linearGradient>
                    </defs>
                    <rect x="6" y="12" width="52" height="88" rx="5" fill="url(#phone-screen)" />
                    <circle cx="32" cy="7" r="1.8" className="fill-line" />
                    {/* paket APK: kotak isometrik berbidang (atas terang, kiri gelap, kanan sedang) agar terbaca mulus */}
                    <path d="M32 36 46 44 32 52 18 44z" className="fill-gold" />
                    <path d="M18 44 32 52v16L18 60z" className="fill-gold-deep" />
                    <path d="M46 44 32 52v16l14-8z" className="fill-gold/70" />
                    <text x="32" y="82" textAnchor="middle" fontSize="7" className="font-data fill-ink-muted">
                      APK
                    </text>
                  </>
                )}
              </svg>
            )}
          />
          <div aria-hidden className="absolute bottom-[12%] left-[11%] right-[13%] top-[12%] overflow-hidden" style={{ transform: "translateZ(1px)" }}>
            <div ref={beam} className="h-1.5 rounded-full bg-siber-bright/80" style={{ opacity: 0 }} />
          </div>
          {CARDS.map((c) => (
            <div key={c.label} aria-hidden className="pop absolute left-1/2 top-[46%] h-0 w-0 opacity-0">
              {/* pembungkus berukuran nol + lapis tengah memusatkan kartu tanpa menjorok keluar halaman */}
              <div className="w-max -translate-x-1/2 -translate-y-1/2">
                <div className="float flex w-max items-start gap-2 whitespace-nowrap rounded-md border border-line bg-surface px-2.5 py-1.5 shadow-[0_10px_18px_-8px_rgb(0_0_0/0.85)]">
                  <span className={`dot mt-1 h-2 w-2 shrink-0 rounded-full ${c.dot}`} />
                  <span className="flex flex-col leading-tight">
                    <span className="font-data text-[11px] text-ink">{c.label}</span>
                    <span className="font-data text-[11px] text-ink-muted">{c.detail}</span>
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
