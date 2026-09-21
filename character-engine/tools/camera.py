#!/usr/bin/env python3
"""
tools/camera.py — camera-window math for the wide stage.

assets/sets/stage_wide.png is a virtual set much bigger than the delivered
1920x1080 frame. Every shot the audience sees is a 16:9 crop of it, scaled to
1920x1080. Speaker changes interpolate the crop window's center/size from the
old shot to the new one over a few frames (a simulated push) instead of v1's
dim/desaturate trick — replaced entirely in v2.

v3 (production-fork redesign): make_stage.py now bakes ONE shared screen
centered between the two anchor marks instead of one screen per anchor. That's
the actual fix for "the anchors are supposed to share a screen, camera cuts
between them, screen stays in shot" — nate_cam()/kai_cam() below both frame
against the SAME stage.SHARED_SCREEN_CENTER, so cutting from one to the other
is a real news-desk-style camera cut (favor whichever anchor is speaking) that
never drops the shared screen out of frame, and — because there's only one
screen now instead of two independently-reset mounts — there's no more state
for the non-speaking anchor's screen to go stale on (the old dual-mount bug
class this class of shot used to hit).

Two single-cam framings (v2.2, geometry updated for v3's shared screen):
- close (single_shot_close): head/torso + the shared screen — the shot for a
  planted line. Cropping to the upper body only (screen_mount's y is set at
  head/shoulder height in make_stage.py) keeps a tight medium shot instead of
  zooming out for a screen mounted far above the character.
- full (single_shot_full): the whole body, no screen — used while an anchor is
  walking (a leg-swing walk cycle needs legs in frame; a screen isn't the point
  of a walk beat).
wide_shot() (both anchors + the shared screen) is kept for a possible future
cold-open/establishing beat but isn't used per-line by camera_for_line.

Character placement constants live here (not in make_stage.py) because framing
and placement are the same concern: the camera has to know where a body is to
frame it.
"""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_stage as stage  # noqa: E402

DELIVER_W, DELIVER_H = 1920, 1080
ASPECT = DELIVER_W / DELIVER_H  # 16:9
PORTRAIT_ASPECT = 1080 / 1920

# Full-body character display size on the stage canvas (rig canvas is 1000x1400).
CHAR_DISPLAY_H = 1150
CHAR_DISPLAY_W = int(CHAR_DISPLAY_H * 1000 / 1400)
CHAR_TOP_Y = stage.FLOOR_Y - CHAR_DISPLAY_H

# Fraction of full character height the close single-cam crop uses — tall enough
# that every gesture pose's raised hand stays in frame (verified against
# rig_pose.POSES; the highest reach, a fully overhead arm, lands well within the
# top ~15% of the character). The crop's *actual* rendered window ends up taller
# than this fraction alone would suggest: the bbox is proportionally wide (it has
# to reach sideways to the screen), so the 16:9-aspect-derived window height has
# slack below the nominal boundary — raised to 0.8 so a walk beat's leg motion
# reads instead of being cropped at the waist, at no extra zoom-out cost (see
# camera.single_shot_close).
CHAR_UPPER_FRAC = 0.8

MARGIN = 1.08  # headroom multiplier applied to a shot's content bounding box


def char_box(center_x):
    """(left, top, right, bottom) of a full-body character centered at center_x."""
    return (center_x - CHAR_DISPLAY_W // 2, CHAR_TOP_Y,
            center_x + CHAR_DISPLAY_W // 2, CHAR_TOP_Y + CHAR_DISPLAY_H)


def char_upper_box(center_x, frac=CHAR_UPPER_FRAC):
    """(left, top, right, bottom) of just the head/torso portion, for the close
    single-cam + screen framing."""
    return (center_x - CHAR_DISPLAY_W // 2, CHAR_TOP_Y,
            center_x + CHAR_DISPLAY_W // 2, CHAR_TOP_Y + int(CHAR_DISPLAY_H * frac))


def screen_box(center):
    cx, cy = center
    return (cx - stage.SCREEN_W // 2, cy - stage.SCREEN_H // 2,
            cx + stage.SCREEN_W // 2, cy + stage.SCREEN_H // 2)


def _bbox_union(*boxes):
    xs0 = min(b[0] for b in boxes)
    ys0 = min(b[1] for b in boxes)
    xs1 = max(b[2] for b in boxes)
    ys1 = max(b[3] for b in boxes)
    return xs0, ys0, xs1, ys1


def _window_from_bbox(bbox, margin=MARGIN, aspect=ASPECT):
    """Smallest 16:9 window (center_x, center_y, width, height) that contains
    `bbox` with `margin` headroom, clamped so it doesn't run off the stage."""
    x0, y0, x1, y1 = bbox
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    bw, bh = (x1 - x0) * margin, (y1 - y0) * margin
    if bw / bh > aspect:
        w, h = bw, bw / aspect
    else:
        h, w = bh, bh * aspect
    # clamp center so the window stays inside the stage canvas
    half_w, half_h = w / 2, h / 2
    cx = min(max(cx, half_w), stage.W - half_w)
    cy = min(max(cy, half_h), stage.H - half_h)
    return {"center_x": cx, "center_y": cy, "width": w, "height": h}


def wide_shot():
    """Both anchors, full body, the shared screen between them — cold open /
    establishing shot."""
    bbox = _bbox_union(
        char_box(stage.NATE_MARK_X), char_box(stage.KAI_MARK_X),
        screen_box(stage.SHARED_SCREEN_CENTER),
    )
    return _window_from_bbox(bbox, margin=1.05)


def single_shot_full(char_center_x):
    """Full body, no screen. Not used by camera_for_line by default (see
    single_shot_close) — kept as a building block for anything that explicitly
    wants a screen-free full-body frame."""
    return _window_from_bbox(char_box(char_center_x), margin=1.15)


def single_shot_close(char_center_x, screen_center):
    """Head/torso + the shared screen — the shot for every planted OR walking
    line, favoring whichever anchor is speaking. The window is recomputed from
    the *live* bbox every frame (see resolve_camera in make_episode.py, which
    calls this per frame during a walk), so as an anchor steps away from their
    mark the union bbox grows and the window widens just enough to keep both
    them and the screen in frame, then tightens back up once they're planted
    again. Because the screen is now centered *between* the two marks (v3)
    rather than mounted right next to the speaker, this crop's far edge often
    catches a sliver of the other anchor at frame edge — kept deliberately,
    it reads as "we're at the same desk," not an isolated solo shot."""
    bbox = _bbox_union(char_upper_box(char_center_x), screen_box(screen_center))
    # v4: tightened from 1.15 — paired with the bigger SCREEN_W/H (make_stage.py)
    # and resolve_camera's cited-line push-in (make_episode.py), a looser margin
    # here just left more dead grid floor around a shot that's supposed to read
    # as "close enough to actually see the screen."
    return _window_from_bbox(bbox, margin=1.06)


# --- Reel (9:16) shared-screen panel ---------------------------------------
# v11: reel used to skip the shared screen entirely (see the old
# single_shot_portrait docstring below this comment's predecessor) because
# cropping character+screen together from the wide stage forces a distant,
# tiny-subject wide shot — the screen sits ~900px outboard of each mark, way
# more lateral reach than a narrow portrait frame can afford without zooming
# out past the point either subject reads. Fix: stop trying to capture both
# in one stage-space crop. The screen becomes a fixed delivery-space panel
# (make_episode.py composites it directly, same technique as the caption bar
# or brand pill — not a stage crop at all), and the character crop below is
# framed against the *remaining* vertical space instead of the full frame.
REEL_W, REEL_H = 1080, 1920
REEL_PANEL_H = 760  # delivery-space px reserved for the screen panel, top of frame
PORTRAIT_CHAR_ASPECT = REEL_W / (REEL_H - REEL_PANEL_H)


def single_shot_portrait(char_center_x, full_body=False):
    """Character-only crop for reel, framed against the space *below* the
    screen panel (REEL_PANEL_H) instead of the full 1920 frame height.
    Caller renders this at (REEL_W, REEL_H - REEL_PANEL_H) and pastes it at
    y=REEL_PANEL_H, then composites the screen panel separately on top.

    v13: PORTRAIT_CHAR_ASPECT is much closer to square than a true portrait
    crop, so the resulting window is wide enough (~950-1000 stage-px) that
    centering it exactly on a mark can still reach into the shared screen's
    stage-space footprint (SHARED_SCREEN_CENTER +/- SCREEN_W/2) — even though
    reel never pastes per-line content there, the *baked-in bezel border* is
    part of the static stage art and bled through at the frame edge. Clamp
    the window away from the screen's bounds entirely: push it further from
    the mark, on the side away from the screen, rather than trying to shrink
    it (shrinking would zoom in past what the character needs)."""
    box = char_box(char_center_x) if full_body else char_upper_box(char_center_x, frac=0.92)
    window = _window_from_bbox(box, margin=1.08, aspect=PORTRAIT_CHAR_ASPECT)
    half_w = window["width"] / 2
    screen_left = stage.SHARED_SCREEN_CENTER[0] - stage.SCREEN_W / 2
    screen_right = stage.SHARED_SCREEN_CENTER[0] + stage.SCREEN_W / 2
    if char_center_x >= stage.SHARED_SCREEN_CENTER[0]:
        window["center_x"] = max(window["center_x"], screen_right + half_w)
    else:
        window["center_x"] = min(window["center_x"], screen_left - half_w)
    return window


def nate_cam(char_center_x=None, walking=False):
    x = char_center_x if char_center_x is not None else stage.NATE_MARK_X
    return single_shot_close(x, stage.SHARED_SCREEN_CENTER)


def kai_cam(char_center_x=None, walking=False):
    x = char_center_x if char_center_x is not None else stage.KAI_MARK_X
    return single_shot_close(x, stage.SHARED_SCREEN_CENTER)


def camera_for_line(speaker, char_center_x=None, walking=False):
    """The shot for a given line: close single-cam favoring the speaker + the
    one shared screen, tracked live — same framing style whether they're
    planted or walking (see single_shot_close). `walking` is accepted for
    call-site compatibility but no longer changes the framing; kept in the
    signature in case a future shot style wants to know."""
    return nate_cam(char_center_x, walking) if speaker == "nate" else kai_cam(char_center_x, walking)


def portrait_cam(char_center_x, walking=False):
    return single_shot_portrait(char_center_x, full_body=walking)


def interpolate_window(a, b, t):
    return {k: a[k] + (b[k] - a[k]) * t for k in a}


def ease_in_out(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def push_transition_windows(prev_win, next_win, n_frames, overshoot=1.08):
    """A few frames of eased interpolation from prev_win to next_win, with a brief
    zoom-in overshoot at the midpoint for a simulated camera push rather than a
    flat pan — the user's 'quick push/zoom' choice over a hard cut."""
    frames = []
    for i in range(n_frames):
        t = ease_in_out((i + 1) / n_frames)
        win = interpolate_window(prev_win, next_win, t)
        # overshoot peaks at t=0.5, back to 1.0 at both ends
        punch = 1.0 - (1.0 - overshoot) * (1.0 - abs(2 * t - 1))
        win = {**win, "width": win["width"] / punch, "height": win["height"] / punch}
        frames.append(win)
    return frames


def render_window(scene, window, deliver_w=DELIVER_W, deliver_h=DELIVER_H):
    """Crop `window` (a dict from wide_shot/single_shot/interpolate_window) out of
    `scene` (the fully-composited stage RGBA image) and scale to DELIVER_W x
    DELIVER_H."""
    cx, cy, w, h = window["center_x"], window["center_y"], window["width"], window["height"]
    box = (int(cx - w / 2), int(cy - h / 2), int(cx + w / 2), int(cy + h / 2))
    return scene.crop(box).resize((deliver_w, deliver_h), Image.LANCZOS)


if __name__ == "__main__":
    # Smoke test: composite both characters (rest pose) onto the stage and render
    # the wide shot + both single-cam shots so framing can be eyeballed before
    # wiring into make_episode.py.
    from rig_pose import Rig, render_body, get_pose

    REPO = Path(__file__).resolve().parent.parent
    scene = Image.open(REPO / "assets/sets/stage_wide.png").convert("RGBA")
    nate = Rig("nate", REPO / "assets/mouths/male_mouths")
    kai = Rig("kai", REPO / "assets/mouths/female_mouths")
    nate_body = render_body(nate, get_pose("rest_stand"), viseme="neutral")
    kai_body = render_body(kai, get_pose("point_screen_L"), viseme="Aa")

    def paste_char(scene, body, center_x):
        disp = body.resize((CHAR_DISPLAY_W, CHAR_DISPLAY_H), Image.LANCZOS)
        scene.alpha_composite(disp, (center_x - CHAR_DISPLAY_W // 2, CHAR_TOP_Y))

    paste_char(scene, nate_body, stage.NATE_MARK_X)
    paste_char(scene, kai_body, stage.KAI_MARK_X)

    out_dir = REPO / "tools/tmp_pose_check"
    out_dir.mkdir(exist_ok=True)
    render_window(scene, wide_shot()).convert("RGB").save(out_dir / "cam_wide.png")
    render_window(scene, nate_cam()).convert("RGB").save(out_dir / "cam_nate_close.png")
    render_window(scene, kai_cam()).convert("RGB").save(out_dir / "cam_kai_close.png")
    render_window(scene, nate_cam(walking=True)).convert("RGB").save(out_dir / "cam_nate_walk.png")
    print(f"wrote camera test stills to {out_dir}")
