import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "gold" | "ghost" | "dark";

const variants: Record<Variant, string> = {
  primary:
    "bg-ink text-surface-0 hover:offset-shadow-gold hover:-translate-x-0.5 hover:-translate-y-0.5",
  gold:
    "bg-gold text-ink hover:bg-gold-bright",
  ghost:
    "bg-transparent text-ink border border-ink hover:bg-ink hover:text-surface-0",
  dark:
    "bg-ink-deep text-surface-0 hover:bg-ink",
};

export function Button({
  variant = "primary",
  className = "",
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 px-6 py-3 font-display text-tag font-bold uppercase tracking-wider transition-all offset-press active:translate-x-0.5 active:translate-y-0.5 ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
