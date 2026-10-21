"use client";

import { AnimatePresence, motion } from "motion/react";
import { useState } from "react";
import { eventLabel, formatTime, REGION_LABEL, topicLabel } from "@/lib/api";
import type { Event } from "@/lib/types";
import { Segmented } from "./segmented";
import { SourceLink } from "./source-link";

type Region = "all" | Event["region"];

export function NewsFeed({ events, loaded }: { events: Event[]; loaded: boolean }) {
  const [region, setRegion] = useState<Region>("all");
  const shown = region === "all" ? events : events.filter((e) => e.region === region);

  return (
    <section id="arus-berita" aria-labelledby="feed-title" className="flex min-w-0 flex-col gap-4">
      <h2 id="feed-title" className="font-display text-3xl font-bold">
        Arus Berita
      </h2>
      <Segmented
        id="feed-region"
        label="Saring asal media"
        value={region}
        onChange={setRegion}
        options={[
          { value: "all", label: "Semua" },
          { value: "domestic", label: REGION_LABEL.domestic },
          { value: "foreign", label: REGION_LABEL.foreign },
        ]}
      />
      {loaded && shown.length === 0 && (
        <p className="text-ink-muted">
          {events.length === 0
            ? "Belum ada berita yang cocok dengan kamus topik. Berita baru akan tampil di sini."
            : "Belum ada berita dari media dengan asal ini."}
        </p>
      )}
      <ul className="flex flex-col gap-2 xl:max-h-[calc(100dvh-16rem)] xl:overflow-y-auto xl:pr-1">
        <AnimatePresence initial={false}>
          {shown.map((e, i) => (
            <motion.li
              // satu artikel bisa menjadi beberapa event (beda kategori), jadi kunci memakai event_type juga
              key={`${e.url ?? e.title}-${e.event_type}-${e.timestamp}`}
              layout
              initial={{ opacity: 0, x: 16 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3, delay: i === 0 ? 0.05 : 0 }}
              className="rounded-xl border border-line bg-white/[0.02] p-3"
            >
              <p className="font-data text-xs text-ink-muted">
                {formatTime(e.timestamp)} · {e.source} · {REGION_LABEL[e.region]}
              </p>
              <p className="mt-1 leading-snug">{e.title}</p>
              <p className="font-data mt-2 flex gap-2 text-xs">
                <span className="rounded-sm bg-surface-2 px-1.5 py-0.5 text-ink-muted">{topicLabel(e.topic)}</span>
                <span className="rounded-sm bg-surface-2 px-1.5 py-0.5 text-ink-muted">{eventLabel(e.event_type)}</span>
              </p>
              <SourceLink url={e.url} />
            </motion.li>
          ))}
        </AnimatePresence>
      </ul>
    </section>
  );
}
