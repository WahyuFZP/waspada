"use client";

import { AnimatePresence, motion } from "motion/react";
import { useState } from "react";
import { eventLabel, facts, formatTime, originLabel, REGION_LABEL, topicLabel } from "@/lib/api";
import type { Event } from "@/lib/types";
import { Segmented } from "./segmented";
import { SourceLink } from "./source-link";

// "security" = semua yang bukan berita: log auth, Suricata, CISA KEV
type Filter = "all" | "security" | "domestic" | "foreign";
const pick = (e: Event, f: Filter) => f === "all" || (f === "security" ? !e.region : e.region === f);

export function NewsFeed({ events, loaded }: { events: Event[]; loaded: boolean }) {
  const [filter, setFilter] = useState<Filter>("all");
  const shown = events.filter((e) => pick(e, filter));

  return (
    <section id="arus-berita" aria-labelledby="feed-title" className="flex min-w-0 flex-col gap-4">
      <h2 id="feed-title" className="font-pixel text-xl font-bold md:text-2xl">
        Arus Kejadian
      </h2>
      <Segmented
        id="feed-region"
        label="Saring asal kejadian"
        value={filter}
        onChange={setFilter}
        options={[
          { value: "all", label: "Semua" },
          { value: "security", label: "Siber" },
          { value: "domestic", label: REGION_LABEL.domestic },
          { value: "foreign", label: REGION_LABEL.foreign },
        ]}
      />
      {loaded && shown.length === 0 && (
        <p className="text-ink-muted">
          {events.length === 0
            ? "Belum ada kejadian. Log keamanan, kecocokan CISA KEV, dan berita yang cocok dengan kamus topik akan tampil di sini."
            : "Belum ada kejadian dari asal ini."}
        </p>
      )}
      {/* relative: elemen absolute di dalam (teks sr-only) harus terpotong kotak scroll ini; tanpa ini mereka
          lepas ke tingkat halaman dan membuat halaman bisa digulir jauh melewati footer */}
      <ul className="relative flex flex-col gap-2 xl:max-h-[calc(100dvh-16rem)] xl:overflow-y-auto xl:pr-1">
        <AnimatePresence initial={false}>
          {shown.map((e, i) => (
            <motion.li
              // satu artikel bisa menjadi beberapa event (beda kategori), jadi kunci memakai event_type juga
              key={`${e.url ?? e.title}-${e.event_type}-${e.timestamp}-${i}`}
              layout
              initial={{ opacity: 0, x: 16 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3, delay: i === 0 ? 0.05 : 0 }}
              className="rounded-xl border border-line bg-white/[0.02] p-3"
            >
              <p className="font-data text-xs text-ink-muted">
                {formatTime(e.timestamp)} · {e.source} · {originLabel(e)}
              </p>
              <p className="mt-1 leading-snug">{e.title}</p>
              {facts(e) && <p className="font-data mt-1 text-xs text-ink-muted">{facts(e)}</p>}
              <p className="font-data mt-2 flex flex-wrap gap-2 text-xs">
                {e.topic && (
                  <span className="rounded-sm bg-surface-2 px-1.5 py-0.5 text-ink-muted">{topicLabel(e.topic)}</span>
                )}
                <span className="rounded-sm bg-surface-2 px-1.5 py-0.5 text-ink-muted">{eventLabel(e.event_type)}</span>
                {e.demo && <span className="rounded-sm bg-surface-2 px-1.5 py-0.5 text-ink-muted">Simulasi</span>}
              </p>
              {(e.url || e.region) && <SourceLink url={e.url} />}
            </motion.li>
          ))}
        </AnimatePresence>
      </ul>
    </section>
  );
}
