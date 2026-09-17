"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Icon } from "@/components/ui/icon";
import { useCart } from "@/lib/cart-context";

const navLinks = [
  { href: "/", label: "Storefront & Drops" },
  { href: "/products/neural-spec-quarter-zip-arctic", label: "Quarter-Zip Specs" },
  { href: "/campus", label: "Campus Node Directory" },
];

export function Header() {
  const pathname = usePathname();
  const { itemCount, subtotal } = useCart();

  return (
    <header className="sticky top-0 z-50 w-full bg-surface-0/95 backdrop-blur-md shadow-[0_1px_8px_rgba(0,0,0,0.04)]">
      <div className="bg-ink-deep text-surface px-4 lg:px-10 py-1.5">
        <div className="max-w-7xl mx-auto flex items-center justify-between font-display text-tag-sm uppercase tracking-wider gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <span className="flex h-2 w-2 shrink-0 rounded-full bg-gold-bright animate-pulse" />
            <span className="truncate">
              TOP 100 CS INITIATIVE // ZERO LATENCY FULFILLMENT // FREE CAMPUS SHIPPING $100+
            </span>
          </div>
          <span className="hidden sm:inline shrink-0 text-gold-soft">POWERED BY AUTONATEAI</span>
        </div>
      </div>

      <div className="h-20 max-w-7xl mx-auto px-4 lg:px-10 flex items-center justify-between gap-6">
        <Link href="/" className="flex items-center gap-3 group shrink-0">
          <div className="relative w-9 h-9 shrink-0">
            <Image src="/brand/logo.png" alt="Bot That Lyfe" fill className="object-contain" />
          </div>
          <div className="flex flex-col">
            <span className="font-display text-lg font-bold tracking-tight text-ink uppercase leading-none">
              Bot That Lyfe<span className="text-gold text-xs align-super">™</span>
            </span>
            <span className="font-display text-tag-sm tracking-widest text-ink-soft uppercase">
              Research. Automate. Simulate.
            </span>
          </div>
        </Link>

        <nav className="hidden xl:flex items-center gap-6">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`font-display text-tag uppercase tracking-wider transition-colors ${
                pathname === link.href
                  ? "text-ink font-semibold"
                  : "text-ink-soft hover:text-ink"
              }`}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-3 shrink-0">
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-surface-1 text-ink-soft">
            <Icon name="search" className="text-lg" />
            <span className="font-display text-tag-sm uppercase tracking-wide">Search specs...</span>
          </div>
          <div className="hidden lg:flex flex-col px-3 py-1 bg-surface-1">
            <span className="font-display text-tag-sm uppercase tracking-widest text-ink">
              [01] ANN ARBOR
            </span>
            <span className="font-body text-spec text-ink-soft">42.28°N // LAT-0.08MS</span>
          </div>
          <Link
            href="/cart"
            className="flex items-center gap-2 px-3 py-2 bg-surface-2 hover:bg-surface-3 transition-colors text-ink"
          >
            <Icon name="shopping_bag" className="text-lg" />
            <span className="font-display text-tag-sm uppercase tracking-widest font-bold">
              CART [{itemCount}]
            </span>
            <span className="font-display text-tag-sm text-gold font-bold">
              ${subtotal.toFixed(2)}
            </span>
          </Link>
        </div>
      </div>
    </header>
  );
}
