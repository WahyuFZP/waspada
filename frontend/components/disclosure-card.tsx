"use client";

// Kartu "Draf laporan responsible disclosure" (#18): teks santun untuk DITINJAU & DIKIRIM SENDIRI.
// Tombol Salin hanya menyalin ke clipboard pengguna — tidak mengirim apa pun ke mana pun.
import { useState } from "react";

type Draf = { subjek: string; badan: string; catatan: string };

export function DisclosureCard({ d }: { d?: Draf | null }) {
  const [tersalin, setTersalin] = useState(false);
  if (!d) return null;
  const teks = `Subjek: ${d.subjek}\n\n${d.badan}`;

  async function salin() {
    try {
      await navigator.clipboard.writeText(teks);
      setTersalin(true);
      setTimeout(() => setTersalin(false), 2000);
    } catch {
      setTersalin(false); // clipboard tak tersedia: isi draf tetap terlihat untuk disalin manual
    }
  }

  return (
    <section aria-label="Draf laporan responsible disclosure" className="rounded-2xl border border-siber/40 bg-siber/5 p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="font-data text-xs uppercase tracking-[0.12em] text-siber-bright">Draf laporan — tinjau &amp; kirim sendiri</p>
        <button
          type="button"
          onClick={salin}
          className="font-data min-h-9 rounded-md border border-siber/50 bg-siber/10 px-3 text-xs text-siber-bright hover:bg-siber/20 print:hidden"
        >
          {tersalin ? "Tersalin ✓" : "Salin draf"}
        </button>
      </div>
      <p className="mt-3 font-data text-[11px] uppercase tracking-wide text-ink-muted">Subjek</p>
      <p className="font-data break-words text-sm text-ink">{d.subjek}</p>
      <p className="mt-3 font-data text-[11px] uppercase tracking-wide text-ink-muted">Isi</p>
      <pre className="mt-1 whitespace-pre-wrap break-words font-data text-xs leading-relaxed text-ink">{d.badan}</pre>
      <p className="mt-4 rounded-md border border-gold/40 bg-gold/5 p-3 text-xs italic text-ink-muted">{d.catatan}</p>
    </section>
  );
}
