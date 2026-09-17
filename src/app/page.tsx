import Image from "next/image";
import Link from "next/link";
import { Icon } from "@/components/ui/icon";
import { Button } from "@/components/ui/button";
import { CampusFilterGrid } from "@/components/commerce/campus-filter-grid";
import { campuses } from "@/lib/data/campuses";

const specs = [
  {
    tag: "SPEC_01 // CHASSIS",
    title: "88/12 MICRO-POLY",
    body: "High-tenacity filament yarn woven in an orthogonal stretch lattice. Repels campus cold while venting high-intensity cognitive spikes.",
    meta: "RESISTANCE: 10K PORES",
    icon: "memory",
  },
  {
    tag: "SPEC_02 // HERALDRY",
    title: "SYNAPSE CHEVRON",
    body: "The triple-chevron nape badge integrates gold-flux capillary conduits. Visual identification across research nodes and hackathons.",
    meta: "PRINT: 3D REFLECTIVE",
    icon: "share",
  },
  {
    tag: "SPEC_03 // CHECKOUT API",
    title: "MEDUSA V2 ENGINE",
    body: "Sub-second serverless cart mutations and Square Pay. Order verification handled via automated microservice pipelines.",
    meta: "LATENCY: <20MS",
    icon: "terminal",
  },
  {
    tag: "SPEC_04 // NODE LOGISTICS",
    title: "CAMPUS LOCKERS",
    body: "Direct routing to campus student centers and CS lab lockers across the Top 100 CS Initiative footprint.",
    meta: "DISPATCH: AUTOMATED",
    icon: "near_me",
  },
];

export default function Home() {
  return (
    <div className="flex flex-col w-full">
      <section className="w-full bg-surface-3 py-1.5 px-4 lg:px-10">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2 font-body text-spec text-ink-soft">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5 text-ink font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-gold" />
              PROTOCOL: MESH_POD_V4
            </span>
            <span className="hidden md:inline text-line-strong">/</span>
            <span className="hidden md:inline">FABRIC_TEST: ASTM_D3786_BURST_OK</span>
            <span className="hidden lg:inline text-line-strong">/</span>
            <span className="hidden lg:inline">SYNAPSE_INK: METALLIC_REFLECTIVE_GOLD_580NM</span>
          </div>
          <span className="text-gold font-display text-tag-sm font-bold tracking-widest">
            DISPATCH STATUS: NORMAL [0.08MS]
          </span>
        </div>
      </section>

      <section className="w-full bg-surface-0 py-14 px-4 lg:px-10">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          <div className="lg:col-span-7 flex flex-col items-start gap-5">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-surface-1 text-ink font-display text-tag-sm uppercase tracking-widest">
              <span className="w-2 h-2 bg-gold rounded-full animate-ping" />
              <span>CYCLE_04 // RELEASE: AUTONOMOUS ATHLETIC SYSTEMS</span>
            </div>
            <div className="flex flex-col gap-1">
              <h1 className="font-display text-[2.6rem] sm:text-display-xl text-ink font-bold tracking-tight uppercase leading-[0.95]">
                TECHWEAR FOR THE <br />
                <span className="text-gold">BUILDER</span> GENERATION
              </h1>
              <p className="font-display text-tag uppercase tracking-widest text-ink-soft mt-1">
                RESEARCH. AUTOMATE. SIMULATE. // ZERO FRICTION RUNTIME
              </p>
            </div>
            <p className="font-body text-base text-ink-soft max-w-xl">
              Engineered moisture-adaptive poly-spandex quarter-zips, luminous gold neural sleeve
              prints, and precision heraldry for elite computer science collectives. Powered by
              AutoNateAI autonomous manufacturing telemetry.
            </p>
            <div className="flex flex-wrap items-center gap-3 pt-1">
              <Link href="/products/neural-spec-quarter-zip-arctic">
                <Button variant="gold">
                  <span>SHOP CAMPUS DROP</span>
                  <Icon name="arrow_forward" />
                </Button>
              </Link>
              <Link href="/campus">
                <Button variant="dark">
                  <span>EXPLORE TOP 100 CS NODES</span>
                  <Icon name="hub" />
                </Button>
              </Link>
            </div>
            <div className="w-full grid grid-cols-3 gap-4 pt-4 mt-2 bg-surface-1 p-4">
              <div className="flex flex-col">
                <span className="font-display text-tag-sm uppercase text-ink-soft tracking-wider">
                  CHASSIS DENSITY
                </span>
                <span className="font-display text-xl text-ink font-bold">320 GSM</span>
                <span className="font-body text-spec text-ink-soft">88/12 MicroPoly Matrix</span>
              </div>
              <div className="flex flex-col">
                <span className="font-display text-tag-sm uppercase text-ink-soft tracking-wider">
                  CHECKOUT LATENCY
                </span>
                <span className="font-display text-xl text-gold font-bold">0.02 SEC</span>
                <span className="font-body text-spec text-ink-soft">Medusa v2 API Engine</span>
              </div>
              <div className="flex flex-col">
                <span className="font-display text-tag-sm uppercase text-ink-soft tracking-wider">
                  CAMPUS DISPATCH
                </span>
                <span className="font-display text-xl text-ink font-bold">100% POD</span>
                <span className="font-body text-spec text-ink-soft">Mesh Local Fulfillment</span>
              </div>
            </div>
          </div>

          <div className="lg:col-span-5 relative">
            <div className="relative w-full aspect-4/5 bg-ink overflow-hidden shadow-xl">
              <div
                className="absolute inset-0 opacity-[0.1] invert"
                style={{
                  backgroundImage:
                    "repeating-linear-gradient(135deg, currentColor 0px, currentColor 1px, transparent 1px, transparent 16px)",
                }}
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="relative w-1/2 aspect-square">
                  <Image src="/brand/logo.png" alt="Bot That Lyfe chevron mark" fill className="object-contain" />
                </div>
              </div>
              <div className="absolute top-3 left-3 right-3 flex items-center justify-between pointer-events-none">
                <span className="bg-ink-deep/90 backdrop-blur text-surface font-body text-spec px-2 py-0.5 tracking-widest uppercase">
                  SYS: DUAL_FABRIC_POLY_4WAY
                </span>
                <span className="bg-gold/90 backdrop-blur text-ink font-display text-tag-sm font-bold px-2 py-0.5 tracking-wider uppercase">
                  BUILD VERIFIED
                </span>
              </div>
              <div className="absolute bottom-3 left-3 bg-ink-deep/95 text-surface p-2.5 font-body text-spec pointer-events-none">
                <div className="text-gold font-bold">HIGHER THINKING IN PROGRESS.</div>
                <div className="text-surface-3 text-[10px]">
                  COORDINATES: 42.28° N, 83.74° W [UMICH]
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <CampusFilterGrid />

      <section className="w-full bg-surface-1 py-14 px-4 lg:px-10">
        <div className="max-w-7xl mx-auto flex flex-col gap-8">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <span className="font-display text-tag-sm uppercase tracking-widest text-gold font-bold">
                FABRICATION MATRIX
              </span>
              <h2 className="font-display text-3xl text-ink font-bold uppercase">
                Architectural Apparel Telemetry
              </h2>
            </div>
            <div className="hidden sm:flex items-center gap-2 bg-surface-2 px-3 py-1.5 font-body text-spec">
              <span className="w-2 h-2 rounded-full bg-gold" />
              <span>SYSTEM BENCHMARK: PASS</span>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {specs.map((spec) => (
              <div key={spec.title} className="bg-surface-0 p-5 flex flex-col justify-between gap-4 shadow-sm">
                <div className="flex flex-col gap-1.5">
                  <span className="font-body text-spec text-gold font-bold">{spec.tag}</span>
                  <h4 className="font-display text-xl text-ink uppercase font-bold">{spec.title}</h4>
                  <p className="font-body text-sm text-ink-soft">{spec.body}</p>
                </div>
                <div className="pt-2 flex items-center justify-between font-display text-tag-sm text-ink">
                  <span>{spec.meta}</span>
                  <Icon name={spec.icon} className="text-gold text-xl" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="w-full bg-surface py-14 px-4 lg:px-10">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          <div className="lg:col-span-5 flex flex-col gap-4">
            <span className="font-display text-tag-sm uppercase tracking-widest text-gold font-bold">
              DISTRIBUTED CAMPUS FABRICATION
            </span>
            <h2 className="font-display text-3xl text-ink font-bold uppercase">
              Physical Nodes On Top 100 CS Campuses
            </h2>
            <p className="font-body text-sm text-ink-soft">
              We don&apos;t use slow overseas supply chains. Bot That Lyfe utilizes autonomous
              micro-fulfillment nodes positioned within 5 miles of premier engineering
              institutions.
            </p>
            <div className="flex flex-col gap-1.5 pt-1">
              {campuses.slice(0, 3).map((c) => (
                <div
                  key={c.slug}
                  className="flex items-center justify-between p-2.5 bg-surface-0 shadow-sm"
                >
                  <div className="flex items-center gap-2.5">
                    <span className="w-2 h-2 rounded-full bg-gold" />
                    <span className="font-body text-spec font-bold text-ink">
                      [NODE_{c.index}] {c.shortName}
                    </span>
                  </div>
                  <span className="font-body text-spec text-ink-soft">EST: {c.dispatch}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="lg:col-span-7">
            <div className="relative w-full h-80 bg-surface-3 overflow-hidden shadow-md">
              <div
                className="absolute inset-0 opacity-20"
                style={{
                  backgroundImage:
                    "repeating-linear-gradient(90deg, #0b1325 0px, #0b1325 1px, transparent 1px, transparent 40px), repeating-linear-gradient(0deg, #0b1325 0px, #0b1325 1px, transparent 1px, transparent 40px)",
                }}
              />
              <div className="absolute bottom-4 left-4 right-4 bg-surface-0/95 backdrop-blur p-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Icon name="location_on" className="text-gold" />
                  <span className="font-display text-tag-sm text-ink font-bold uppercase">
                    PRIMARY LATENCY HUB: ANN ARBOR // 42.28°N
                  </span>
                </div>
                <span className="font-body text-spec text-gold font-bold">STATUS: 100% ONLINE</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="w-full bg-ink-deep text-surface py-14 px-4 lg:px-10">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-8 p-8 bg-ink shadow-2xl">
          <div className="flex flex-col gap-4 max-w-2xl">
            <div className="flex items-center gap-2 text-gold font-display text-tag-sm uppercase tracking-widest font-bold">
              <span className="w-2 h-2 rounded-full bg-gold" />
              <span>AUTONATEAI CORE TENET</span>
            </div>
            <h2 className="font-display text-display-lg font-bold uppercase tracking-tight text-surface-0 leading-none">
              HIGHER THINKING <br />IN PROGRESS.
            </h2>
            <p className="font-body text-base text-surface-3">
              Code less. Orchestrate more. Our technical apparel is tailored with the exact
              balance of thermoregulation, kinetic recovery, and heraldic symbolism demanded by
              people building planetary-scale intelligent systems.
            </p>
            <div className="flex flex-wrap items-center gap-3 font-body text-spec text-surface-3 pt-1">
              <span>COMPILED FOR: AI RESEARCHERS</span>
              <span>·</span>
              <span>SYSTEM ARCHITECTS</span>
              <span>·</span>
              <span>FOUNDERS</span>
            </div>
          </div>
          <div className="flex flex-col items-center justify-center gap-3 p-6 bg-surface-0/5">
            <div className="relative w-24 h-24">
              <Image src="/brand/logo.png" alt="Synapse chevron mark" fill className="object-contain" />
            </div>
            <Button variant="gold">JOIN CAMPUS DISCORD</Button>
            <span className="font-body text-spec text-surface-3">12,480 ACTIVE CS STUDENTS</span>
          </div>
        </div>
      </section>
    </div>
  );
}
