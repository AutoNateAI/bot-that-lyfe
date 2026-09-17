"use client";

import { useState } from "react";
import { Icon } from "@/components/ui/icon";

export function Accordion({
  items,
}: {
  items: { title: string; body: React.ReactNode }[];
}) {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <div className="flex flex-col border border-surface-4 divide-y divide-surface-4">
      {items.map((item, i) => (
        <div key={item.title}>
          <button
            onClick={() => setOpen(open === i ? null : i)}
            className="w-full flex items-center justify-between px-4 py-3.5 text-left"
          >
            <span className="font-display text-tag uppercase tracking-wider text-ink font-semibold">
              {item.title}
            </span>
            <Icon
              name={open === i ? "remove" : "add"}
              className="text-ink-soft text-lg"
            />
          </button>
          {open === i && (
            <div className="px-4 pb-4 font-body text-sm text-ink-soft">{item.body}</div>
          )}
        </div>
      ))}
    </div>
  );
}
