"use client";

import { motion } from "motion/react";

type Props<T extends string> = {
  id: string; // layoutId unik per kontrol, supaya indikator tidak melompat antar kontrol
  label: string;
  options: { value: T; label: string }[];
  value: T;
  onChange: (v: T) => void;
};

export function Segmented<T extends string>({ id, label, options, value, onChange }: Props<T>) {
  return (
    <div role="group" aria-label={label} className="flex rounded-md border border-line bg-surface p-1">
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          aria-pressed={value === o.value}
          onClick={() => onChange(o.value)}
          className={`font-data relative min-h-11 flex-1 whitespace-nowrap rounded px-3 text-xs transition-colors ${
            value === o.value ? "text-ink" : "text-ink-muted hover:text-ink"
          }`}
        >
          {value === o.value && (
            <motion.span
              layoutId={id}
              // hanya animasikan saat pilihan berganti, bukan saat halaman bergeser karena alert baru
              layoutDependency={value}
              className="absolute inset-0 rounded bg-siber"
              transition={{ type: "spring", stiffness: 500, damping: 40 }}
            />
          )}
          <span className="relative">{o.label}</span>
        </button>
      ))}
    </div>
  );
}
