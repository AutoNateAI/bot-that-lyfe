"use client";

import Link from "next/link";
import { useState } from "react";
import type { Product } from "@/lib/types";
import { ProductArt } from "@/components/commerce/product-art";
import { Icon } from "@/components/ui/icon";
import { useCart } from "@/lib/cart-context";

const badgeStyles: Record<string, string> = {
  FLAGSHIP: "bg-gold text-ink",
  POPULAR: "bg-surface-4 text-ink",
  RESTOCKED: "bg-surface-0 text-gold",
  LIMITED: "bg-ink text-gold-soft",
  NEW: "bg-success text-ink",
};

export function ProductCard({ product }: { product: Product }) {
  const [size, setSize] = useState(product.sizes[Math.floor(product.sizes.length / 2)]);
  const { addLine } = useCart();

  return (
    <div className="group flex flex-col bg-surface-0 border border-surface-4 hover:border-ink shadow-sm hover:offset-shadow transition-all duration-150">
      <Link href={`/products/${product.slug}`} className="block">
        <div className="relative w-full aspect-4/5">
          <ProductArt product={product} className="absolute inset-0" />
          <div className="absolute top-2 left-2 bg-ink-deep text-surface font-body text-spec px-2 py-0.5 uppercase tracking-wide">
            SKU: {product.sku}
          </div>
          {product.badge && (
            <div
              className={`absolute top-2 right-2 font-display text-tag-sm font-bold px-2 py-0.5 uppercase tracking-wider ${badgeStyles[product.badge]}`}
            >
              {product.badge}
            </div>
          )}
          <div className="absolute bottom-2 left-2 right-2 bg-surface-0/90 backdrop-blur px-2 py-1 flex items-center justify-between">
            <span className="font-body text-spec text-ink uppercase">{product.fabricSpec}</span>
          </div>
        </div>
      </Link>
      <div className="p-4 flex flex-col flex-grow justify-between gap-4">
        <div>
          <div className="flex items-baseline justify-between mb-1">
            <span className="font-display text-tag-sm text-gold font-bold tracking-widest">
              {product.category}
            </span>
            <span className="font-display text-lg font-bold text-ink">
              ${product.price.toFixed(2)}
            </span>
          </div>
          <Link href={`/products/${product.slug}`}>
            <h3 className="font-display text-lg text-ink uppercase font-bold tracking-tight leading-snug hover:text-gold transition-colors">
              {product.name}
            </h3>
          </Link>
          <p className="font-body text-spec text-ink-soft mt-1">
            {`Color: ${product.colorway} // ${product.description}`}
          </p>
        </div>
        <div className="flex flex-col gap-2 pt-1">
          <div className="flex items-center justify-between">
            <span className="font-display text-tag-sm text-ink-soft">SIZING MATRIX:</span>
            <div className="flex items-center gap-1">
              {product.sizes.map((s) => (
                <button
                  key={s}
                  onClick={() => setSize(s)}
                  className={`w-7 h-7 font-body text-spec transition-colors ${
                    size === s
                      ? "bg-ink text-surface-0 font-bold"
                      : "bg-surface-2 text-ink hover:bg-ink hover:text-surface-0"
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
          <button
            onClick={() => addLine(product.slug, size)}
            className="w-full bg-gold hover:bg-gold-bright text-ink font-display text-tag font-bold uppercase tracking-wider py-2.5 flex items-center justify-center gap-2 transition-all offset-press active:translate-y-0.5"
          >
            <Icon name="bolt" className="text-lg" />
            <span>DEPLOY TO CART</span>
          </button>
        </div>
      </div>
    </div>
  );
}
