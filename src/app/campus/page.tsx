"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { campuses } from "@/lib/data/campuses";
import { Icon } from "@/components/ui/icon";

const totalStudents = campuses.reduce((sum, c) => sum + c.students, 0);
const avgInventory = Math.round(
  campuses.reduce((sum, c) => sum + c.inventoryPct, 0) / campuses.length
);

const pillars = [
  {
    icon: "bolt",
    title: "Autonomous Dispatch",
    body: "Orders route to the nearest campus print-on-demand node the moment checkout confirms.",
  },
  {
    icon: "groups",
    title: "Ambassador Fellowship",
    body: "Each node is anchored by an ACM/AI-club lead who runs local drops and Discord onboarding.",
  },
  {
    icon: "verified",
    title: "Build Verification",
    body: "Every unit clears ASTM burst testing and a manual QA pass before it ships from its node.",
  },
];

export default function CampusDirectoryPage() {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return campuses;
    return campuses.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        c.shortName.toLowerCase().includes(q) ||
        c.city.toLowerCase().includes(q)
    );
  }, [query]);

  return (
    <div className="w-full">
      <section className="w-full bg-ink-deep text-surface py-14 px-4 lg:px-10">
        <div className="max-w-7xl mx-auto flex flex-col gap-6">
          <div className="flex items-center gap-2 font-body text-spec text-gold-soft uppercase">
            <span className="w-2 h-2 rounded-full bg-gold animate-pulse" />
            <span>TOP 100 CS INITIATIVE // NODE TELEMETRY LIVE</span>
          </div>
          <h1 className="font-display text-display-lg font-bold uppercase tracking-tight text-surface-0">
            Campus Node Directory
          </h1>
          <p className="font-body text-base text-surface-3 max-w-2xl">
            Six live fulfillment nodes anchored inside Top 100 CS programs, expanding toward full
            coverage across the initiative.
          </p>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-2">
            {[
              { label: "ACTIVE NODES", value: campuses.length.toString() },
              { label: "STUDENTS REACHED", value: `${(totalStudents / 1000).toFixed(1)}K` },
              { label: "AVG INVENTORY", value: `${avgInventory}%` },
              { label: "DISPATCH SLA", value: "≤24H" },
            ].map((m) => (
              <div key={m.label} className="bg-surface-0/5 p-4 border border-surface-0/10">
                <div className="font-display text-2xl font-bold text-gold">{m.value}</div>
                <div className="font-display text-tag-sm uppercase tracking-widest text-surface-3">
                  {m.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="w-full bg-surface-0 border-b border-surface-3 py-4 px-4 lg:px-10">
        <div className="max-w-7xl mx-auto flex items-center gap-3">
          <Icon name="search" className="text-ink-soft" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="SEARCH NODES BY SCHOOL OR CITY..."
            className="flex-1 bg-transparent font-display text-tag uppercase tracking-wide placeholder:text-ink-soft/60 outline-none"
          />
          <span className="font-body text-spec text-ink-soft hidden sm:inline">
            {filtered.length} / {campuses.length} NODES
          </span>
        </div>
      </section>

      <section className="w-full bg-surface py-14 px-4 lg:px-10">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.map((c) => (
            <div key={c.slug} className="bg-surface-0 border border-surface-3 hover:border-ink transition-colors flex flex-col">
              <div className="flex items-center justify-between px-4 py-2 bg-ink-deep text-surface">
                <span className="font-body text-spec uppercase tracking-widest">NODE_{c.index}</span>
                <span className="font-body text-spec text-gold-soft">{c.dispatch}</span>
              </div>
              <div className="relative aspect-video bg-surface-2">
                <div
                  className="absolute inset-0 opacity-25"
                  style={{
                    backgroundImage:
                      "repeating-linear-gradient(90deg, #0b1325 0px, #0b1325 1px, transparent 1px, transparent 24px), repeating-linear-gradient(0deg, #0b1325 0px, #0b1325 1px, transparent 1px, transparent 24px)",
                  }}
                />
                <div className="absolute bottom-2 left-2 font-body text-spec text-ink bg-surface-0/90 px-2 py-0.5">
                  {c.coordinates}
                </div>
              </div>
              <div className="p-4 flex flex-col gap-3 flex-1">
                <div>
                  <h3 className="font-display text-lg text-ink font-bold uppercase tracking-tight">
                    {c.name}
                  </h3>
                  <p className="font-body text-spec text-ink-soft">{`${c.shortName} // ${c.city}`}</p>
                </div>
                <div className="flex flex-col gap-1.5 font-body text-sm text-ink-soft">
                  <div className="flex items-center justify-between">
                    <span>Ambassador Chapter</span>
                    <span className="text-ink font-medium">{c.ambassador}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Reachable Students</span>
                    <span className="text-ink font-medium">{c.students.toLocaleString()}</span>
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between font-display text-tag-sm uppercase tracking-wide mb-1">
                    <span className="text-ink-soft">Inventory</span>
                    <span className="text-gold font-bold">{c.inventoryPct}%</span>
                  </div>
                  <div className="h-1.5 bg-surface-3 w-full">
                    <div className="h-full bg-gold" style={{ width: `${c.inventoryPct}%` }} />
                  </div>
                </div>
                <Link
                  href="/"
                  className="mt-auto w-full text-center bg-surface-2 hover:bg-ink hover:text-surface-0 text-ink font-display text-tag-sm font-bold uppercase tracking-wider py-2.5 transition-colors"
                >
                  Shop This Node
                </Link>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="w-full bg-ink text-surface py-14 px-4 lg:px-10">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="max-w-xl">
            <span className="font-display text-tag-sm uppercase tracking-widest text-gold font-bold">
              Chapter Lead & ACM Ambassador Program
            </span>
            <h2 className="font-display text-2xl font-bold uppercase mt-2 text-surface-0">
              Run the Drop On Your Campus
            </h2>
            <p className="font-body text-sm text-surface-3 mt-2">
              Ambassadors get early access to drops, a revenue share on local sales, and a direct
              line into AutoNateAI&apos;s research releases.
            </p>
          </div>
          <button className="bg-gold hover:bg-gold-bright text-ink font-display text-tag font-bold uppercase tracking-wider px-6 py-3.5 shrink-0">
            Apply For Your Node
          </button>
        </div>
      </section>

      <section className="w-full bg-surface-1 py-14 px-4 lg:px-10">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
          {pillars.map((p) => (
            <div key={p.title} className="bg-surface-0 p-6 flex flex-col gap-3">
              <Icon name={p.icon} className="text-gold text-3xl" />
              <h3 className="font-display text-lg text-ink font-bold uppercase">{p.title}</h3>
              <p className="font-body text-sm text-ink-soft">{p.body}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
