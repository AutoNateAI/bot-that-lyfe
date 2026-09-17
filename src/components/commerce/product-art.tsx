import Image from "next/image";
import type { Product } from "@/lib/types";

/**
 * Placeholder garment art — real product photography lands here once shot
 * (Fourthwall/Printful POD assets). Keeps the grid honest instead of
 * hotlinking third-party render URLs.
 */
export function ProductArt({
  product,
  className = "",
}: {
  product: Pick<Product, "tone" | "colorway" | "name">;
  className?: string;
}) {
  const dark = product.tone === "dark";
  return (
    <div
      className={`relative flex items-center justify-center overflow-hidden ${
        dark ? "bg-ink" : "bg-surface-1"
      } ${className}`}
    >
      <div
        className={`absolute inset-0 opacity-[0.08] ${dark ? "invert" : ""}`}
        style={{
          backgroundImage:
            "repeating-linear-gradient(135deg, currentColor 0px, currentColor 1px, transparent 1px, transparent 14px)",
          color: dark ? "#ffffff" : "#0b1325",
        }}
      />
      <div className="relative w-2/5 aspect-square opacity-90">
        <Image
          src="/brand/logo.png"
          alt=""
          fill
          className="object-contain"
          sizes="240px"
        />
      </div>
    </div>
  );
}
