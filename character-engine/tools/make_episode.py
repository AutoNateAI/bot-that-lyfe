#!/usr/bin/env python3
"""
tools/make_episode.py — runs pipeline stages 3-7 (VOICE, SYNC, RENDER, ASSEMBLE,
SCORE) for a given episode.json end to end.

Usage:
    python3 tools/make_episode.py episodes/ep001-ai-math-conjecture/episode.json

v2 RENDER stage: full-body anchors posed by tools/rig_pose.py's FK engine (walking,
gestures, idle sway) standing on the wide open-floor set (tools/make_stage.py), each
with their own content screen (tools/screen_graphics.py) showing the fact behind a
cited line. tools/camera.py crops/scales a 1920x1080 window out of that wide stage —
a two-shot for cited lines (so the point-at-screen gesture and the screen both read),
a push in on whoever's speaking otherwise — replacing v1's dim/desaturate trick with
an actual camera cut (with a quick simulated push, not a hard cut).

VOICE (synth_line), SYNC (rhubarb_sync), and SCORE (ensure_audio_assets, mix_in_ding,
score_episode) are unchanged from v1 — nothing about audio changed in v2.
"""
import json
import math
import os
import random
import shutil
import subprocess
import sys
import time
import urllib.parse
import argparse
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO = Path(__file__).resolve().parent.parent
# Consolidated, easy-to-browse export location — every episode's working files
# (frames/, audio/, intermediate .mp4s) still live under episodes/<slug>/ as
# build cache, but the one finished deliverable per render moves here so
# Nathan doesn't have to go hunting through 18+ episode folders to find the
# actual videos to watch/upload. Mirrors the youtube/reel split the pipeline
# already has via --format. Gitignored, same as episodes/*/*.mp4.
OUTPUT_DIR = REPO / "output"
sys.path.insert(0, str(REPO / "tools"))
import camera  # noqa: E402
import make_stage as stage  # noqa: E402
import rig_pose  # noqa: E402
import screen_graphics  # noqa: E402

RHUBARB = REPO / "tools/bin/rhubarb"
SAY = REPO / "voices/say.sh"
STAGE_PATH = REPO / "assets/sets/stage_wide.png"
FONT_DIR = "/System/Library/Fonts/Supplemental/"

MUSIC_BED = REPO / "assets/music/bed_loop.wav"
SFX_DING = REPO / "assets/sfx/ding.wav"
SFX_INTRO = REPO / "assets/sfx/intro_stinger.wav"
SFX_OUTRO = REPO / "assets/sfx/outro_stinger.wav"

FPS = 24
DELIVER_W, DELIVER_H = camera.DELIVER_W, camera.DELIVER_H
FORMAT_PRESETS = {
    "youtube": {"size": (1920, 1080), "label": "youtube"},
    "reel": {"size": (1080, 1920), "label": "reel"},
}

RHUBARB_TO_VISEME = {"A": "M", "B": "D", "C": "Ee", "D": "Aa", "E": "Oh",
                      "F": "WOo", "G": "F", "H": "L", "X": "neutral"}

TAG_COLOR = {"nate": stage.CYAN, "kai": stage.MAGENTA}

# Motion tuning — see rig_pose.py for the pose/walk-cycle primitives these drive.
GESTURE_EASE_FRAMES = 6     # frames to ease into a held gesture / back to rest
CAM_TRANSITION_FRAMES = 4   # frames of push/zoom when the camera window changes
WALK_SPEED = 5.0            # stage-px/frame (~120px/s at 24fps)
WALK_CYCLE_FRAMES = 16      # one full gait cycle, ~0.67s — see rig_pose.walk_cycle_frames
PACE_DISTANCE = 240         # stage-px a "pace_out" move steps away from the home mark
BRAND_TEXT = "BTL"


def cta_url_for(ep):
    """The URL the outro card sends viewers to. Episodes here are standalone
    scripts (not derived from a published article), so this defaults to the
    storefront root; set an explicit `cta_url` in episode.json to point a
    given episode at a specific drop/product/campus page instead."""
    return ep.get("cta_url") or "https://botthatlyfe.com/"


# ---------------------------------------------------------------- character assets

class DisplayCache:
    """Per-character cache of posed, display-scaled body images, keyed by
    (pose, viseme, eye_state, brow_up). Doesn't help while a mouth is actively
    talking (viseme changes every few frames) but collapses the idle listener and
    any held pose down to a handful of renders instead of one per frame — see
    rig_pose.PosedBodyCache, which this wraps and adds the display-resize to."""

    def __init__(self, rig):
        self.rig = rig
        self._cache = {}

    def get(self, pose, viseme, eye_state, brow_up):
        key = (rig_pose.pose_signature(pose), viseme, eye_state, brow_up)
        img = self._cache.get(key)
        if img is None:
            body = rig_pose.render_body(self.rig, pose, viseme, eye_state, brow_up)
            img = body.resize((camera.CHAR_DISPLAY_W, camera.CHAR_DISPLAY_H), Image.LANCZOS)
            self._cache[key] = img
        return img


def load_rigs():
    nate = rig_pose.Rig("nate", REPO / "assets/mouths/male_mouths")
    kai = rig_pose.Rig("kai", REPO / "assets/mouths/female_mouths")
    return {"nate": nate, "kai": kai}


def ensure_stage_asset():
    if not STAGE_PATH.exists():
        subprocess.run([sys.executable, str(REPO / "tools/make_stage.py")], check=True)


# ---------------------------------------------------------------- voice + sync (unchanged from v1)

def synth_line(speaker, text, wav_path):
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    if os_environ_true("USE_OPENAI_TTS"):
        engine = "openai_tts"
    elif speaker == "nate" and os_environ_true("USE_CHATTERBOX_NATE"):
        engine = "chatterbox_nate"
    else:
        engine = "macos_say"
    meta_path = wav_path.with_suffix(".voice.json")
    expected_meta = {"speaker": speaker, "text": text, "engine": engine}
    if wav_path.exists() and meta_path.exists():
        try:
            found_meta = json.loads(meta_path.read_text())
            if found_meta == expected_meta or (
                engine == "openai_tts"
                and found_meta.get("speaker") == speaker
                and found_meta.get("text") == text
                and found_meta.get("engine") == engine
            ):
                print(f"    voice cache hit: {wav_path.name}")
                return
        except Exception:
            pass
    subprocess.run([str(SAY), speaker, text, str(wav_path)], check=True)
    meta_path.write_text(json.dumps(expected_meta, indent=2) + "\n")


def os_environ_true(name):
    import os

    return os.environ.get(name, "").lower() in {"1", "true", "yes", "on"}


def ensure_audio_assets():
    if not all(p.exists() for p in (MUSIC_BED, SFX_DING, SFX_INTRO, SFX_OUTRO)):
        subprocess.run([sys.executable, str(REPO / "tools/make_audio.py")], check=True)


def ensure_batched_nate_voice(ep_path):
    """Generate all missing Nate cloned-voice lines in one Chatterbox process."""
    if os_environ_true("USE_OPENAI_TTS"):
        return
    if not os_environ_true("USE_CHATTERBOX_NATE"):
        return
    chatterbox_py = Path("/Users/autonate/code/autonateai-roblox-gamelab/.venv/chatterbox/bin/python")
    py = chatterbox_py if chatterbox_py.exists() else Path(sys.executable)
    subprocess.run([str(py), str(REPO / "tools/batch_chatterbox_nate.py"), str(ep_path)], check=True)


def ensure_batched_openai_voice(ep_path):
    """Generate all missing OpenAI TTS lines in one pre-render batch."""
    if not os_environ_true("USE_OPENAI_TTS"):
        return
    subprocess.run([sys.executable, str(REPO / "tools/batch_openai_tts.py"), str(ep_path)], check=True)


def ensure_batched_screen_memes(ep_path, render_format="youtube"):
    """Generate every line's contextual screen meme in one parallel batch,
    same idea as ensure_batched_openai_voice — a line's `screen` spec
    ({"type": "meme", "prompt": ..., "path": ...}) is the source of truth,
    generate_screen_meme.py's own caching means an unchanged prompt costs
    nothing here on a re-render."""
    subprocess.run([sys.executable, str(REPO / "tools/generate_screen_meme.py"),
                     "--episode", str(ep_path), "--format", render_format], check=True)


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        check=True, capture_output=True, text=True,
    )
    return float(out.stdout.strip())


def cover_resize(img, target_w, target_h):
    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    new_w, new_h = int(src_w * scale + 0.5), int(src_h * scale + 0.5)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def contextual_background_path(ep):
    spec = ep.get("background_meme")
    if isinstance(spec, dict) and spec.get("path"):
        path = Path(spec["path"]).expanduser()
        if path.exists():
            return path
    return None


def background_cache_key(ep):
    spec = ep.get("background_meme")
    if not isinstance(spec, dict):
        return None
    return {k: spec.get(k) for k in ("path", "prompt")}


def build_stage_background(ep, render_format):
    base = Image.open(STAGE_PATH).convert("RGBA")
    bg_path = contextual_background_path(ep)
    if not bg_path:
        return base

    contextual = Image.open(bg_path).convert("RGB")
    contextual = cover_resize(contextual, stage.W, stage.H).convert("RGBA")
    shade = Image.new("RGBA", (stage.W, stage.H), (4, 5, 12, 95))
    contextual.alpha_composite(shade)
    # Keep enough of the native set art to preserve the floor grid, screen mount,
    # and show identity while letting the episode-specific image carry the mood.
    return Image.blend(contextual, base, 0.42)


def build_delivery_backdrop(ep, render_format):
    bg_path = contextual_background_path(ep)
    fallback = render_backdrop(DELIVER_W, DELIVER_H).convert("RGBA")
    if not bg_path:
        return fallback
    contextual = Image.open(bg_path).convert("RGB")
    contextual = cover_resize(contextual, DELIVER_W, DELIVER_H).convert("RGBA")
    contextual.alpha_composite(Image.new("RGBA", (DELIVER_W, DELIVER_H), (4, 5, 12, 110)))
    return Image.blend(contextual, fallback, 0.30)


def mix_in_ding(wav_path, out_path):
    """Overlay the citation ding at t=0, keeping the dialogue's own duration/volume."""
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(wav_path), "-i", str(SFX_DING),
        "-filter_complex", "[1:a]volume=0.7[d];[0:a][d]amix=inputs=2:duration=first:normalize=0[aout]",
        "-map", "[aout]", str(out_path),
    ], check=True)


def rhubarb_sync(wav_path, tsv_path):
    subprocess.run([str(RHUBARB), "-r", "phonetic", "-f", "tsv", "-o", str(tsv_path),
                     str(wav_path)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    cues = []
    for line in open(tsv_path):
        parts = line.split()
        if len(parts) >= 2 and parts[1] in RHUBARB_TO_VISEME:
            cues.append((float(parts[0]), RHUBARB_TO_VISEME[parts[1]]))
    if not cues:
        sys.exit(f"no cues parsed from {tsv_path}")
    return cues


# ---------------------------------------------------------------- blinking (unchanged from v1)

def blink_windows(n_frames, fps, rng):
    """1 frame each: half -> closed -> half, spaced 2-5s apart (open is the default,
    no overlay needed)."""
    windows = {}
    t = rng.uniform(0.4, 2.2)
    while t * fps < n_frames:
        start = int(t * fps)
        for i, state in enumerate(("half", "closed", "half")):
            fi = start + i
            if fi < n_frames:
                windows[fi] = state
        t += rng.uniform(2.0, 5.0)
    return windows


def eye_state_at(f, windows, force_half=False):
    if force_half:
        return "half"
    return windows.get(f, "open")


# ---------------------------------------------------------------- motion: pose + position per frame

SWAY_HOLD_FRAMES = 3  # v7 perf: see idle_sway


def idle_sway(f):
    """Small held-pose weight shift so a planted character never looks frozen —
    layered on top of whatever pose (rest or gesture) is active that frame.

    v7 perf: this used to recompute from the exact frame `f` every call, which
    means its "torso" value (the only part of this dict render_body actually
    reads a rotation from — "hips_dy" doesn't match any key render_body looks
    up, so it's inert) was a distinct float on every single frame. pose_
    signature() rounds to 1 decimal, but at these sin() rates that still rarely
    repeats, so DisplayCache/PosedBodyCache — built specifically to skip
    render_body's full-canvas FK rotate for a repeated pose — almost never hit
    for either character: the listener holds the *same* gesture for an entire
    line, and would be free after the first frame if not for this. Holding the
    sway sample for SWAY_HOLD_FRAMES (125ms at 24fps) instead of resampling
    every frame is imperceptible at this amplitude (1-3px) and turns the
    listener into a near-total cache hit for the rest of the line."""
    bucket = (f // SWAY_HOLD_FRAMES) * SWAY_HOLD_FRAMES
    t = bucket / FPS
    return {"hips_dy": 3 * math.sin(t * 0.9), "torso": 1.2 * math.sin(t * 0.6 + 1.0)}


def add_pose(a, b):
    keys = set(a) | set(b)
    return {k: a.get(k, 0) + b.get(k, 0) for k in keys}


def emphasis_trigger_times(text, indices, duration):
    """Approximate wall-clock trigger times for episode.json's per-line `emphasis`
    word indices. Rhubarb gives us viseme timing, not word-boundary timing, so this
    spreads word indices linearly across the line's audio duration — not phoneme-
    accurate, but plenty close for a stylistic accent, not a lip-sync requirement."""
    if not indices:
        return []
    words = text.split()
    n = max(len(words) - 1, 1)
    return [duration * (min(i, len(words) - 1) / n) for i in indices]


def walk_step(state, target_x, speed=WALK_SPEED, cycle_frames=WALK_CYCLE_FRAMES):
    """Advance state["x"]/state["walk_phase"] one frame toward target_x. Returns the
    gait pose for this frame, or None once arrived (caller then holds position)."""
    dx = target_x - state["x"]
    if abs(dx) <= speed:
        state["x"] = target_x
        return None
    state["x"] += speed if dx > 0 else -speed
    state["walk_phase"] = (state["walk_phase"] + 1.0 / cycle_frames) % 1.0
    return rig_pose.walk_pose(state["walk_phase"])


def resolve_listener_motion(state, n_frames, listener=None):
    """Listener never walks — eases back to rest_stand at their home mark and
    holds it with idle sway, plus a slight held neck-turn toward the shared
    screen (v3: previously the listener just faced forward at rest for the
    entire line, which read as inert now that there's a real shared screen for
    them to plausibly be looking at along with the audience). Reuses the same
    neck angle already established by point_screen_L/R's gesture convention —
    Nate's screen-side is his frame-right (neck: 3, same as point_screen_R),
    Kai's is her frame-left (neck: -3, same as point_screen_L). (v4: these were
    inverted before the point_screen_R/L pose-content swap in rig_pose.py.)"""
    glance = {"neck": 3} if listener == "nate" else {"neck": -3} if listener == "kai" else {}
    poses = []
    for f in range(n_frames):
        ease_t = rig_pose.ease_in_out(min(f / GESTURE_EASE_FRAMES, 1.0))
        pose = rig_pose.interpolate_pose(state["pose"], rig_pose.REST_STAND, ease_t)
        pose = add_pose(pose, glance)
        poses.append(add_pose(pose, idle_sway(f)))
    state["pose"] = rig_pose.interpolate_pose(state["pose"], rig_pose.REST_STAND, 1.0)
    return poses


def resolve_speaker_motion(state, move, gesture, n_frames, emphasis_times=None):
    """The speaking anchor's pose + stage-x for every frame of their line: either a
    planted gesture (eased in, held — optionally punctuated by a harmonic bounce on
    specific words) or a walk beat (pace out from / back to their home mark),
    landing in the gesture pose once they arrive. Returns (poses, xs)."""
    target_gesture = rig_pose.get_pose(gesture)
    # v5: every named gesture except point_screen_R/L raises the same (right)
    # arm, which reads toward Kai's screen-side and away from Nate's (see
    # rig_pose.mirror_pose's docstring) — mirror it for Nate so "explain_chop"/
    # "count_one"/etc. don't wave away from the shared screen he's standing
    # next to. point_screen_R/L already name a specific frame side and are
    # selected correctly per speaker upstream, so they're left alone here.
    if state["name"] == "nate" and gesture not in ("point_screen_R", "point_screen_L"):
        target_gesture = rig_pose.mirror_pose(target_gesture)
    emphasis_times = emphasis_times or []

    if not move:
        poses = []
        for f in range(n_frames):
            ease_t = rig_pose.ease_in_out(min(f / GESTURE_EASE_FRAMES, 1.0))
            pose = rig_pose.interpolate_pose(state["pose"], target_gesture, ease_t)
            pose = add_pose(pose, idle_sway(f))
            if emphasis_times:
                t = f / FPS
                bounce = sum(rig_pose.emphasis_pulse(t - tt) for tt in emphasis_times)
                pose = add_pose(pose, {"hips_dy": bounce, "torso": bounce * 0.12,
                                        "leg_lower_L": bounce * 0.4, "leg_lower_R": bounce * 0.4})
            poses.append(pose)
        state["pose"] = rig_pose.interpolate_pose(state["pose"], target_gesture, 1.0)
        return poses, [state["x"]] * n_frames

    direction = 1 if state["name"] == "nate" else -1
    target_x = state["mark_x"] + direction * PACE_DISTANCE if move == "pace_out" else state["mark_x"]

    poses, xs = [], []
    for f in range(n_frames):
        walk_pose = walk_step(state, target_x)
        if walk_pose is not None:
            poses.append(walk_pose)
        else:
            poses.append(add_pose(target_gesture, idle_sway(f)))
        xs.append(state["x"])
    state["pose"] = poses[-1]
    return poses, xs


def resolve_camera(cam_state, target_fn, speaker_xs, n_frames):
    """This line's camera window per frame: a short push/zoom transition from the
    previous line's ending window into this line's target, then live tracking
    (target_fn re-evaluated against the speaker's current x every frame, so a
    walking speaker is actually followed).

    v8: dropped the v4 cited-line push-in (a continued zoom-in for the rest of
    a cited line's hold) — with the bigger screen and full-bleed contextual
    memes, the content is already legible at the base framing, and the
    zoom's shrinking window was clipping the top of a meme's own baked-in
    caption on longer holds (see build_meme_card / generate_screen_meme.py's
    STYLE_LOCK margin note)."""
    prev = cam_state.get("window")
    target0 = target_fn(speaker_xs[0])
    transition = [] if prev is None else camera.push_transition_windows(prev, target0, CAM_TRANSITION_FRAMES)

    windows = []
    for f in range(n_frames):
        windows.append(transition[f] if f < len(transition) else target_fn(speaker_xs[f]))
    cam_state["window"] = windows[-1]
    return windows


# ---------------------------------------------------------------- compositing

def paste_char(scene, display_img, center_x):
    scene.alpha_composite(display_img, (int(center_x) - camera.CHAR_DISPLAY_W // 2, camera.CHAR_TOP_Y))


def paste_screen(scene, content_img, center):
    box = camera.screen_box(center)
    scene.alpha_composite(content_img, (int(box[0]), int(box[1])))


def wrap_text(draw, text, font, max_width):
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
    if cur:
        lines.append(cur)
    return lines


def active_word_index(text, frame_index, duration):
    words = text.split()
    if not words or duration <= 0:
        return -1
    t = frame_index / FPS
    idx = int((t / duration) * len(words))
    return max(0, min(idx, len(words) - 1))


def word_index_to_time(text, word_index, duration):
    words = text.split()
    if not words or duration <= 0:
        return 0.0
    idx = max(0, min(int(word_index), len(words) - 1))
    return (idx / max(len(words), 1)) * duration


def screen_start_time(item, text, duration):
    if item.get("start_word") is not None:
        return word_index_to_time(text, item["start_word"], duration)
    try:
        return float(item.get("at", 0.0))
    except Exception:
        return 0.0


def active_screen_index(screen_sequence, frame_index):
    if not screen_sequence:
        return 0
    t = frame_index / FPS
    active = 0
    for i, item in enumerate(screen_sequence):
        if t >= item["at"]:
            active = i
        else:
            break
    return active


def layout_words(draw, words, font, max_width):
    lines, cur, width = [], [], 0
    space = draw.textlength(" ", font=font)
    for word_index, word in words:
        ww = draw.textlength(word, font=font)
        next_width = ww if not cur else width + space + ww
        if cur and next_width > max_width:
            lines.append(cur)
            cur, width = [(word_index, word, ww)], ww
        else:
            cur.append((word_index, word, ww))
            width = next_width
    if cur:
        lines.append(cur)
    return lines


def draw_highlighted_words(draw, xy, text, font, max_width, active_idx, max_lines, color, highlight_color):
    x0, y = xy
    words = [(i, w) for i, w in enumerate(text.split())]
    lines = layout_words(draw, words, font, max_width)[:max_lines]
    line_h = int(font.size * 1.32)
    space = draw.textlength(" ", font=font)
    for line in lines:
        x = x0
        for word_index, word, ww in line:
            fill = highlight_color if word_index == active_idx else color
            if word_index == active_idx:
                pad_x, pad_y = 5, 3
                draw.rounded_rectangle(
                    (x - pad_x, y - pad_y, x + ww + pad_x, y + font.size + pad_y),
                    radius=5,
                    fill=highlight_color[:3] + (52,),
                )
            draw.text((x, y), word, font=font, fill=fill)
            x += ww + space
        y += line_h


def draw_brand_pill(draw, render_format, fonts):
    if render_format == "reel":
        # v12: the caption bar this used to sit just above is gone (see
        # build_line_overlay) — simple bottom-right corner now, same row as
        # the footer.
        box = (816, DELIVER_H - 92, 1036, DELIVER_H - 44)
        font = fonts["tag"]
    else:
        # v6: was top-left (60,46)-(320,92) — the shared screen can land on
        # either side of frame depending on who's speaking (camera favors
        # whoever's talking), so a fixed top-left mark clipped screen content
        # (a chart or meme's own corner) on whichever half it happened to
        # land on that line. This sits in the gap between where the screen's
        # bottom edge lands in a typical close crop (~y820, see
        # build_popup_overlay's note) and the caption bar (y888) — clear of
        # the screen on either side, every line.
        box = (1600, 828, 1860, 874)
        font = fonts["tag"]
    draw.rounded_rectangle(box, radius=10, fill=(8, 10, 18, 210), outline=stage.CYAN + (210,), width=2)
    draw.text((box[0] + 16, box[1] + 10), BRAND_TEXT.upper(), font=font, fill=stage.CYAN + (255,))


def fit_font(draw, text, font, max_width, min_size=24):
    try:
        size = font.size
    except AttributeError:
        return font
    while draw.textlength(text, font=font) > max_width and size > min_size:
        size -= 2
        font = font.font_variant(size=size)
    return font


def build_line_overlay(episode_title, speaker, text, cite_domains, fonts, render_format, frame_index, duration):
    """Lower-third caption bar, drawn at delivery resolution after the camera crop
    (it's a fixed on-screen graphic, not part of the set) — same geometry as v1,
    now deliberately overlaying the lower legs of an open-floor full-body shot,
    same as a real broadcast lower-third would."""
    layer = Image.new("RGBA", (DELIVER_W, DELIVER_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    color = TAG_COLOR[speaker]
    active_idx = active_word_index(text, frame_index, duration)
    draw_brand_pill(d, render_format, fonts)

    if render_format == "reel":
        # v12: dropped the karaoke-style caption bar (bar/tag/highlighted
        # words/source ticker) entirely for reel, by request — audio-first,
        # no burned-in dialogue text. Just the brand pill (drawn above) and a
        # small footer near the bottom; nothing left to fight the character
        # crop for space, so both get simple, low-risk positions.
        footer = f"{BRAND_TEXT} / HIGHER THINKING / {episode_title}"
        footer_font = fit_font(d, footer, fonts["footer"], DELIVER_W - 100, min_size=14)
        d.text((44, DELIVER_H - 46), footer, font=footer_font, fill=(210, 222, 240, 220))
        return layer

    bar = (60, 888, 1860, 1012)
    d.rounded_rectangle(bar, radius=16, fill=(8, 6, 16, 195), outline=color + (200,), width=2)

    tag_box = (84, 906, 246, 950)
    d.rounded_rectangle(tag_box, radius=10, fill=color + (255,))
    d.text((tag_box[0] + 16, tag_box[1] + 8), speaker.upper(), font=fonts["tag"], fill=(10, 8, 16, 255))

    draw_highlighted_words(
        d, (270, 902), text, fonts["caption"], 1550,
        active_idx, 2, (240, 245, 250, 255), stage.AMBER + (255,),
    )

    if cite_domains:
        src_text = "SOURCE: " + ", ".join(cite_domains)
        d.text((1860 - d.textlength(src_text, font=fonts["ticker"]), 986), src_text,
               font=fonts["ticker"], fill=stage.AMBER + (235,), anchor="ra")

    footer = f"{BRAND_TEXT}  ·  HIGHER THINKING  ·  {episode_title}"
    d.text((60, 1032), footer, font=fonts["footer"], fill=(180, 190, 210, 190))
    return layer


def build_popup_overlay(line, speaker, fonts, frame_index, render_format):
    popup = line.get("popup")
    if not popup:
        return None
    if isinstance(popup, str):
        headline, sub = popup, ""
    else:
        headline = popup.get("headline") or popup.get("text") or ""
        sub = popup.get("subhead") or popup.get("sub") or ""
    if not headline:
        return None

    layer = Image.new("RGBA", (DELIVER_W, DELIVER_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    color = TAG_COLOR[speaker]
    pulse = 1.0 + 0.035 * math.sin(frame_index * 0.55)
    if render_format == "reel":
        box_w = int((DELIVER_W - 120) * pulse)
        cx = DELIVER_W // 2
        top = 250
        box = (cx - box_w // 2, top, cx + box_w // 2, top + 240)
        d.rounded_rectangle(box, radius=26, fill=(8, 10, 18, 224), outline=color + (235,), width=4)
        d.line([(box[0] + 28, box[1] + 28), (box[2] - 28, box[1] + 28)], fill=stage.AMBER + (220,), width=5)
        hfont = fit_font(d, headline.upper(), fonts["popup_big"], box_w - 80, min_size=38)
        lines = wrap_text(d, headline.upper(), hfont, box_w - 80)[:2]
        y = top + 62
        for ln in lines:
            tw = d.textlength(ln, font=hfont)
            d.text((cx - tw / 2, y), ln, font=hfont, fill=(248, 252, 255, 255))
            y += 58
        if sub:
            sfont = fit_font(d, sub, fonts["popup_small"], box_w - 80, min_size=24)
            sw = d.textlength(sub, font=sfont)
            d.text((cx - sw / 2, top + 184), sub, font=sfont, fill=color + (235,))
        return layer

    # v3: repositioned + centered from the old fixed top-right box (1120,118)-
    # (1810,302), which was fine when nothing else lived in that quadrant — but
    # the shared screen (v3's whole point) now regularly occupies the upper
    # frame in both anchors' shots, on either side depending on who's speaking.
    # This band (roughly y=650-820) sits below where the screen's bottom edge
    # lands and above the caption bar in both a Nate-favoring and Kai-favoring
    # crop, so centering horizontally avoids the screen regardless of which
    # side it's on this line.
    box_w, box_h = 900, 170
    cx = DELIVER_W // 2
    top = 650
    box = (cx - box_w // 2, top, cx + box_w // 2, top + box_h)
    d.rounded_rectangle(box, radius=18, fill=(8, 10, 18, 224), outline=color + (235,), width=3)
    hfont = fit_font(d, headline.upper(), fonts["popup_mid"], box_w - 80, min_size=26)
    lines = wrap_text(d, headline.upper(), hfont, box_w - 80)[:2]
    y = top + 30
    for ln in lines:
        tw = d.textlength(ln, font=hfont)
        d.text((cx - tw / 2, y), ln, font=hfont, fill=(248, 252, 255, 255))
        y += 44
    if sub:
        sw = d.textlength(sub, font=fonts["ticker"])
        d.text((cx - sw / 2, top + box_h - 38), sub, font=fonts["ticker"], fill=color + (235,))
    return layer


def render_backdrop(w, h):
    """Standalone branded backdrop for the outro card — a clean vector wash
    instead of a crop of the live character stage.

    v5: render_cta_segment used to crop camera.wide_shot() (both anchors + the
    shared screen prop) for its background. Nothing composites screen content
    onto the shared screen during the CTA (there's no line driving it), so
    that crop put the screen's empty bezel — a dead, unlit monitor outline —
    right above the actual CTA card. The anchors that far apart also forced a
    tall 16:9 window that couldn't crop the bezel out no matter how the shot
    was framed (see the geometry note in the v5 changelog): the screen sits at
    head height between two marks 1800px apart, so any wide two-shot at this
    aspect ratio reaches that band regardless of what's in the bbox union.
    Giving the outro its own backdrop sidesteps that geometry entirely, lets
    the card take up most of the frame, and stays correct if the stage layout
    (marks, screen size) ever changes."""
    img = Image.new("RGB", (w, h), (10, 6, 22))
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([w * 0.5 - w * 0.36, h * 0.5 - h * 0.42, w * 0.5 + w * 0.36, h * 0.5 + h * 0.42],
               fill=stage.CYAN + (46,))
    glow = glow.filter(ImageFilter.GaussianBlur(int(min(w, h) * 0.12)))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")

    d = ImageDraw.Draw(img, "RGBA")
    vp = (w // 2, int(h * 0.1))
    for i in range(15):
        t = i / 14
        x_bottom = int(-w * 0.4 + t * w * 1.8)
        d.line([vp, (x_bottom, h)], fill=stage.CYAN + (60,), width=1)
    for j in range(1, 10):
        t = (j / 9) ** 1.6
        y = int(h * 0.1 + t * h * 0.95)
        a = int(26 + 70 * t)
        d.line([(0, y), (w, y)], fill=stage.MAGENTA + (min(a, 110),), width=1)
    return img


def build_cta_overlay(fonts, render_format, frame_index, cta_url, has_meme=False):
    """Names the brand + show explicitly and prints the real,
    clickable-as-typed URL this episode points to (see cta_url_for()).

    v5: enlarged + recentered the card now that it isn't sharing the frame
    with the stage/screen (see render_backdrop), and fixed the header
    layout — the amber divider was drawn only 24px below the brand-tagline
    text's baseline, too close for that font's ~32px line height, so the rule
    sliced straight through the tagline's descenders. Brand line, divider,
    title, and URL each now get their own clear vertical band.

    v10: `has_meme` shrinks and drops the card so it sits below an outro meme
    card instead of centered in the full frame — see render_cta_segment."""
    layer = Image.new("RGBA", (DELIVER_W, DELIVER_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    pulse = 1.0 + 0.025 * math.sin(frame_index * 0.45)
    display_url = cta_url.replace("https://", "").replace("http://", "")
    if render_format == "reel":
        box_w = int((DELIVER_W - 96) * pulse)
        cx = DELIVER_W // 2
        # v12: was DELIVER_H-480 (1440) — paired with the meme card sitting
        # up near the top (60-680), that dumped all the leftover vertical
        # space into one big gap between the two cards instead of balanced
        # margins. 1290 centers this card + the meme card above it as one
        # group, with equal ~330px margins top and bottom of the frame.
        cy = 1290 if has_meme else DELIVER_H // 2
        half_h = 300 if has_meme else 420
        box = (cx - box_w // 2, cy - half_h, cx + box_w // 2, cy + half_h)
        title_font = fonts["popup_big"].font_variant(size=48)
        brand_font = fonts["popup_small"].font_variant(size=26)
        url_font = fonts["popup_small"]
    else:
        box_w = int(1500 * pulse)
        cx = DELIVER_W // 2
        cy = 800 if has_meme else DELIVER_H // 2
        half_h = 240 if has_meme else 300
        box = (cx - box_w // 2, cy - half_h, cx + box_w // 2, cy + half_h)
        title_font = fonts["popup_mid"]
        brand_font = fonts["popup_small"].font_variant(size=26)
        url_font = fonts["popup_small"]
    box_w_actual = box[2] - box[0]
    d.rounded_rectangle(box, radius=28, fill=(8, 10, 18, 236), outline=stage.CYAN + (250,), width=5)

    brand = f"{BRAND_TEXT} — RESEARCH. AUTOMATE. SIMULATE."
    bfont = fit_font(d, brand, brand_font, box_w_actual - 80, min_size=18)
    bw = d.textlength(brand, font=bfont)
    brand_y = box[1] + 44
    d.text((cx - bw / 2, brand_y), brand, font=bfont, fill=stage.AMBER + (235,))

    line_y = brand_y + bfont.size + 26
    d.line([(box[0] + 40, line_y), (box[2] - 40, line_y)], fill=stage.AMBER + (200,), width=4)

    title = "MORE AT BOT THAT LYFE"
    tfont = fit_font(d, title, title_font, box_w_actual - 80, min_size=32)
    tw = d.textlength(title, font=tfont)
    title_y = line_y + 44
    d.text((cx - tw / 2, title_y), title, font=tfont, fill=(248, 252, 255, 255))

    ufont = fit_font(d, display_url, url_font, box_w_actual - 80, min_size=18)
    uw = d.textlength(display_url, font=ufont)
    d.text((cx - uw / 2, box[3] - 90), display_url, font=ufont, fill=stage.CYAN + (255,))
    return layer


def load_fonts():
    return {
        "tag": ImageFont.truetype(FONT_DIR + "Arial Black.ttf", 22),
        "caption": ImageFont.truetype(FONT_DIR + "Arial Bold.ttf", 32),
        "ticker": ImageFont.truetype(FONT_DIR + "Arial Bold.ttf", 18),
        "footer": ImageFont.truetype(FONT_DIR + "Arial.ttf", 20),
        "popup_big": ImageFont.truetype(FONT_DIR + "Arial Black.ttf", 58),
        "popup_mid": ImageFont.truetype(FONT_DIR + "Arial Black.ttf", 38),
        "popup_small": ImageFont.truetype(FONT_DIR + "Arial Bold.ttf", 32),
        "intro_wide": ImageFont.truetype(FONT_DIR + "Arial Black.ttf", 68),
        "intro_reel": ImageFont.truetype(FONT_DIR + "Arial Black.ttf", 64),
        "screen": screen_graphics._fonts(),
    }


def domain_of(url):
    return urllib.parse.urlparse(url).netloc.replace("www.", "")


# ---------------------------------------------------------------- line rendering

def render_line(ep, line, rigs, caches, stage_bg, fonts, out_dir, rng, states, cam_state, render_format):
    n = line["n"]
    speaker = line["speaker"]
    listener = "kai" if speaker == "nate" else "nate"
    mood = line.get("mood", "neutral")

    audio_dir = out_dir / "audio"
    wav_path = audio_dir / f"line{n:02d}.wav"
    tsv_path = audio_dir / f"line{n:02d}.tsv"
    line_mp4 = out_dir / f"line{n:02d}.mp4"
    print(f"  line {n:2d} [{speaker:4s}] synthesizing...")
    synth_line(speaker, line["text"], wav_path)
    cues = rhubarb_sync(wav_path, tsv_path)
    duration = cues[-1][0]
    n_frames = max(int(duration * FPS) + 1, 1)

    render_meta_path = line_mp4.with_suffix(".render.json")
    render_meta = {
        "n": n,
        "speaker": speaker,
        "text": line["text"],
        "format": render_format,
        "deliver_w": DELIVER_W,
        "deliver_h": DELIVER_H,
        "audio_meta": json.loads(wav_path.with_suffix(".voice.json").read_text()) if wav_path.with_suffix(".voice.json").exists() else None,
        "frame_count": n_frames,
        "video_only": True,
        # v5: hash the parts of the line spec that actually change the render
        # (gesture/screen/popup/mood/move/emphasis/cite) directly, instead of
        # relying on a manually-bumped render_version to catch every future
        # content edit. Before this, editing only a line's `screen` or
        # `gesture` in episode.json without touching its `text` reported a
        # stale cache hit and silently kept the old render — which is exactly
        # what happened switching lines 3/8 off the cover-image screen and
        # fixing line 4/6's gestures in this same pass.
        "line_spec": {k: line.get(k) for k in
                      ("gesture", "screen", "screens", "popup", "mood", "move", "emphasis", "cite")},
        "background_meme": background_cache_key(ep),
        # v11 bump: reel's screen-panel layout, character-crop aspect, and
        # caption-bar position all changed in overlay-drawing code that isn't
        # part of line_spec above — without this, every reel line would
        # report a stale cache hit and keep the old (torso-overlapping)
        # layout.
        "render_version": 13,
    }
    if line_mp4.exists() and render_meta_path.exists():
        try:
            if json.loads(render_meta_path.read_text()) == render_meta:
                print(f"  line {n:2d} [{speaker:4s}] render cache hit: {line_mp4.name}")
                mux_wav = audio_dir / f"line{n:02d}_mixed.wav" if line.get("cite") else wav_path
                if line.get("cite") and not mux_wav.exists():
                    mix_in_ding(wav_path, mux_wav)
                return line_mp4, mux_wav
        except Exception:
            pass

    cites = line.get("cite", [])
    domains = sorted({domain_of(s["url"]) for s in ep.get("sources", []) if s["id"] in cites})
    cited = bool(domains)

    gesture = line.get("gesture")
    if not gesture:
        gesture = ("point_screen_R" if speaker == "nate" else "point_screen_L") if cited else "rest_stand"
    move = line.get("move")

    emphasis_times = emphasis_trigger_times(line["text"], line.get("emphasis", []), duration)

    print(f"  line {n:2d} [{speaker:4s}] rendering {n_frames} frames "
          f"(gesture={gesture}, move={move}, cited={cited}, emphasis={line.get('emphasis', [])})...")

    speaker_poses, speaker_xs = resolve_speaker_motion(
        states[speaker], move, gesture, n_frames, emphasis_times)
    listener_poses = resolve_listener_motion(states[listener], n_frames, listener=listener)

    hold_half = mood == "halflid"
    speaker_windows = {} if hold_half else blink_windows(n_frames, FPS, rng)
    listener_windows = blink_windows(n_frames, FPS, rng)
    brow_up = mood == "brows_up"

    # v3: ONE shared screen driven by the current line, regardless of which
    # anchor is speaking — replaces the old nate_screen/kai_screen dual state,
    # which reset the *non-speaking* anchor's screen to a standby placeholder
    # every single frame (see camera.py's v3 docstring for why that was also a
    # framing dead end, not just a state bug). There's now exactly one screen
    # to keep correct instead of two independently-reset ones.
    screen_sequence = screen_graphics.screen_sequence_for_line(
        ep, line, TAG_COLOR[speaker], stage.SCREEN_W, stage.SCREEN_H, fonts["screen"], base_dir=out_dir)
    screen_sequence = sorted([
        {**item, "at": screen_start_time(item, line["text"], duration)}
        for item in screen_sequence
    ], key=lambda item: item["at"])
    if screen_sequence:
        screen_sequence[0]["at"] = 0.0

    walking = bool(move)
    if render_format == "reel":
        target_fn = lambda x: camera.portrait_cam(x, walking)
    else:
        target_fn = (lambda x: camera.nate_cam(x, walking)) if speaker == "nate" else (
            lambda x: camera.kai_cam(x, walking))
    cam_windows = resolve_camera(cam_state, target_fn, speaker_xs, n_frames)

    # v11/v13: reel's screen panel — see camera.py's REEL_PANEL_H note.
    # A line may now have a `screens[]` timeline, so cache the fitted panel
    # for each beat and switch inside the line.
    if render_format == "reel":
        # v12: top margin pulled down from 40 to 100 — sat too close to the
        # very top edge before.
        panel_box = (40, 100, camera.REEL_W - 40, camera.REEL_PANEL_H - 40)
        for item in screen_sequence:
            item["panel_img"] = screen_graphics.fit_image_to_box(
                item["image"], panel_box[2] - panel_box[0], panel_box[3] - panel_box[1])

    mux_wav = wav_path
    if domains:
        mux_wav = audio_dir / f"line{n:02d}_mixed.wav"
        mix_in_ding(wav_path, mux_wav)

    frame_dir = out_dir / "frames" / f"line{n:02d}"
    frame_dir.mkdir(parents=True, exist_ok=True)
    for old_frame in frame_dir.glob("f*.png"):
        old_frame.unlink()
    ci = 0
    for f in range(n_frames):
        t = f / FPS
        while ci + 1 < len(cues) and cues[ci + 1][0] <= t:
            ci += 1
        viseme = cues[ci][1]
        if viseme == "neutral" and mood == "smile":
            viseme = "smile"

        scene = stage_bg.copy()

        sp_eye = eye_state_at(f, speaker_windows, force_half=hold_half)
        sp_body = caches[speaker].get(speaker_poses[f], viseme, sp_eye, brow_up)
        paste_char(scene, sp_body, speaker_xs[f])

        li_eye = eye_state_at(f, listener_windows)
        li_body = caches[listener].get(listener_poses[f], "neutral", li_eye, False)
        paste_char(scene, li_body, states[listener]["x"])

        active_screen = screen_sequence[active_screen_index(screen_sequence, f)]
        shared_screen = active_screen["image"]

        # v12: reel doesn't paste the screen onto the stage at all — the panel
        # gets its content straight from the in-memory `shared_screen` image
        # (built once above), not a stage crop. Pasting it onto the stage too
        # was the actual cause of the screen appearing a second time, cut off,
        # over on one side of the character shot: the character-only camera
        # window is centered tightly on the speaker, but its edge could still
        # clip the pasted screen (900px away on the wide stage) during a
        # push-transition or a walk beat, when the window briefly widens.
        # youtube still needs this — its whole composition IS character+
        # screen cropped together.
        if render_format != "reel":
            paste_screen(scene, shared_screen, stage.SHARED_SCREEN_CENTER)

        if render_format == "reel":
            # Character crop is framed against the space *below* the panel
            # (camera.PORTRAIT_CHAR_ASPECT, baked into portrait_cam's window
            # already) — render at that reduced height and paste below the
            # panel instead of stretching a full-height render into it.
            char_h = camera.REEL_H - camera.REEL_PANEL_H
            char_crop = camera.render_window(scene, cam_windows[f], camera.REEL_W, char_h).convert("RGBA")
            frame_img = Image.new("RGBA", (camera.REEL_W, camera.REEL_H), (10, 6, 22, 255))
            frame_img.alpha_composite(char_crop, (0, camera.REEL_PANEL_H))
            frame_img.alpha_composite(active_screen["panel_img"], (panel_box[0], panel_box[1]))
            pd = ImageDraw.Draw(frame_img)
            pd.rounded_rectangle(panel_box, radius=20, outline=TAG_COLOR[speaker] + (255,), width=4)
        else:
            frame_img = camera.render_window(scene, cam_windows[f], DELIVER_W, DELIVER_H).convert("RGBA")
        # v3 fix: build_popup_overlay() has always had a real youtube-format
        # layout (the box positioned at (1120, 118, 1810, 302)) sitting right
        # next to the reel-format one — this call was gated to reel-only, so
        # the youtube-format branch never ran. That's the actual reason the
        # 16:9 explainer videos never showed a popup.
        # v11: reel no longer calls this at all — the screen panel now covers
        # the job popups used to do for reel (the only visual at all, back
        # when reel had no screen), so a popup box would just be a second,
        # redundant callout stacked on top of the same information.
        popup = None if render_format == "reel" else build_popup_overlay(line, speaker, fonts, f, render_format)
        if popup:
            frame_img.alpha_composite(popup)
        overlay = build_line_overlay(ep["title"], speaker, line["text"], domains, fonts, render_format, f, duration)
        frame_img.alpha_composite(overlay)
        frame_img.convert("RGB").save(frame_dir / f"f{f:05d}.png", compress_level=1)

    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
        "-i", str(frame_dir / "f%05d.png"),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-an", str(line_mp4),
    ], check=True)
    render_meta_path.write_text(json.dumps(render_meta, indent=2) + "\n")
    return line_mp4, mux_wav


def render_intro_segment(ep, stage_bg, fonts, out_dir, render_format):
    duration = float(ep.get("intro_duration_sec", 2.2))
    n_frames = max(int(duration * FPS), 1)
    frame_dir = out_dir / "frames" / "intro"
    frame_dir.mkdir(parents=True, exist_ok=True)
    for old_frame in frame_dir.glob("f*.png"):
        old_frame.unlink()

    intro = ep.get("intro", {})
    kicker = intro.get("kicker", f"{BRAND_TEXT} / HIGHER THINKING")
    title = intro.get("title", ep["title"])
    # No default subhead — "Simulate before reality" was internal dev-slang that
    # leaked into shipped video; only show one if an episode explicitly asks for it.
    subhead = intro.get("subhead", "")

    # v10: an intro-specific contextual meme, same idea (and same generation
    # pipeline) as a dialogue line's screen — "automatically captivating"
    # instead of opening on bare title-card text. Optional: falls back to the
    # old text-only card when an episode doesn't set one.
    meme_spec = ep.get("intro_meme")
    meme_path = Path(meme_spec["path"]) if isinstance(meme_spec, dict) and meme_spec.get("path") else None
    meme_img = None
    if meme_path and meme_path.exists():
        if render_format == "reel":
            meme_img = screen_graphics.build_meme_card(str(meme_path), DELIVER_W - 128, 620)
        else:
            meme_img = screen_graphics.build_meme_card(str(meme_path), 1300, 560)

    # v11: reel used to show a live character crop (both anchors' marks,
    # bbox-unioned) behind the intro card, but that crop was framed for the
    # *full* frame height — with the meme card also overlaid at a fixed
    # position, the two fought over the same pixels (the meme sat right on
    # top of the anchors' heads). The intro is a 2.2s hook before anyone's
    # talking anyway; matching youtube's already-working intro (clean
    # backdrop, no live characters) sidesteps that entirely instead of
    # reserving yet another panel layout just for this one brief segment.
    backdrop = build_delivery_backdrop(ep, render_format)

    for f in range(n_frames):
        frame = backdrop.copy()
        d = ImageDraw.Draw(frame)
        t = f / max(n_frames - 1, 1)
        alpha = int(255 * min(1.0, t * 2.4))
        if render_format == "reel":
            box = (64, 900, DELIVER_W - 64, 1270) if meme_img else (64, 560, DELIVER_W - 64, 930)
            meme_box = (64, 200, DELIVER_W - 64, 820)
            title_w = DELIVER_W - 180
            y0 = box[1] + 60
            hfont = fonts["intro_reel"]
            sfont = fonts["popup_small"]
        else:
            box = (210, 650, DELIVER_W - 210, 1030) if meme_img else (210, 310, DELIVER_W - 210, 690)
            meme_box = (310, 40, 1610, 600)
            title_w = DELIVER_W - 520
            y0 = box[1] + 80
            hfont = fonts["intro_wide"]
            sfont = fonts["popup_mid"]

        if meme_img:
            mx, my = meme_box[0], meme_box[1]
            mw, mh = meme_box[2] - meme_box[0], meme_box[3] - meme_box[1]
            frame.alpha_composite(meme_img, (mx, my))
            d.rounded_rectangle((mx, my, mx + mw, my + mh), radius=20, outline=stage.CYAN + (alpha,), width=4)

        d.rounded_rectangle(box, radius=24, fill=(5, 6, 14, int(210 * t)), outline=stage.CYAN + (alpha,), width=4)
        d.line([(box[0] + 34, box[1] + 72), (box[2] - 34, box[1] + 72)], fill=stage.AMBER + (alpha,), width=5)
        d.text((box[0] + 34, box[1] + 30), kicker, font=fonts["tag"], fill=stage.AMBER + (alpha,))

        title_font = fit_font(d, title.upper(), hfont, title_w, min_size=42)
        for i, ln in enumerate(wrap_text(d, title.upper(), title_font, title_w)[:2]):
            tw = d.textlength(ln, font=title_font)
            d.text((DELIVER_W / 2 - tw / 2, y0 + i * int(title_font.size * 1.05)), ln,
                   font=title_font, fill=(248, 252, 255, alpha))

        if subhead:
            sub_font = fit_font(d, subhead, sfont, title_w, min_size=24)
            sw = d.textlength(subhead, font=sub_font)
            d.text((DELIVER_W / 2 - sw / 2, box[3] - 82), subhead, font=sub_font, fill=stage.CYAN + (alpha,))
        frame.convert("RGB").save(frame_dir / f"f{f:05d}.png", compress_level=1)

    silent = out_dir / "audio" / "intro_silence.wav"
    silent.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
        "-i", "anullsrc=channel_layout=stereo:sample_rate=44100", "-t", f"{duration:.3f}",
        str(silent),
    ], check=True)
    intro_mp4 = out_dir / "line00_intro.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
        "-i", str(frame_dir / "f%05d.png"),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-an", str(intro_mp4),
    ], check=True)
    return intro_mp4, silent


def render_cta_segment(ep, stage_bg, fonts, out_dir, render_format):
    duration = float(ep.get("cta_duration_sec", 2.8))
    n_frames = max(int(duration * FPS), 1)
    frame_dir = out_dir / "frames" / "cta"
    frame_dir.mkdir(parents=True, exist_ok=True)
    for old_frame in frame_dir.glob("f*.png"):
        old_frame.unlink()
    # v5: no longer a crop of the live stage (see render_backdrop's docstring
    # for why that always exposed the shared screen's empty bezel) — `stage_bg`
    # is unused here now but kept in the signature so this stays a drop-in call
    # alongside render_intro_segment.
    backdrop = build_delivery_backdrop(ep, render_format)
    cta_url = cta_url_for(ep)

    # v10: an outro-specific contextual meme, mirroring intro_meme — bookends
    # the episode on a joke instead of just a link card.
    meme_spec = ep.get("outro_meme")
    meme_path = Path(meme_spec["path"]) if isinstance(meme_spec, dict) and meme_spec.get("path") else None
    meme_img = None
    meme_box = None
    if meme_path and meme_path.exists():
        if render_format == "reel":
            # v12: was (64,60)-(...,680) — hugging the top with a big empty
            # gap before the CTA card lower down, all the leftover space
            # dumped in the middle. Meme card + CTA card are now centered as
            # one group, with the space distributed to equal margins at the
            # top and bottom instead (see build_cta_overlay's has_meme cy).
            meme_box = (64, 330, DELIVER_W - 64, 950)
        else:
            meme_box = (410, 40, 1510, 520)
        meme_img = screen_graphics.build_meme_card(
            str(meme_path), meme_box[2] - meme_box[0], meme_box[3] - meme_box[1])

    for f in range(n_frames):
        frame = backdrop.copy()
        if meme_img:
            frame.alpha_composite(meme_img, (meme_box[0], meme_box[1]))
            d = ImageDraw.Draw(frame)
            d.rounded_rectangle(meme_box, radius=20, outline=stage.CYAN + (250,), width=4)
        frame.alpha_composite(build_cta_overlay(fonts, render_format, f, cta_url, has_meme=bool(meme_img)))
        frame.convert("RGB").save(frame_dir / f"f{f:05d}.png", compress_level=1)
    silent = out_dir / "audio" / "cta_silence.wav"
    silent.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
        "-i", "anullsrc=channel_layout=stereo:sample_rate=44100", "-t", f"{duration:.3f}",
        str(silent),
    ], check=True)
    cta_mp4 = out_dir / "line99_cta.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
        "-i", str(frame_dir / "f%05d.png"),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-an", str(cta_mp4),
    ], check=True)
    return cta_mp4, silent


def initial_character_states():
    return {
        "nate": {"name": "nate", "x": float(stage.NATE_MARK_X), "mark_x": stage.NATE_MARK_X,
                 "walk_phase": 0.0, "pose": dict(rig_pose.REST_STAND)},
        "kai": {"name": "kai", "x": float(stage.KAI_MARK_X), "mark_x": stage.KAI_MARK_X,
                "walk_phase": 0.0, "pose": dict(rig_pose.REST_STAND)},
    }


def render_line_worker(payload):
    ep, line, out_dir_s, render_format, deliver_w, deliver_h = payload
    global DELIVER_W, DELIVER_H
    DELIVER_W, DELIVER_H = deliver_w, deliver_h
    out_dir = Path(out_dir_s)
    rng = random.Random(4200 + int(line["n"]))
    rigs = load_rigs()
    caches = {name: DisplayCache(rig) for name, rig in rigs.items()}
    stage_bg = build_stage_background(ep, render_format)
    fonts = load_fonts()
    return render_line(
        ep, line, rigs, caches, stage_bg, fonts, out_dir, rng,
        initial_character_states(), {"window": None}, render_format,
    )


def render_lines_parallel(ep, out_dir, render_format, workers):
    payloads = [(ep, line, str(out_dir), render_format, DELIVER_W, DELIVER_H) for line in ep["lines"]]
    results = {}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(render_line_worker, payload): payload[1]["n"] for payload in payloads}
        for future in as_completed(futures):
            n = futures[future]
            results[n] = future.result()
            print(f"  line {n:2d} finished in worker")
    return [results[line["n"]] for line in ep["lines"]]


# ---------------------------------------------------------------- music + sfx pass (unchanged from v1)

def score_episode(dialogue_cut_mp4, final_mp4):
    """Lay a ducked music bed + intro/outro stingers under the finished dialogue cut.
    The music sidechain-compresses against the dialogue track so it dips whenever
    Nate or Kai are talking and swells back up in the gaps."""
    duration = probe_duration(dialogue_cut_mp4)
    outro_dur = probe_duration(SFX_OUTRO)
    outro_delay_ms = max(int((duration - outro_dur) * 1000), 0)
    fade_out_start = max(duration - 1.5, 0.0)

    filter_complex = (
        f"[1:a]atrim=0:{duration},afade=t=in:st=0:d=1,"
        f"afade=t=out:st={fade_out_start}:d=1.5,volume=0.16[music_raw];"
        f"[music_raw][0:a]sidechaincompress=threshold=0.05:ratio=12:attack=5:release=300:makeup=1[music_duck];"
        f"[2:a]volume=0.9[introv];"
        f"[3:a]adelay={outro_delay_ms}|{outro_delay_ms},volume=0.85[outrov];"
        f"[0:a][music_duck][introv][outrov]amix=inputs=4:duration=first:normalize=0[mixed];"
        f"[mixed]alimiter=limit=0.95[aout]"
    )
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(dialogue_cut_mp4),
        "-stream_loop", "-1", "-t", str(duration + 2), "-i", str(MUSIC_BED),
        "-i", str(SFX_INTRO),
        "-i", str(SFX_OUTRO),
        "-filter_complex", filter_complex,
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-shortest",
        str(final_mp4),
    ], check=True)


# ---------------------------------------------------------------- main

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("episode_json")
    parser.add_argument("--format", choices=sorted(FORMAT_PRESETS), default=None)
    parser.add_argument("--workers", type=int, default=None,
                        help="parallel line render workers; defaults to RENDER_WORKERS or up to 4")
    args = parser.parse_args()
    ep_path = Path(args.episode_json).resolve()
    ep = json.loads(ep_path.read_text())
    render_format = args.format or ep.get("format", "youtube")
    if render_format not in FORMAT_PRESETS:
        sys.exit(f"unknown format {render_format!r}; expected one of {sorted(FORMAT_PRESETS)}")
    global DELIVER_W, DELIVER_H
    DELIVER_W, DELIVER_H = FORMAT_PRESETS[render_format]["size"]
    out_dir = ep_path.parent
    rng = random.Random(42)
    if args.workers is not None:
        workers = max(args.workers, 1)
    else:
        workers = int(os.environ.get("RENDER_WORKERS", "0") or 0)
        if workers <= 0:
            # v7 perf: was capped at 4 regardless of machine — on an 8-core M1
            # that left half the machine idle during the per-line render pool,
            # the single biggest wall-clock stage in the whole pipeline. Override
            # with RENDER_WORKERS= if a given machine's RAM makes fewer workers
            # the better trade (each worker loads its own copy of the rigs +
            # 3800x2300 stage canvas — ~100-150MB per worker, comfortably under
            # 16GB even at 8, but tune down on a lower-RAM machine).
            workers = max(1, min(len(ep.get("lines", [])), os.cpu_count() or 1))

    print("Ensuring stage + music/SFX assets exist...")
    ensure_stage_asset()
    ensure_audio_assets()

    # v9: stage timers — perf work on this pipeline had been guessing at where
    # wall-clock time actually goes (e.g. assuming the API-call phase was the
    # bottleneck, then uncapping its worker pools with no measured benefit).
    # Printing each stage's elapsed time turns that into something you can
    # actually see per run instead of re-guessing every time.
    t_gen_start = time.monotonic()

    # Voice generation (TTS) and screen-meme generation (image-gen) are
    # independent API calls driven by the same line list — no reason to do
    # them back-to-back when they can run at the same time.
    print("Generating voice lines + screen memes in parallel...")
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [
            pool.submit(ensure_batched_openai_voice, ep_path),
            pool.submit(ensure_batched_nate_voice, ep_path),
            pool.submit(ensure_batched_screen_memes, ep_path, render_format),
        ]
        for future in as_completed(futures):
            future.result()
    t_gen_done = time.monotonic()
    print(f"  [timing] voice+meme generation: {t_gen_done - t_gen_start:.1f}s")

    print("Loading character rigs...")
    rigs = load_rigs()
    caches = {name: DisplayCache(rig) for name, rig in rigs.items()}
    stage_bg = build_stage_background(ep, render_format)
    fonts = load_fonts()

    states = initial_character_states()
    cam_state = {"window": None}

    subprocess.run([sys.executable, str(REPO / "tools/validate_episode.py"), str(ep_path)], check=True)

    t_render_start = time.monotonic()
    print(f"Rendering {ep['episode']}: {ep['title']} ({render_format} {DELIVER_W}x{DELIVER_H}, workers={workers})")
    segments = [render_intro_segment(ep, stage_bg, fonts, out_dir, render_format)]
    if workers > 1:
        segments.extend(render_lines_parallel(ep, out_dir, render_format, workers))
    else:
        for line in ep["lines"]:
            segments.append(render_line(ep, line, rigs, caches, stage_bg, fonts, out_dir, rng, states, cam_state, render_format))
    segments.append(render_cta_segment(ep, stage_bg, fonts, out_dir, render_format))
    t_render_done = time.monotonic()
    print(f"  [timing] frame render + per-line encode: {t_render_done - t_render_start:.1f}s")

    print("Assembling dialogue cut...")
    line_mp4s = [video for video, _audio in segments]
    line_wavs = [audio for _video, audio in segments]
    concat_wavs = []
    concat_audio_dir = out_dir / "audio" / "concat"
    concat_audio_dir.mkdir(parents=True, exist_ok=True)
    for i, wav in enumerate(line_wavs):
        normalized = concat_audio_dir / f"seg{i:02d}.wav"
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
            "-ac", "2", "-ar", "44100", "-sample_fmt", "s16", str(normalized),
        ], check=True)
        concat_wavs.append(normalized)
    concat_txt = out_dir / "concat.txt"
    concat_txt.write_text("\n".join(f"file '{p.name}'" for p in line_mp4s) + "\n")
    audio_concat_txt = out_dir / "audio_concat.txt"
    audio_concat_txt.write_text("\n".join(f"file '{p.resolve()}'" for p in concat_wavs) + "\n")
    # v3 fix: these filenames didn't used to include render_format, so running
    # --format youtube then --format reel for the same episode.json (which the
    # daily pipeline always does — both deliverables are required) silently
    # overwrote the first format's finished files with the second's. Caught
    # this for real: rendered youtube, then reel, and the youtube _final.mp4
    # was gone, replaced by a 1080x1920 file under the same name.
    dialogue_cut = out_dir / f"{ep['episode']}_{render_format}_dialogue_cut.mp4"
    dialogue_audio = out_dir / f"{ep['episode']}_{render_format}_dialogue.wav"
    dialogue_video = out_dir / f"{ep['episode']}_{render_format}_video_only.mp4"
    # v7 perf: was a full libx264 re-encode of the entire concatenated video —
    # every segment feeding this (line_mp4/intro_mp4/cta_mp4) is already
    # libx264/yuv420p/same FPS+resolution, so the concat demuxer can just
    # copy the bytestreams instead of decoding and re-encoding the whole
    # video a second time (a bug caught in review, not something needed for
    # correctness — this was pure wasted encode time).
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
        "-i", str(concat_txt), "-map", "0:v", "-an",
        "-c:v", "copy", str(dialogue_video),
    ], check=True, cwd=out_dir)
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
        "-i", str(audio_concat_txt), "-c:a", "pcm_s16le", str(dialogue_audio),
    ], check=True)
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(dialogue_video), "-i", str(dialogue_audio),
        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-shortest", str(dialogue_cut),
    ], check=True)

    print("Scoring with music bed + stingers...")
    final_mp4 = out_dir / f"{ep['episode']}_{render_format}_final.mp4"
    score_episode(dialogue_cut, final_mp4)
    t_assemble_done = time.monotonic()
    print(f"  [timing] assemble + score: {t_assemble_done - t_render_done:.1f}s")
    print(f"  [timing] TOTAL: {t_assemble_done - t_gen_start:.1f}s "
          f"(generation {t_gen_done - t_gen_start:.1f}s / render {t_render_done - t_render_start:.1f}s / "
          f"assemble {t_assemble_done - t_render_done:.1f}s)")

    export_subdir = "youtube" if render_format == "youtube" else "reels"
    export_dir = OUTPUT_DIR / export_subdir
    export_dir.mkdir(parents=True, exist_ok=True)
    export_path = export_dir / f"{ep['episode']}.mp4"
    shutil.move(str(final_mp4), str(export_path))

    print(f"Done: {export_path}")


if __name__ == "__main__":
    main()
