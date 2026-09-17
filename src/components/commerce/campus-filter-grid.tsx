"use client";

import { useMemo, useState } from "react";
import { products } from "@/lib/data/products";
import { campuses } from "@/lib/data/campuses";
import { ProductCard } from "@/components/commerce/product-card";

export function CampusFilterGrid() {
  const [active, setActive] = useState<string>("all");

  const filtered = useMemo(
    () =>
      active === "all"
        ? products
        : products.filter((p) => p.campus === active || p.campus === "all"),
    [active]
  );

  const tabs = [
    { slug: "all", index: "00", label: "ALL DROPS", coord: `(${products.length})` },
    ...campuses.map((c) => ({
      slug: c.slug,
      index: c.index,
      label: c.shortName.split(" ")[0].toUpperCase(),
      coord: c.coordinates,
    })),
  ];

  return (
    <>
      <section className="sticky top-20 z-40 w-full bg-surface-0/95 backdrop-blur-md border-y border-surface-3">
        <div className="max-w-7xl mx-auto px-4 lg:px-10 py-3 flex flex-col md:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-1.5 overflow-x-auto w-full md:w-auto pb-1 md:pb-0">
            {tabs.map((tab) => (
              <button
                key={tab.slug}
                onClick={() => setActive(tab.slug)}
                className={`px-4 py-2 font-display text-tag-sm uppercase tracking-wider whitespace-nowrap transition-colors ${
                  active === tab.slug
                    ? "bg-ink text-surface-0 font-bold shadow-sm"
                    : "bg-surface-1 hover:bg-surface-2 text-ink"
                }`}
              >
                [{tab.index}] {tab.label} [{tab.coord}]
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <span className="w-2 h-2 rounded-full bg-gold animate-pulse" />
            <span className="font-body text-spec text-ink-soft">STOCK_NODE: LIVE</span>
          </div>
        </div>
      </section>

      <section className="w-full bg-surface py-14 px-4 lg:px-10">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-end justify-between mb-6 flex-wrap gap-2">
            <div>
              <span className="font-display text-tag-sm uppercase tracking-widest text-gold font-bold">
                SPEC SHEET // ACTIVE RELEASES
              </span>
              <h2 className="font-display text-3xl text-ink font-bold uppercase tracking-tight">
                Engineered Harnesses &amp; Drapery
              </h2>
            </div>
            <span className="font-body text-spec text-ink-soft hidden md:inline">
              SYSTEM CAPACITY: {filtered.length} AVAILABLE SPECIFICATIONS
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {filtered.map((product) => (
              <ProductCard key={product.slug} product={product} />
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
