#!/usr/bin/env python3
"""
tools/screen_graphics.py — per-anchor "monitor" content cards.

tools/make_stage.py bakes an empty neon bezel for each anchor's screen into the
static stage art; this module renders what goes *inside* it per line, pulling
straight from episode.json's existing sources[] (id/url/fact) — no new research
format needed. The speaking anchor's screen shows the fact behind their current
line (if it cites one); otherwise, both anchors' screens show a idle standby
card so the mounts never look broken.

Sized to fill make_stage.SCREEN_W x SCREEN_H so it drops straight into the bezel
interior at render time.
"""
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
FONT_DIR = "/System/Library/Fonts/Supplemental/"
BG = (8, 10, 18, 255)


def _fonts():
    try:
        return {
            "headline": ImageFont.truetype(FONT_DIR + "Arial Bold.ttf", 34),
            "ticker": ImageFont.truetype(FONT_DIR + "Arial.ttf", 22),
            "standby": ImageFont.truetype(FONT_DIR + "Arial Bold.ttf", 26),
            "stat_value": ImageFont.truetype(FONT_DIR + "Arial Black.ttf", 110),
            "stat_label": ImageFont.truetype(FONT_DIR + "Arial Bold.ttf", 26),
            "timeline_year": ImageFont.truetype(FONT_DIR + "Arial Black.ttf", 30),
            "timeline_label": ImageFont.truetype(FONT_DIR + "Arial.ttf", 20),
            "table_header": ImageFont.truetype(FONT_DIR + "Arial Bold.ttf", 22),
            "table_cell": ImageFont.truetype(FONT_DIR + "Arial.ttf", 24),
            "quote_mark": ImageFont.truetype(FONT_DIR + "Arial Black.ttf", 80),
            "quote_text": ImageFont.truetype(FONT_DIR + "Arial Italic.ttf", 30),
            "quote_attr": ImageFont.truetype(FONT_DIR + "Arial Bold.ttf", 22),
            "caption": ImageFont.truetype(FONT_DIR + "Arial.ttf", 22),
        }
    except Exception:
        d = ImageFont.load_default()
        return {k: d for k in ("headline", "ticker", "standby", "stat_value", "stat_label",
                                "timeline_year", "timeline_label", "table_header", "table_cell",
                                "quote_mark", "quote_text", "quote_attr", "caption")}


def _domain_ticker(draw, domain, tag_color, width, pad, fonts):
    """Shared top strip: DOMAIN.COM over a thin rule — every card type opens with
    this so the source is always legible regardless of what's below it."""
    draw.text((pad, pad), domain.upper(), font=fonts["ticker"], fill=tag_color + (220,))
    draw.line([(pad, pad + 34), (width - pad, pad + 34)], fill=tag_color + (120,), width=2)


def _corner_ticks(draw, tag_color, width, height, pad):
    for cx, cy, dx, dy in [(pad, height - pad, 26, 0), (pad, height - pad, 0, -26)]:
        draw.line([(cx, cy), (cx + dx, cy + dy)], fill=tag_color + (200,), width=3)


def _fit_text_font(draw, text, base_font, max_width, min_size=36, step=6):
    """Shrink base_font (a truetype ImageFont) until `text` fits max_width, down to
    min_size — so a stat card's big value never blows past the card edge no matter
    what the author puts in it."""
    font = base_font
    try:
        size = font.size
    except AttributeError:
        return font
    while draw.textlength(text, font=font) > max_width and size > min_size:
        size -= step
        font = font.font_variant(size=size)
    return font


def domain_of(url):
    net = urlparse(url).netloc
    return net[4:] if net.startswith("www.") else net


def _wrap(draw, text, font, max_width, max_lines):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
        if len(lines) == max_lines:
            break
    if cur and len(lines) < max_lines:
        lines.append(cur)
    return lines


def build_card(fact_text, domain, tag_color, width, height, fonts=None):
    """Plain headline/fact card — the default for a cited line with no explicit
    `screen` spec. type: "text"."""
    fonts = fonts or _fonts()
    img = Image.new("RGBA", (width, height), BG)
    draw = ImageDraw.Draw(img)
    pad = 34

    _domain_ticker(draw, domain, tag_color, width, pad, fonts)

    lines = _wrap(draw, fact_text, fonts["headline"], width - pad * 2, max_lines=5)
    ty = pad + 60
    for ln in lines:
        draw.text((pad, ty), ln, font=fonts["headline"], fill=(240, 245, 250, 255))
        ty += 42

    _corner_ticks(draw, tag_color, width, height, pad)
    return img


def build_stat(value, label, domain, tag_color, width, height, fonts=None, sublabel=None):
    """A big-number/short-value callout. type: "stat". `value` should be short
    (a number, a year span, a checkmark) — this is a poster, not a paragraph."""
    fonts = fonts or _fonts()
    img = Image.new("RGBA", (width, height), BG)
    draw = ImageDraw.Draw(img)
    pad = 34

    _domain_ticker(draw, domain, tag_color, width, pad, fonts)

    vfont = _fit_text_font(draw, value, fonts["stat_value"], width - pad * 2 - 20)
    vw = draw.textlength(value, font=vfont)
    draw.text(((width - vw) / 2, height / 2 - 78), value, font=vfont,
               fill=(240, 245, 250, 255))
    lw = draw.textlength(label.upper(), font=fonts["stat_label"])
    draw.text(((width - lw) / 2, height / 2 + 48), label.upper(), font=fonts["stat_label"],
               fill=tag_color + (230,))
    if sublabel:
        sw = draw.textlength(sublabel, font=fonts["ticker"])
        draw.text(((width - sw) / 2, height - pad - 22), sublabel, font=fonts["ticker"],
                   fill=(180, 190, 210, 200))

    _corner_ticks(draw, tag_color, width, height, pad)
    return img


def build_timeline(events, domain, tag_color, width, height, fonts=None):
    """A horizontal timeline with 2-4 dated nodes. type: "timeline".
    events: [{"year": "1946", "label": "Conjecture posed"}, ...]"""
    fonts = fonts or _fonts()
    img = Image.new("RGBA", (width, height), BG)
    draw = ImageDraw.Draw(img)
    pad = 44

    _domain_ticker(draw, domain, tag_color, width, pad, fonts)

    # nodes are inset well past the label half-width so an end label centered on
    # the first/last node never runs off the card edge
    label_max_w = 150
    inset = pad + label_max_w / 2 + 8
    line_y = height / 2 + 10
    x0, x1 = inset, width - inset
    draw.line([(x0, line_y), (x1, line_y)], fill=tag_color + (200,), width=3)

    n = max(len(events), 1)
    for i, ev in enumerate(events):
        x = x0 if n == 1 else x0 + (x1 - x0) * (i / (n - 1))
        draw.ellipse([x - 9, line_y - 9, x + 9, line_y + 9], fill=tag_color + (255,),
                     outline=(240, 245, 250, 255), width=2)
        year = ev.get("year", "")
        yw = draw.textlength(year, font=fonts["timeline_year"])
        draw.text((x - yw / 2, line_y - 56), year, font=fonts["timeline_year"],
                   fill=(240, 245, 250, 255))
        label_lines = _wrap(draw, ev.get("label", ""), fonts["timeline_label"], label_max_w, max_lines=2)
        ly = line_y + 24
        for ln in label_lines:
            lw = draw.textlength(ln, font=fonts["timeline_label"])
            draw.text((x - lw / 2, ly), ln, font=fonts["timeline_label"], fill=(190, 200, 215, 235))
            ly += 24

    _corner_ticks(draw, tag_color, width, height, pad)
    return img


def build_table(rows, domain, tag_color, width, height, fonts=None, header=None):
    """A simple 2-column table. type: "table".
    rows: [["Fields Medalist review", "Recommended, no hesitation"], ...]"""
    fonts = fonts or _fonts()
    img = Image.new("RGBA", (width, height), BG)
    draw = ImageDraw.Draw(img)
    pad = 34

    _domain_ticker(draw, domain, tag_color, width, pad, fonts)

    col_split = width * 0.42
    top = pad + 56
    if header:
        draw.text((pad, top), header[0].upper(), font=fonts["table_header"], fill=tag_color + (230,))
        draw.text((col_split + 16, top), header[1].upper(), font=fonts["table_header"],
                   fill=tag_color + (230,))
        top += 34
        draw.line([(pad, top), (width - pad, top)], fill=tag_color + (100,), width=1)
        top += 14

    row_h = (height - top - pad) / max(len(rows), 1)
    for i, (a, b) in enumerate(rows):
        ry = top + i * row_h + 6
        for extra, ln in enumerate(_wrap(draw, a, fonts["table_cell"], col_split - pad - 10, 2)):
            draw.text((pad, ry + extra * 28), ln, font=fonts["table_cell"], fill=(235, 240, 248, 255))
        for extra, ln in enumerate(_wrap(draw, b, fonts["table_cell"], width - col_split - pad - 16, 2)):
            draw.text((col_split + 16, ry + extra * 28), ln, font=fonts["table_cell"],
                       fill=(200, 210, 225, 245))
        if i < len(rows) - 1:
            draw.line([(pad, top + (i + 1) * row_h), (width - pad, top + (i + 1) * row_h)],
                       fill=(255, 255, 255, 25), width=1)

    _corner_ticks(draw, tag_color, width, height, pad)
    return img


def build_quote(quote_text, attribution, domain, tag_color, width, height, fonts=None):
    """A pull-quote card. type: "quote". Direct quotes only — pull straight from a
    source's `fact`, never paraphrase into something that reads as a quotation."""
    fonts = fonts or _fonts()
    img = Image.new("RGBA", (width, height), BG)
    draw = ImageDraw.Draw(img)
    pad = 34

    _domain_ticker(draw, domain, tag_color, width, pad, fonts)

    draw.text((pad - 6, pad + 30), "“", font=fonts["quote_mark"], fill=tag_color + (160,))
    lines = _wrap(draw, quote_text, fonts["quote_text"], width - pad * 2 - 20, max_lines=4)
    ty = pad + 90
    for ln in lines:
        draw.text((pad + 14, ty), ln, font=fonts["quote_text"], fill=(240, 245, 250, 255))
        ty += 38
    draw.text((pad + 14, height - pad - 30), f"— {attribution}", font=fonts["quote_attr"],
               fill=tag_color + (220,))

    _corner_ticks(draw, tag_color, width, height, pad)
    return img


def build_image_card(image_path, caption, domain, tag_color, width, height, fonts=None):
    """A real image (photo/chart/screenshot) dropped in from research/epNNN/,
    letterboxed to fit with a caption strip. type: "image". Only ever point this
    at a real captured file — never synthesize something meant to look like a
    screenshot of a real page; that's fabricating evidence, not visualizing it."""
    fonts = fonts or _fonts()
    img = Image.new("RGBA", (width, height), BG)
    draw = ImageDraw.Draw(img)
    pad = 34

    _domain_ticker(draw, domain, tag_color, width, pad, fonts)

    cap_h = 44
    frame_top = pad + 50
    frame_h = height - frame_top - pad - cap_h
    frame_w = width - pad * 2
    try:
        photo = Image.open(image_path).convert("RGBA")
        photo.thumbnail((frame_w, frame_h), Image.LANCZOS)
        px = pad + (frame_w - photo.width) // 2
        py = frame_top + (frame_h - photo.height) // 2
        img.alpha_composite(photo, (px, py))
    except Exception:
        draw.rectangle([pad, frame_top, width - pad, frame_top + frame_h],
                        outline=tag_color + (150,), width=2)
        msg = "image unavailable"
        mw = draw.textlength(msg, font=fonts["ticker"])
        draw.text(((width - mw) / 2, frame_top + frame_h / 2 - 10), msg, font=fonts["ticker"],
                   fill=(150, 155, 170, 200))

    if caption:
        draw.text((pad, height - pad - cap_h + 10), caption, font=fonts["caption"],
                   fill=(200, 208, 222, 230))

    _corner_ticks(draw, tag_color, width, height, pad)
    return img


def fit_image_to_box(img, width, height):
    """Scale (not stretch) an already-loaded RGBA image to fit inside
    (width, height), centered on the same background every card type uses.
    Shared by build_meme_card (loads from a generated meme file) and
    make_episode.py's reel screen panel (already has a rendered PIL image —
    the current line's shared_screen — in memory, no file to load)."""
    fitted = img.copy()
    fitted.thumbnail((width, height), Image.LANCZOS)
    canvas = Image.new("RGBA", (width, height), BG)
    px = (width - fitted.width) // 2
    py = (height - fitted.height) // 2
    canvas.alpha_composite(fitted.convert("RGBA"), (px, py))
    return canvas


def build_meme_card(image_path, width, height):
    """A contextual meme image, scaled (not stretched) to fit the box. type:
    "meme". No ticker/caption overlay — a meme has its own baked-in caption
    text (see tools/generate_screen_meme.py's STYLE_LOCK), so drawing
    anything on top of it would clutter someone else's typography.

    v10: this used to hard-resize to (width, height) exactly, distorting the
    image whenever its aspect ratio didn't match the box (stretching a face
    wide/tall). generate_screen_meme.py used to force-crop every generation
    to match the screen's exact aspect specifically to make that stretch a
    no-op — it no longer does that (see that script's own v10 note), so this
    now does what it always should have: scale uniformly to fit inside the
    box and pad the rest with the same background every other card type uses,
    same as build_image_card already does for a real chart/photo."""
    img = Image.open(image_path).convert("RGBA")
    return fit_image_to_box(img, width, height)


def _resolve_path(spec, base_dir):
    spec = dict(spec)
    if base_dir and "path" in spec:
        image_path = Path(spec["path"]).expanduser()
        if not image_path.is_absolute():
            spec["path"] = str(Path(base_dir) / image_path)
    return spec


def render_screen(spec, tag_color, width, height, fonts=None, base_dir=None):
    """Dispatch a `screen` spec (from episode.json) to the right renderer.
    spec["type"]: "text" | "stat" | "timeline" | "table" | "quote" | "image" | "meme"."""
    fonts = fonts or _fonts()
    t = spec.get("type", "text")
    if t == "stat":
        return build_stat(spec["value"], spec["label"], spec.get("domain", ""), tag_color,
                           width, height, fonts, sublabel=spec.get("sublabel"))
    if t == "timeline":
        return build_timeline(spec["events"], spec.get("domain", ""), tag_color, width, height, fonts)
    if t == "table":
        return build_table(spec["rows"], spec.get("domain", ""), tag_color, width, height, fonts,
                            header=spec.get("header"))
    if t == "quote":
        return build_quote(spec["quote"], spec["attribution"], spec.get("domain", ""), tag_color,
                            width, height, fonts)
    if t == "image":
        spec = _resolve_path(spec, base_dir)
        return build_image_card(spec["path"], spec.get("caption", ""), spec.get("domain", ""),
                                 tag_color, width, height, fonts)
    if t == "meme":
        spec = _resolve_path(spec, base_dir)
        return build_meme_card(spec["path"], width, height)
    return build_card(spec.get("fact", ""), spec.get("domain", ""), tag_color, width, height, fonts)


def build_standby(tag_color, width, height, fonts=None):
    fonts = fonts or _fonts()
    img = Image.new("RGBA", (width, height), BG)
    draw = ImageDraw.Draw(img)
    label = "HIGHER THINKING"
    tw = draw.textlength(label, font=fonts["standby"])
    draw.text(((width - tw) / 2, height / 2 - 40), label, font=fonts["standby"],
               fill=tag_color + (200,))
    # a few flat waveform bars for idle-monitor flavor
    bar_y = height / 2 + 10
    bar_w, gap = 10, 8
    n = 14
    total = n * bar_w + (n - 1) * gap
    x0 = (width - total) / 2
    heights = [10, 22, 14, 30, 18, 26, 12, 28, 16, 24, 10, 20, 14, 22]
    for i, h in enumerate(heights):
        x = x0 + i * (bar_w + gap)
        draw.rectangle([x, bar_y - h / 2, x + bar_w, bar_y + h / 2], fill=tag_color + (130,))
    return img


def screen_content_for_line(ep, line, tag_color, width, height, fonts=None, base_dir=None):
    """The image to composite into a screen bezel for this line:
    1. an explicit `line["screen"]` spec, if present (any type incl. diagrams/
       tables/quotes/images — see render_screen) — `domain` in the spec is
       optional, auto-filled from the line's first cited source if omitted;
    2. else the first cited source's fact as a plain text card;
    3. else the branded standby card.

    v4: (3) used to be build_line_summary(), which put the *line's own spoken
    text* (or its popup headline) on the screen — meaning banter with no
    citation and no explicit `screen` spec rendered as a caption box standing
    in for a monitor, indistinguishable from the lower-third caption already
    on screen. The mount is a display device showing lab output, not a second
    subtitle track — an uncited beat with nothing to show gets the idle
    standby card, same as it does between cited lines today."""
    cites = line.get("cite", [])
    sources_by_id = {s["id"]: s for s in ep.get("sources", [])}
    cited_src = sources_by_id.get(cites[0]) if cites else None

    spec = line.get("screen")
    if spec:
        spec = dict(spec)
        if "domain" not in spec and cited_src:
            spec["domain"] = domain_of(cited_src["url"])
        return render_screen(spec, tag_color, width, height, fonts, base_dir=base_dir)

    if cited_src:
        return build_card(cited_src["fact"], domain_of(cited_src["url"]), tag_color, width, height, fonts)

    return build_standby(tag_color, width, height, fonts)


def _screen_spec_for_item(item):
    if isinstance(item, dict) and isinstance(item.get("screen"), dict):
        return item["screen"]
    return item


def screen_sequence_for_line(ep, line, tag_color, width, height, fonts=None, base_dir=None):
    """Return timed screen cards for one spoken line.

    Backwards-compatible default is a single card from screen_content_for_line().
    Long lines may opt into `screens[]`:

      {"at": 0.0, "screen": {"type": "meme", ...}}
      {"start_word": 8, "screen": {"type": "meme", ...}}

    `at` is seconds from the start of this line; `start_word` is converted to
    an approximate time by make_episode.py, where the line duration is known.
    """
    items = line.get("screens")
    if not items:
        return [{"at": 0.0, "start_word": 0, "image": screen_content_for_line(
            ep, line, tag_color, width, height, fonts, base_dir=base_dir)}]

    cites = line.get("cite", [])
    sources_by_id = {s["id"]: s for s in ep.get("sources", [])}
    cited_src = sources_by_id.get(cites[0]) if cites else None
    rendered = []
    for item in items:
        if not isinstance(item, dict):
            continue
        spec = _screen_spec_for_item(item)
        if not isinstance(spec, dict):
            continue
        spec = dict(spec)
        if "domain" not in spec and cited_src:
            spec["domain"] = domain_of(cited_src["url"])
        rendered.append({
            "at": item.get("at", spec.get("at", 0.0)),
            "start_word": item.get("start_word", spec.get("start_word")),
            "image": render_screen(spec, tag_color, width, height, fonts, base_dir=base_dir),
        })

    if not rendered:
        rendered.append({"at": 0.0, "start_word": 0, "image": screen_content_for_line(
            ep, line, tag_color, width, height, fonts, base_dir=base_dir)})
    return rendered


if __name__ == "__main__":
    import json
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import make_stage as stage

    ep_path = REPO / "episodes/ep001-ai-math-conjecture/episode.json"
    ep = json.loads(ep_path.read_text())
    fonts = _fonts()
    out_dir = REPO / "tools/tmp_pose_check"
    out_dir.mkdir(exist_ok=True)

    cited_line = next(l for l in ep["lines"] if l.get("cite"))
    card = screen_content_for_line(ep, cited_line, stage.CYAN, stage.SCREEN_W, stage.SCREEN_H, fonts)
    card.convert("RGB").save(out_dir / "screen_card.png")
    standby = build_standby(stage.MAGENTA, stage.SCREEN_W, stage.SCREEN_H, fonts)
    standby.convert("RGB").save(out_dir / "screen_standby.png")
    print(f"wrote screen graphic stills to {out_dir}")
