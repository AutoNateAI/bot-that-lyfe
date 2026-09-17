import Link from "next/link";
import { campuses } from "@/lib/data/campuses";

export function Footer() {
  return (
    <footer className="w-full bg-surface-0 border-t border-surface-3">
      <div className="max-w-7xl mx-auto px-4 lg:px-10 py-14">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8 pb-10">
          <div className="lg:col-span-2 flex flex-col gap-4">
            <div className="flex flex-col">
              <span className="font-display text-lg font-bold tracking-tight text-ink uppercase">
                Bot That Lyfe<span className="text-gold text-xs align-super">™</span>
              </span>
              <span className="font-display text-tag-sm tracking-widest text-ink-soft uppercase">
                Techwear for high-throughput minds
              </span>
            </div>
            <p className="font-body text-sm text-ink-soft max-w-md">
              Engineered apparel for AI researchers, distributed systems architects, and
              competitive algorithmic developers. Precision thermoregulation, zero-chaffing
              builds, campus mesh nodes.
            </p>
            <div className="flex flex-wrap items-center gap-2 pt-1">
              {["MEDUSA V2 CORE", "SQUARE PAY ENCRYPTED", "NODE: US-EAST-01"].map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-0.5 bg-surface-1 font-display text-tag-sm uppercase tracking-wider text-ink"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-3">
            <span className="font-display text-tag-sm uppercase tracking-widest font-bold text-ink">
              Campus Nodes
            </span>
            <ul className="flex flex-col gap-2 font-display text-tag text-ink-soft">
              {campuses.map((c) => (
                <li key={c.slug}>
                  <Link href="/campus" className="hover:text-ink transition-colors">
                    [{c.index}] {c.shortName}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div className="flex flex-col gap-3">
            <span className="font-display text-tag-sm uppercase tracking-widest font-bold text-ink">
              Technical Specs
            </span>
            <ul className="flex flex-col gap-2 font-display text-tag text-ink-soft">
              <li>420GSM Poly-Spandex Matrix</li>
              <li>YKK Semi-Auto Aquaguard Zips</li>
              <li>Thermal Dispersion Mapping</li>
              <li>Care Protocol & Cold Deployments</li>
            </ul>
          </div>

          <div className="flex flex-col gap-3">
            <span className="font-display text-tag-sm uppercase tracking-widest font-bold text-ink">
              Operations
            </span>
            <ul className="flex flex-col gap-2 font-display text-tag text-ink-soft">
              <li>Campus Ambassador Fellowship</li>
              <li>Print-on-Demand Telemetry</li>
              <li>Returns & Defect SLA</li>
              <li className="text-gold font-bold">System Health: 99.98%</li>
            </ul>
          </div>
        </div>

        <div className="pt-6 border-t border-surface-3 flex flex-col md:flex-row items-center justify-between gap-3 font-display text-tag-sm tracking-wider uppercase text-ink-soft">
          <span>© 2026 Bot That Lyfe™ // Powered by AutoNateAI</span>
          <div className="flex items-center gap-4">
            <span>Headless Commerce // Secure SHA-256</span>
            <span className="text-gold font-bold">Campus Dispatch Active</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
