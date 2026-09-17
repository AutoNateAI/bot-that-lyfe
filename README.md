# Bot That Lyfe™

Techwear storefront for the Bot That Lyfe brand — Next.js (App Router) + Tailwind v4,
built against the Kinetic Spec design system (`assets/design/stitch-export/kinetic_spec/DESIGN.md`).

Storefront currently runs on mock product/campus data and a client-side cart
(`src/lib/cart-context.tsx`, persisted to `localStorage`). No commerce backend is wired
up yet — Medusa (commerce engine), Square (payments), and a print-on-demand provider are
the planned next layer.

## Getting started

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Structure

- `src/app` — routes: `/` (storefront & drops), `/products/[slug]`, `/cart`, `/campus`
- `src/components` — `layout/` (header, footer), `commerce/` (product card, PDP, filter grid), `ui/` (button, accordion, icon)
- `src/lib/data` — mock product and campus catalogs
- `src/lib/cart-context.tsx` — client cart state
- `assets/brand` — logo source; `assets/design` — the original Stitch export (design tokens + page mockups)
- `public/brand/logo.png` — logo as served by the app

## Design tokens

Colors, type scale, and the zero-radius/chamfer/offset-shadow techwear treatments live in
`src/app/globals.css` under `@theme`, sourced from the Kinetic Spec.
