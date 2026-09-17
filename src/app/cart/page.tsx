"use client";

import { useState } from "react";
import Link from "next/link";
import { useCart } from "@/lib/cart-context";
import { getProductBySlug } from "@/lib/data/products";
import { ProductArt } from "@/components/commerce/product-art";
import { Icon } from "@/components/ui/icon";

const FREE_SHIPPING_THRESHOLD = 100;

const upsells = [
  { name: "31.5\" XL Neural Desk Mat", price: 34, spec: "MICROFIBER // STITCHED EDGE" },
  { name: "Automated Homework Sticker 8-Pack", price: 12, spec: "MATTE VINYL // WEATHERPROOF" },
];

export default function CartPage() {
  const { lines, updateQuantity, removeLine, subtotal } = useCart();
  const [promo, setPromo] = useState("");

  const progress = Math.min(100, (subtotal / FREE_SHIPPING_THRESHOLD) * 100);
  const shipping = subtotal >= FREE_SHIPPING_THRESHOLD || subtotal === 0 ? 0 : 8;
  const tax = subtotal * 0.06;
  const total = subtotal + shipping + tax;

  return (
    <div className="max-w-7xl mx-auto px-4 lg:px-10 py-10 w-full">
      <div className="font-body text-spec text-ink-soft uppercase mb-4">
        <Link href="/" className="hover:text-ink">Storefront</Link> / Cart & Checkout
      </div>
      <h1 className="font-display text-3xl text-ink font-bold uppercase tracking-tight mb-8">
        Manifest & Ledger
      </h1>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
        <div className="lg:col-span-7 flex flex-col gap-6">
          <div className="bg-surface-1 p-4">
            <div className="flex items-center justify-between font-display text-tag-sm uppercase tracking-wide mb-2">
              <span className="text-ink font-semibold">Campus Free Shipping</span>
              <span className="text-gold font-bold">
                {shipping === 0 ? "UNLOCKED" : `$${(FREE_SHIPPING_THRESHOLD - subtotal).toFixed(2)} TO GO`}
              </span>
            </div>
            <div className="h-1.5 bg-surface-3 w-full">
              <div
                className="h-full bg-gradient-to-r from-gold to-gold-bright transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {lines.length === 0 ? (
            <div className="bg-surface-0 border border-surface-3 p-10 text-center">
              <p className="font-body text-ink-soft mb-4">Cart manifest is empty.</p>
              <Link href="/" className="font-display text-tag uppercase tracking-wider text-gold font-bold">
                Browse the Drop →
              </Link>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              {lines.map((line) => {
                const product = getProductBySlug(line.slug);
                if (!product) return null;
                return (
                  <div key={`${line.slug}-${line.size}`} className="flex gap-4 bg-surface-0 border border-surface-3 p-4">
                    <div className="relative w-24 h-24 shrink-0">
                      <ProductArt product={product} className="absolute inset-0" />
                    </div>
                    <div className="flex-1 flex flex-col justify-between min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <Link href={`/products/${product.slug}`}>
                            <h3 className="font-display text-base text-ink uppercase font-bold tracking-tight truncate hover:text-gold">
                              {product.name}
                            </h3>
                          </Link>
                          <p className="font-body text-spec text-ink-soft">
                            {`SIZE: ${line.size} // SKU: ${product.sku}`}
                          </p>
                        </div>
                        <span className="font-display text-base font-bold text-ink shrink-0">
                          ${(product.price * line.quantity).toFixed(2)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between mt-2">
                        <div className="flex items-center border border-ink">
                          <button
                            onClick={() => updateQuantity(line.slug, line.size, line.quantity - 1)}
                            className="w-8 h-8 flex items-center justify-center hover:bg-surface-1"
                          >
                            −
                          </button>
                          <span className="w-8 text-center font-body text-sm">{line.quantity}</span>
                          <button
                            onClick={() => updateQuantity(line.slug, line.size, line.quantity + 1)}
                            className="w-8 h-8 flex items-center justify-center hover:bg-surface-1"
                          >
                            +
                          </button>
                        </div>
                        <button
                          onClick={() => removeLine(line.slug, line.size)}
                          className="font-display text-tag-sm uppercase text-ink-soft hover:text-danger transition-colors"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          <div className="pt-4">
            <span className="font-display text-tag-sm uppercase tracking-widest text-gold font-bold">
              Paired For The Lab
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-3">
              {upsells.map((item) => (
                <div key={item.name} className="flex items-center gap-3 bg-surface-1 p-3">
                  <div className="w-16 h-16 bg-surface-3 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="font-display text-tag text-ink font-semibold uppercase leading-snug">
                      {item.name}
                    </p>
                    <p className="font-body text-spec text-ink-soft">{item.spec}</p>
                    <p className="font-display text-tag-sm text-gold font-bold mt-1">
                      +${item.price.toFixed(2)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="lg:col-span-5">
          <div className="border border-ink p-5 sticky top-28 flex flex-col gap-4">
            <span className="font-display text-tag-sm uppercase tracking-widest text-ink-soft border-b border-surface-3 pb-3">
              Ledger Breakdown
            </span>
            <div className="flex flex-col gap-2 font-body text-sm text-ink-soft">
              <div className="flex items-center justify-between">
                <span>Subtotal</span>
                <span className="text-ink">${subtotal.toFixed(2)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Dispatch / Shipping</span>
                <span className="text-ink">{shipping === 0 ? "FREE" : `$${shipping.toFixed(2)}`}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Est. Tax</span>
                <span className="text-ink">${tax.toFixed(2)}</span>
              </div>
            </div>
            <div className="flex items-center justify-between border-t border-surface-3 pt-3">
              <span className="font-display text-tag uppercase font-bold text-ink">Grand Total</span>
              <span className="font-display text-2xl font-bold text-ink">${total.toFixed(2)}</span>
            </div>

            <div className="flex gap-2">
              <input
                value={promo}
                onChange={(e) => setPromo(e.target.value.toUpperCase())}
                placeholder="PROMO CODE"
                className="flex-1 bg-surface-1 border border-surface-4 px-3 py-2 font-display text-tag-sm uppercase tracking-wide outline-none focus:border-gold"
              />
              <button className="px-4 font-display text-tag-sm uppercase tracking-wide border border-ink hover:bg-ink hover:text-surface-0 transition-colors">
                Apply
              </button>
            </div>

            <button
              disabled={lines.length === 0}
              className="w-full bg-gold hover:bg-gold-bright disabled:opacity-40 disabled:cursor-not-allowed text-ink font-display text-tag font-bold uppercase tracking-wider py-3.5 flex items-center justify-center gap-2 transition-all"
            >
              <Icon name="bolt" />
              <span>CHECKOUT WITH SQUARE PAY</span>
            </button>
            <button
              disabled={lines.length === 0}
              className="w-full border border-ink text-ink disabled:opacity-40 disabled:cursor-not-allowed font-display text-tag font-bold uppercase tracking-wider py-3.5 hover:bg-ink hover:text-surface-0 transition-colors"
            >
              STANDARD MEDUSA CHECKOUT
            </button>

            <div className="flex items-center gap-2 font-body text-spec text-ink-soft justify-center pt-1">
              <Icon name="verified" className="text-gold text-base" />
              <span>CAMPUS NODE GUARANTEE // 30-DAY DEFECT SLA</span>
            </div>
            <div className="bg-surface-1 px-3 py-2 text-center font-body text-spec text-ink-soft">
              SECURE_PAYMENT // VERIFIED BY AUTONATE_AI
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
