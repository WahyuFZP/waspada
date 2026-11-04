"use client";

import { MotionConfig } from "motion/react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { AttackerIps } from "@/components/attacker-ips";
import { ConnectionStatus } from "@/components/connection-status";
import { ActivityChart, LogStream, SourceStatus } from "@/components/log-panels";
import { LogoMark } from "@/components/logo-mark";
import { Reveal } from "@/components/reveal";
import { SignalLines } from "@/components/signal-lines";
import { Stat } from "@/components/stats-bar";
import { useAlertStream } from "@/hooks/use-alert-stream";
import { API } from "@/lib/api";

const SOURCES = "auth,suricata"; // log keamanan saja; berita ada di /pemantauan

export default function LogPage() {
  const { events, status, loaded } = useAlertStream(undefined, SOURCES);
  // "sekarang" bergeser tiap 15 detik: grafik per menit dan status aktif/diam ikut berjalan tanpa log baru
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 15_000);
    return () => clearInterval(id);
  }, []);
  useEffect(() => setNow(Date.now()), [events.length]); // tiap log baru juga menyegarkan "sekarang"

  const count = (pred: (t: string) => boolean) => events.filter((e) => pred(e.event_type)).length;
  const failed = count((t) => t === "auth.failed");

  return (
    <MotionConfig reducedMotion="user">
      <SignalLines />
      <nav className="sticky top-0 z-30 border-b border-line bg-bg/85 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-[1400px] items-center justify-between gap-4 px-4 md:px-6">
          <div className="flex items-center gap-8">
            <Link href="/" className="flex items-center gap-2 font-display text-2xl font-bold leading-none">
              <LogoMark className="h-7 w-7" />
              WASPADA
            </Link>
            <ul className="font-data hidden gap-6 text-xs text-ink-muted sm:flex">
              <li>
                <Link href="/pemantauan" className="hover:text-ink">
                  Pemantauan
                </Link>
              </li>
              <li>
                <span aria-current="page" className="text-ink">
                  Log keamanan
                </span>
              </li>
              <li>
                <Link href="/apk" className="hover:text-ink">
                  Pemeriksa APK
                </Link>
              </li>
            </ul>
          </div>
          <ConnectionStatus status={status} />
        </div>
      </nav>

      <main className="mx-auto flex max-w-[1400px] flex-col gap-8 px-4 py-10 md:px-6">
        <Reveal>
          <h1 className="font-display text-5xl font-bold leading-none md:text-6xl">Log keamanan</h1>
          <p className="mt-3 max-w-3xl text-ink-muted md:text-lg">
            Baris log asli dari server satuan (login SSH dan peringatan Suricata), dikirim pengirim log secara live.
            Setiap baris diberi asal IP, lalu dicocokkan mesin korelasi untuk mendeteksi brute force dan intrusi.
          </p>
          {status === "reconnecting" && !loaded && (
            <p role="alert" className="mt-4 rounded-lg border border-sev-critical/50 bg-sev-critical/10 p-4 text-sm">
              Server pemantauan di <span className="font-data">{API}</span> belum dapat dijangkau. Pastikan backend aktif
              (<span className="font-data">docker compose up</span>). Sistem akan menyambung ulang secara otomatis.
            </p>
          )}
        </Reveal>

        <Reveal>
          <dl className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Stat label="Login gagal" value={failed} tone={failed ? "text-sev-high" : "text-ink"} />
            <Stat label="Login berhasil" value={count((t) => t === "auth.success")} />
            <Stat label="Peringatan IDS" value={count((t) => t.startsWith("ids."))} />
            <Stat label="IP sumber unik" value={new Set(events.map((e) => e.src_ip).filter(Boolean)).size} />
          </dl>
          <p className="font-data mt-2 text-xs text-ink-muted">Dihitung dari 200 baris log terbaru.</p>
        </Reveal>

        <Reveal className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_380px]">
          <ActivityChart events={events} now={now} />
          <SourceStatus events={events} now={now} />
        </Reveal>

        <Reveal>
          <LogStream events={events} loaded={loaded} />
        </Reveal>

        <Reveal>
          <AttackerIps events={events} loaded={loaded} />
        </Reveal>

        <Reveal>
          <section aria-labelledby="ship-title" className="slab rounded-2xl border border-line bg-surface p-5 md:p-6">
            <h2 id="ship-title" className="font-display text-2xl font-bold">
              Mengirim log dari server satuan
            </h2>
            <p className="mt-2 max-w-3xl text-sm text-ink-muted">
              Salin <span className="font-data text-ink">shipper/waspada_shipper.py</span> ke server (cukup Python 3.8,
              tanpa instalasi tambahan), lalu jalankan dengan token yang sama dengan <span className="font-data text-ink">INGEST_TOKEN</span>{" "}
              di backend. Pengirim membaca baris baru, tahan rotasi log, dan menyimpan antrean bila SIEM sedang tidak terjangkau.
            </p>
            <pre className="font-data mt-4 overflow-x-auto rounded-lg border border-line bg-bg p-4 text-xs leading-relaxed text-ink">
              {`INGEST_TOKEN=<token> python3 waspada_shipper.py \\
  --api http://<alamat-siem>:8000 \\
  --auth /var/log/auth.log \\
  --suricata /var/log/suricata/eve.json`}
            </pre>
            <p className="font-data mt-3 text-xs text-ink-muted">
              Demo di laptop ini: coba login ke server latihan dengan{" "}
              <span className="text-ink">ssh latihan@localhost -p 2222</span>. Setiap percobaan muncul di halaman ini dalam
              hitungan detik.
            </p>
          </section>
        </Reveal>
      </main>

      <footer className="font-data border-t border-line px-4 py-6 text-center text-xs text-ink-muted">
        WASPADA · Log berasal dari server yang menjalankan pengirim log. Murni pemantauan, bukan alat ofensif.
      </footer>
    </MotionConfig>
  );
}
