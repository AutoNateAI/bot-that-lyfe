"use client";

import { useState } from "react";
import Link from "next/link";
import type { Product } from "@/lib/types";
import { ProductArt } from "@/components/commerce/product-art";
import { Icon } from "@/components/ui/icon";
import { Accordion } from "@/components/ui/accordion";
import { useCart } from "@/lib/cart-context";

const thumbnails = [
  "PRIMARY DROP TRIO",
  "NEURAL CHEVRONS MACRO",
  "STUDIO SLEEVE TYPOGRAPHY",
  "FABRIC WEAVE & ZIP DETAIL",
];

export function ProductDetail({ product }: { product: Product }) {
  const [size, setSize] = useState(product.sizes[Math.floor(product.sizes.length / 2)]);
  const [qty, setQty] = useState(1);
  const [stamp, setStamp] = useState("");
  const [added, setAdded] = useState(false);
  const { addLine } = useCart();

  const handleAdd = () => {
    addLine(product.slug, size, qty);
    setAdded(true);
    setTimeout(() => setAdded(false), 2000);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 lg:px-10 py-8 w-full">
      <div className="flex items-center gap-2 font-body text-spec text-ink-soft uppercase mb-6">
        <Link href="/" className="hover:text-ink">Storefront</Link>
        <span>/</span>
        <span className="text-ink">{product.sku}</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
        {/* Gallery */}
        <div className="lg:col-span-7 flex flex-col gap-3">
          <div className="relative w-full aspect-4/5 shadow-md">
            <ProductArt product={product} className="absolute inset-0" />
            <div className="absolute top-3 left-3 bg-ink-deep/90 text-surface font-body text-spec px-2 py-0.5 uppercase tracking-widest">
              SKU: {product.sku}
            </div>
            <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between bg-surface-0/90 backdrop-blur px-3 py-2 font-body text-spec text-ink">
              <span>{product.fabricSpec}</span>
              <span className="text-gold font-bold">GEN-4</span>
            </div>
          </div>
          <div className="grid grid-cols-4 gap-3">
            {thumbnails.map((t, i) => (
              <div
                key={t}
                className={`relative aspect-square bg-surface-1 flex items-center justify-center p-2 border ${
                  i === 0 ? "border-ink" : "border-surface-3"
                }`}
              >
                <span className="font-body text-[9px] text-center text-ink-soft uppercase leading-tight">
                  {t}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Configuration pane */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="font-display text-tag-sm uppercase tracking-widest text-gold font-bold">
                {product.category}
              </span>
              {product.badge && (
                <span className="bg-gold text-ink font-display text-tag-sm font-bold px-2 py-0.5 uppercase tracking-wider">
                  {product.badge}
                </span>
              )}
            </div>
            <h1 className="font-display text-3xl text-ink font-bold uppercase tracking-tight">
              {product.name}
            </h1>
            <p className="font-body text-sm text-ink-soft mt-2">{product.description}</p>
            <div className="font-display text-2xl text-ink font-bold mt-3">
              ${product.price.toFixed(2)}
            </div>
          </div>

          <div className="bg-surface-1 p-4 flex flex-col gap-4">
            <div>
              <span className="font-display text-tag-sm uppercase tracking-widest text-ink-soft">
                Colorway
              </span>
              <div className="mt-2 flex items-center gap-2">
                <span className="px-3 py-1.5 bg-ink text-surface-0 font-display text-tag-sm uppercase tracking-wide">
                  {product.colorway}
                </span>
              </div>
            </div>

            <div>
              <span className="font-display text-tag-sm uppercase tracking-widest text-ink-soft">
                Calibrated Size
              </span>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                {product.sizes.map((s) => (
                  <button
                    key={s}
                    onClick={() => setSize(s)}
                    className={`w-11 h-11 font-body text-sm transition-colors ${
                      size === s
                        ? "bg-ink text-surface-0 font-bold"
                        : "bg-surface-0 text-ink hover:bg-ink hover:text-surface-0"
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <span className="font-display text-tag-sm uppercase tracking-widest text-ink-soft">
                Campus Coordinate Wrist Stamp (optional)
              </span>
              <input
                value={stamp}
                onChange={(e) => setStamp(e.target.value.toUpperCase().slice(0, 24))}
                placeholder="E.G. UMICH // 42.28°N"
                className="mt-2 w-full bg-surface-0 border border-ink px-3 py-2.5 font-display text-tag-sm uppercase tracking-wide placeholder:text-ink-soft/60 outline-none focus:border-gold"
              />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center border border-ink">
              <button
                onClick={() => setQty((q) => Math.max(1, q - 1))}
                className="w-10 h-11 flex items-center justify-center hover:bg-surface-1"
              >
                −
              </button>
              <span className="w-10 text-center font-display text-tag font-bold">{qty}</span>
              <button
                onClick={() => setQty((q) => q + 1)}
                className="w-10 h-11 flex items-center justify-center hover:bg-surface-1"
              >
                +
              </button>
            </div>
            <button
              onClick={handleAdd}
              className="flex-1 bg-gold hover:bg-gold-bright text-ink font-display text-tag font-bold uppercase tracking-wider py-3.5 flex items-center justify-center gap-2 transition-all offset-press active:translate-y-0.5"
            >
              <Icon name="bolt" />
              <span>{added ? "ADDED TO CART" : "DEPLOY TO CART"}</span>
            </button>
          </div>
          <button className="w-full border border-ink text-ink font-display text-tag font-bold uppercase tracking-wider py-3.5 flex items-center justify-center gap-2 hover:bg-ink hover:text-surface-0 transition-colors">
            <Icon name="bolt" />
            <span>SQUARE PAY — INSTANT CHECKOUT</span>
          </button>

          <div className="flex items-center justify-between font-body text-spec text-ink-soft bg-surface-1 px-3 py-2.5">
            <span>SLA DISPATCH: 24H FROM NEAREST NODE</span>
            <span className="text-gold font-bold">ENCRYPTED // SHA-256</span>
          </div>

          <Accordion
            items={[
              {
                title: "Component Breakdown",
                body: `${product.fabricSpec}. Gold neural print heat-bonded at 400°F, YKK reverse-coil hardware where applicable.`,
              },
              {
                title: "Medusa Headless Architecture & API Workflow",
                body: "Cart mutations run through the Medusa v2 commerce engine; checkout settles via Square, and fulfillment dispatches to the nearest campus print-on-demand node automatically.",
              },
              {
                title: "Fabric Care & Maintenance Guide",
                body: "Cold machine wash, inside out. No bleach. Tumble dry low or hang dry to preserve the neural print's reflective finish.",
              },
              {
                title: "Dimensional Sizing Matrix",
                body: "Runs true to size for a modern athletic fit. Sizing chart with chest/length measurements ships with every order confirmation.",
              },
            ]}
          />
        </div>
      </div>

      {/* Bento spec showcase */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16">
        <div className="md:col-span-2 bg-ink text-surface p-6 flex flex-col justify-end gap-2 aspect-video md:aspect-auto">
          <span className="font-body text-spec text-gold-soft">CHEVRON MICRO-CIRCUITRY</span>
          <p className="font-body text-sm text-surface-3 max-w-md">
            The nape badge&apos;s gold-flux conduits are printed in three passes for depth,
            reading as a physical circuit under direct light.
          </p>
        </div>
        <div className="bg-surface-1 p-6 flex flex-col justify-end gap-2 aspect-square md:aspect-auto">
          <span className="font-body text-spec text-gold font-bold">SLEEVE MANTRA MATRIX</span>
          <p className="font-body text-sm text-ink-soft">
            &quot;Research. Automate. Simulate.&quot; runs the left forearm in reflective ink.
          </p>
        </div>
        <div className="bg-surface-1 p-6 flex flex-col justify-end gap-2">
          <span className="font-body text-spec text-gold font-bold">MESH FLOW & ZERO CHAFING</span>
          <p className="font-body text-sm text-ink-soft">
            Underarm gusset venting and flatlock seams built for long lab sessions.
          </p>
        </div>
        <div className="md:col-span-2 bg-surface-1 p-6 flex flex-col justify-end gap-2">
          <span className="font-body text-spec text-gold font-bold">BUILD VERIFICATION</span>
          <p className="font-body text-sm text-ink-soft">
            Every unit passes ASTM D3786 burst testing before it ships to a campus node.
          </p>
        </div>
      </div>
    </div>
  );
}
