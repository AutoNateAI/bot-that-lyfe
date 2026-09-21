#!/usr/bin/env python3
"""
Generate the v2 open-floor stage: assets/sets/stage_wide.png.

v1's bg_newsroom.png was a fixed 1920x1080 shot with a sit-down desk, sized for a
bust-shot crop. v2 needs full bodies, walking room for both anchors, and a screen
mount above each anchor's home mark — so the stage is a WIDE virtual canvas, much
bigger than the delivered 1920x1080 frame. tools/camera.py crops+scales a 16:9
window out of this at render time (the wide two-shot, or a push in on one anchor);
nothing about camera framing is baked into this art.

No desk/console this time (open floor, per the v2 set design decision) — the floor
grid runs to the bottom of frame, and the lower-third caption overlays the lower
legs, same as real broadcast lower-thirds.

Reuses the proven pieces from make_background.py (sky gradient, seeded skyline,
retrowave grid, vignette, and — importantly — the alpha_composite-layer discipline
that fixed v1's blending bug: draw anything with alpha<255 on its own transparent
layer, then Image.alpha_composite it onto the canvas; drawing translucent shapes
directly on a live RGBA canvas doesn't blend in Pillow, it just overwrites).

Run: python3 tools/make_stage.py
"""
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 3800, 2300
HORIZON = 520          # sky/skyline meets the grid floor
random.seed(11)

CYAN = (80, 240, 230)
MAGENTA = (255, 60, 190)
AMBER = (255, 190, 90)

FONT_DIR = "/System/Library/Fonts/Supplemental/"

# Home marks (stage-space x) each anchor walks to/from and stands at by default.
# v3 (production-fork redesign): pulled further apart than the original two-screen
# layout specifically to make room for ONE shared screen mounted between them —
# a real news-desk composition, anchors flanking a single display, rather than
# each anchor owning an isolated monitor at the far edge of the stage. Verified
# clear of overlap against CHAR_DISPLAY_W (camera.py) at these marks: each
# anchor's own body box, the shared screen box, and the *other* anchor's body box
# all have a real gap between them (no forced overlap at rest).
NATE_MARK_X = 1000
KAI_MARK_X = 2800
FLOOR_Y = 2200          # nominal foot line for full-body placement

# Shared screen bezel mount — ONE display centered between both anchors' marks,
# not one per anchor. This is the core v3 fix: the old layout (a screen at each
# far edge of the stage) meant a camera favoring either anchor could only ever
# show that anchor's own screen, and the two screens never appeared together —
# there was no such thing as "the shared screen" in the old geometry, just two
# unrelated monitors. Centering one screen between the marks means camera.py's
# per-anchor close shot (favor Nate / favor Kai) both naturally include the same
# screen in frame, satisfying the "camera cuts between anchors, screen stays in
# shot" requirement without needing a new camera concept — see camera.py.
# Kept at head/shoulder height (v2.2's fix, still correct) so the close single-cam
# crop stays a tight medium shot instead of zooming out for a screen mounted high.
# v4: bumped up from 820x500 — on a wide two-shot the old size read as a small
# distant plaque, not a display anyone could actually read the chart/graphic
# on. Checked against NATE_MARK_X/KAI_MARK_X + CHAR_DISPLAY_W (camera.py) at
# this width: still clears both anchors' body boxes at rest with a small
# margin, so it doesn't visually stack on top of either of them.
SCREEN_W, SCREEN_H = 1040, 640
SHARED_SCREEN_CENTER = (int((NATE_MARK_X + KAI_MARK_X) / 2), 1250)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def new_layer():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def sky_gradient():
    top = (10, 6, 28)
    mid = (40, 12, 62)
    low = (14, 8, 24)
    arr = np.zeros((HORIZON, W, 3), dtype=np.uint8)
    for y in range(HORIZON):
        t = y / HORIZON
        c = lerp(top, mid, t / 0.55) if t < 0.55 else lerp(mid, low, (t - 0.55) / 0.45)
        arr[y, :, :] = c
    return Image.fromarray(arr, "RGB")


def add_stars(layer, n=280):
    draw = ImageDraw.Draw(layer)
    for _ in range(n):
        x = random.randint(0, W - 1)
        y = random.randint(0, int(HORIZON * 0.7))
        r = random.choice([1, 1, 1, 2])
        a = random.randint(60, 170)
        draw.ellipse([x, y, x + r, y + r], fill=(255, 255, 255, a))


def add_skyline(layer, base_y, color, jitter, win_color, seed):
    rnd = random.Random(seed)
    draw = ImageDraw.Draw(layer)
    x = -20
    while x < W + 20:
        bw = rnd.randint(70, 160)
        bh = rnd.randint(int(jitter * 0.4), jitter)
        top = base_y - bh
        draw.rectangle([x, top, x + bw, base_y + 4], fill=color)
        rows = max(1, bh // 22)
        cols = max(1, bw // 18)
        for r in range(rows):
            for c in range(cols):
                if rnd.random() < 0.22:
                    wx = x + 6 + c * 18
                    wy = top + 8 + r * 22
                    if wx + 6 < x + bw and wy + 10 < base_y:
                        draw.rectangle([wx, wy, wx + 6, wy + 10], fill=win_color)
        x += bw + rnd.randint(6, 20)


def horizon_glow(layer):
    glow = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
    d = ImageDraw.Draw(glow)
    for i in range(130):
        a = int(90 * (1 - i / 130))
        c = lerp(CYAN, MAGENTA, i / 130) if i % 2 == 0 else lerp(MAGENTA, CYAN, i / 130)
        d.line([(0, 130 - i), (W, 130 - i)], fill=c + (a,), width=2)
    glow = glow.filter(ImageFilter.GaussianBlur(24))
    layer.alpha_composite(glow, (0, HORIZON - 140))


def grid_floor(layer):
    """Retrowave perspective grid from the horizon all the way to the bottom of
    frame — no desk to stop it this time."""
    draw = ImageDraw.Draw(layer)
    vp = (W // 2, HORIZON - 6)
    span = H - HORIZON
    n_rays = 34
    for i in range(n_rays + 1):
        t = i / n_rays
        x_bottom = int(-W * 0.5 + t * W * 2.0)
        draw.line([vp, (x_bottom, H)], fill=CYAN + (130,), width=1)
    n_rungs = 20
    for j in range(1, n_rungs + 1):
        t = (j / n_rungs) ** 1.8
        y = int(HORIZON + t * span)
        a = int(50 + 130 * t)
        draw.line([(0, y), (W, y)], fill=MAGENTA + (min(a, 190),), width=1)


def floor_haze(layer):
    """Soft ground-level haze band so full-height figures don't stand on a bare
    grid line — a bit of atmosphere at the horizon/floor seam."""
    haze = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
    d = ImageDraw.Draw(haze)
    for i in range(120):
        a = int(70 * (1 - i / 120))
        d.line([(0, i), (W, i)], fill=(30, 18, 46, a))
    haze = haze.filter(ImageFilter.GaussianBlur(20))
    layer.alpha_composite(haze, (0, HORIZON - 20))


def screen_mount(canvas, center, tag_color):
    """Empty neon-bezel monitor frame — content is composited in per-line by
    tools/screen_graphics.py at render time, this is art only."""
    cx, cy = center
    box = (cx - SCREEN_W // 2, cy - SCREEN_H // 2, cx + SCREEN_W // 2, cy + SCREEN_H // 2)

    glow = new_layer()
    gd = ImageDraw.Draw(glow)
    gd.rounded_rectangle(box, radius=18, outline=tag_color + (255,), width=10)
    glow = glow.filter(ImageFilter.GaussianBlur(14))
    canvas.alpha_composite(glow)

    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(box, radius=18, fill=(8, 10, 18, 255), outline=tag_color + (230,), width=4)
    # standby glyph so the mount doesn't look broken before content is composited
    draw.line([(box[0] + 40, cy), (box[2] - 40, cy)], fill=tag_color + (90,), width=2)
    # thin support strut down to the floor mark, sells "mounted" rather than floating
    draw.line([(cx, box[3]), (cx, box[3] + 46)], fill=tag_color + (160,), width=6)


def logo_bug(canvas):
    try:
        f_title = ImageFont.truetype(FONT_DIR + "Futura.ttc", 58, index=0)
        f_sub = ImageFont.truetype(FONT_DIR + "Arial Bold.ttf", 24)
    except Exception:
        f_title = ImageFont.load_default()
        f_sub = ImageFont.load_default()
    x, y = 70, 50
    glow = new_layer()
    gd = ImageDraw.Draw(glow)
    gd.text((0, 0), "HIGHER THINKING", font=f_title, fill=CYAN + (255,))
    glow = glow.filter(ImageFilter.GaussianBlur(7))
    canvas.alpha_composite(glow, (x - 4, y - 4))
    draw = ImageDraw.Draw(canvas)
    draw.text((x, y), "HIGHER THINKING", font=f_title, fill=(235, 255, 253, 255))
    # Baked into the stage art and visible in every frame — BTL's tagline.
    draw.text((x + 4, y + 68), "RESEARCH. AUTOMATE. SIMULATE.", font=f_sub, fill=MAGENTA + (230,))


def vignette(canvas):
    v = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(v)
    d.ellipse([-W * 0.2, -H * 0.3, W * 1.2, H * 1.2], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(220))
    va = np.array(v).astype(np.float32)
    dark_amount = np.clip(85 - va * (85 / 255), 0, 85).astype(np.uint8)
    layer = new_layer()
    layer.putalpha(Image.fromarray(dark_amount, "L"))
    canvas.alpha_composite(layer)


def main():
    canvas = Image.new("RGBA", (W, H), (10, 6, 22, 255))
    canvas.alpha_composite(sky_gradient().convert("RGBA"), (0, 0))

    stars = new_layer()
    add_stars(stars)
    canvas.alpha_composite(stars)

    sky_buildings = new_layer()
    add_skyline(sky_buildings, base_y=HORIZON - 30, color=(24, 16, 46, 255), jitter=240,
                win_color=(140, 230, 255, 210), seed=1)
    canvas.alpha_composite(sky_buildings)

    near_buildings = new_layer()
    add_skyline(near_buildings, base_y=HORIZON, color=(14, 9, 30, 255), jitter=160,
                win_color=(255, 200, 140, 230), seed=2)
    canvas.alpha_composite(near_buildings)

    horizon_glow(canvas)

    grid = new_layer()
    grid_floor(grid)
    canvas.alpha_composite(grid)

    floor_haze(canvas)

    # One shared screen, tag-colored amber (neutral — belongs to neither anchor).
    screen_mount(canvas, SHARED_SCREEN_CENTER, AMBER)

    logo_bug(canvas)
    vignette(canvas)

    out = canvas.convert("RGB")
    out.save("assets/sets/stage_wide.png")
    print("wrote assets/sets/stage_wide.png", out.size)


if __name__ == "__main__":
    main()
