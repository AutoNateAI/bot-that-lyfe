---
name: Kinetic Spec
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#45464c'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#76777d'
  outline-variant: '#c6c6cd'
  surface-tint: '#565e73'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#131b2e'
  on-primary-container: '#7c839a'
  inverse-primary: '#bfc6df'
  secondary: '#775a00'
  on-secondary: '#ffffff'
  secondary-container: '#fece57'
  on-secondary-container: '#735700'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#261900'
  on-tertiary-container: '#9f7f41'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dbe2fb'
  primary-fixed-dim: '#bfc6df'
  on-primary-fixed: '#131b2e'
  on-primary-fixed-variant: '#3f465b'
  secondary-fixed: '#ffdf98'
  secondary-fixed-dim: '#eec14b'
  on-secondary-fixed: '#251a00'
  on-secondary-fixed-variant: '#5a4300'
  tertiary-fixed: '#ffdea4'
  tertiary-fixed-dim: '#e7c17c'
  on-tertiary-fixed: '#261900'
  on-tertiary-fixed-variant: '#5c4308'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  display-xl:
    fontFamily: Space Grotesk
    fontSize: 56px
    fontWeight: '700'
    lineHeight: 60px
    letterSpacing: -0.03em
  display-xl-mobile:
    fontFamily: Space Grotesk
    fontSize: 38px
    fontWeight: '700'
    lineHeight: 42px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 38px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 26px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 26px
    letterSpacing: -0.01em
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
  label-md:
    fontFamily: Space Grotesk
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.06em
  label-sm:
    fontFamily: Space Grotesk
    fontSize: 10px
    fontWeight: '700'
    lineHeight: 14px
    letterSpacing: 0.1em
  code-spec:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
spacing:
  gutter: 1rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-desktop: 2.5rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

The design system embodies technical prestige, elite builder culture, and high-velocity execution. Tailored for software engineers, ML researchers, and technical founders from top-tier computer science hubs, it merges the tactile precision of technical apparel spec sheets with high-performance mobile-first e-commerce. 

The aesthetic is clean techwear: stark, high-contrast surfaces, razor-sharp geometric framing, and precise metadata labels. The emotional delivery is assertive, intellectually uncompromising, and athletic—delivering the digital equivalent of an advanced modular garment. Micro-interactions should feel immediate, deterministic, and weighted, avoiding sluggish easing in favor of snappy, mechanical transitions.

## Colors

The palette establishes an architectural contrast between clean laboratory light fields and deep obsidian technical chassis:

- **Primary (`#0B1325` / Tech Navy & Obsidian)**: Serves as the primary ground for typographic hierarchy, structural wireframes, and hero callouts. It delivers absolute clarity without the deadening flat tone of pure black.
- **Secondary (`#C59B27` / Raw Auric Amber)**: Deployed with surgical intent for interactive anchors, checkout actions, active filter states, and technical verification badges.
- **Tertiary (`#E5C07B` / Light Gold Tint)**: Used for subtle metallic highlights, hair-thin internal accent borders, and micro-label backdrops.
- **Neutral Surface (`#F8FAFC` to `#FFFFFF`)**: An ultra-clean, hyper-bright backdrop that keeps garment photography crisp and uncompromised.
- **Supporting Technical Accents**: A functional system red (`#EF4444`) for low-stock warnings and a terminal green (`#10B981`) for live compiler and build telemetry states.

## Typography

Typography functions as a structural grid element:

- **Headlines & Technical Display (`Space Grotesk`)**: Provides an engineered, angular presence. Headlines must be styled in tight, tracked-in uppercase or strict sentence case. Display scales communicate athletic power and algorithmic certainty.
- **Functional Body Text (`Inter`)**: Delivers neutral readability across fabric specifications, size breakdowns, and order manifests.
- **Labels & System Meta (`Space Grotesk`, All Caps)**: All badge tags, campus tags, SKU indicators, and operational slogans (`RESEARCH. AUTOMATE. SIMULATE.`) use wide letter-spacing (`0.06em` to `0.1em`) to mimic mil-spec techwear tagging.

## Layout & Spacing

The layout is built around a dense, high-efficiency grid optimized for quick thumb navigation on mobile and structural multi-column parsing on desktop:

- **Mobile Canvas**: 4-column fluid grid, `1rem` margins, `1rem` gutters. Edge-to-edge product carousels with peek margins to indicate pagination.
- **Desktop Canvas**: 12-column fixed-max grid capped at `1440px`, with `2.5rem` outer margins and `1.5rem` gutters.
- **Cadence**: Components follow a strict 4px/8px modular scale. Spacing within cards is compact (`space-sm` to `space-md`) to enforce density, while section separations use generous jumps (`space-xl`) to establish hierarchy.

## Elevation & Depth

This system intentionally rejects ambient blur shadows and soft realism in favor of **sharp structural boundaries and metallic keylines**:

- **Low-Elevation Surfaces**: Plain white or `#F8FAFC` container faces outlined with a 1px solid border in `#E2E8F0` or `#0B1325`.
- **Active / Hover State Depth**: 1px to 2px offset solid drop-shadows using `#0B1325` (e.g., `box-shadow: 3px 3px 0px #0B1325`), creating an engineered, physical-chassis displacement.
- **Sticky / Drawers (Cart & Campus Selector)**: Backed with an ultra-thin 1px top or lateral accent border in raw amber (`#C59B27`), set over `#FFFFFF` with a high-density backdrop blur (`backdrop-filter: blur(16px)` at 95% surface opacity) to separate dynamic sheets from background apparel grids.

## Shapes

The shape architecture relies entirely on zero-radius geometry (`0px` / Sharp):

- Every card, button, tag, drawer, and input field uses unrounded corners.
- Micro-details rely on 45-degree chamfered corners (clip-path / diagonal notch) on spec labels, primary CTA tags, and active status indicators. This reflects tactical gear cutouts and industrial hardware aesthetic.

## Components

- **Buttons**:
  - *Primary CTA*: Solid `#0B1325` background, sharp corners, white text in `Space Grotesk` uppercase. Hover triggers a solid `#C59B27` border with a crisp `2px 2px 0px #C59B27` displacement.
  - *Accent Action ("Quick Deploy" / Add to Cart)*: High-voltage `#C59B27` solid background with `#0B1325` typography. Instant press translation of `1px 1px`.
  - *Secondary / Ghost*: Transparent background, 1px `#0B1325` border, active amber fill on press.

- **Techwear Badges & Campus Selector Tags**:
  - Compact, rectangular badges with a 1px border.
  - Inactive tags: `#F8FAFC` background with `#0B1325` text at `label-sm`.
  - Active campus tags (e.g., `[MIT.AI_LAB]`, `[STANFORD.CS]`, `[CMU.SCS]`): Inverted `#0B1325` fill, `#E5C07B` text, flanked by a leading monospaced index `[01]`.

- **Product Cards**:
  - Sharp 1px `#E2E8F0` border, jumping to `#0B1325` on interaction.
  - Upper corner houses floating specs: SKU number, system status dot, and thermal/weight classification.
  - Image containers use a clean, neutral gray-white studio background (`#F4F6F8`) with zero border radius.

- **Inputs & Form Controls**:
  - Form fields use a stark white fill, a 1px `#0B1325` bounding line, and `Space Grotesk` uppercase placeholder labels.
  - Focus state swaps border color to `#C59B27` and introduces a discrete corner indicator.
  - Checkboxes and radio buttons are sharp squares (`0px` radius). Selected states display a solid `#0B1325` block with an amber center pip.

- **Slide-out Cart & Checkout States**:
  - Flush right-hand drawer with a persistent 1px left border in `#0B1325`.
  - Item rows framed like modular components, complete with quantity toggles designed as stepper blocks (`-` / `QTY` / `+`).
  - Checkout CTA anchors to the bottom viewport with full-bleed width, displaying real-time encryption and build verification metadata: `SECURE_PAYMENT // VERIFIED BY AUTONATE_AI`.