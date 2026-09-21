#!/usr/bin/env python3
"""
tools/rig_pose.py — forward-kinematics poser for the 23-layer character rig.

v1 only ever swapped mouth/eye/brow layers on top of a pre-flattened bust image
(assets/mouths/*/base_no_mouth.png). v2 poses the real skeleton: every part in
assets/<name>/parts/*.png lives on the identical 1000x1400 canvas as everything
else, and assets/<name>/pivots.json gives a documented rotation center for every
joint (see assets/<name>/RIGGING_GUIDE*.md — "Pivot points (rotation anchors)").

Posing a limb is: merge the child part onto the accumulated layer, then
Image.rotate(angle, center=pivot) the WHOLE accumulated layer around the next
joint out — repeated tip-to-root. Because every layer is already registered to
the same canvas, rotating the accumulated composite around a documented pivot
carries every already-merged descendant with it correctly, with no manual
translation math. This never crops, scales, or arbitrarily repositions an
individual part PNG — the only transform ever applied to a part is a rotation
about its own documented pivot, which is exactly what the pivot table was
authored for.

Bone hierarchy (from RIGGING_GUIDE*.md), and the back-to-front stacking order
render_body() honors:
    hips (root)
    ├── leg_upper_L -> leg_lower_L -> foot_L
    ├── leg_upper_R -> leg_lower_R -> foot_R
    └── torso
        ├── arm_upper_L -> arm_lower_L -> hand_L
        ├── arm_upper_R -> arm_lower_R -> hand_R
        └── neck -> head -> {eye_L/R, mouth, brow_L/R, hair_front}
    hair_back rides with neck/head but is the single backmost layer overall.

Known simplification: hair_back inherits hip sway + neck rotation but not torso
lean/twist (it's merged in at the hips level to keep it backmost, per the
documented z-order, rather than threaded through the torso subtree). Fine for
this rig's gesture vocabulary, which does its work with arms, not torso twist.

Z-order caveat: the documented order renders arms *behind* torso/hips/legs, which
is correct at rest (arms hang at the sides) but a raised/pointing arm can cross in
front of the torso silhouette. The pose library keeps gesture angles swinging
outward/up (away from the torso midline) specifically to avoid needing a z-override
for this; revisit per-pose if QA on a render shows clipping.
"""
import json
import math
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parent.parent
CANVAS = (1000, 1400)

# Tip-to-root order per limb chain — each entry's own pivot rotation is that
# joint's local angle; earlier (already-merged) entries ride along automatically.
CHAINS = {
    "leg_L": ["foot_L", "leg_lower_L", "leg_upper_L"],
    "leg_R": ["foot_R", "leg_lower_R", "leg_upper_R"],
    "arm_L": ["hand_L", "arm_lower_L", "arm_upper_L"],
    "arm_R": ["hand_R", "arm_lower_R", "arm_upper_R"],
}

PART_NAMES = [
    "hair_back", "hair_front", "head", "neck", "torso", "hips",
    "arm_upper_L", "arm_lower_L", "hand_L",
    "arm_upper_R", "arm_lower_R", "hand_R",
    "leg_upper_L", "leg_lower_L", "foot_L",
    "leg_upper_R", "leg_lower_R", "foot_R",
    "brow_L", "brow_R",
]


class Rig:
    """Loads one character's rig parts + pivots + mouth/eye state kits."""

    def __init__(self, name, mouths_dir):
        self.name = name
        parts_dir = REPO / f"assets/{name}/parts"
        states_dir = REPO / f"assets/{name}/states"
        self.pivots = json.loads((REPO / f"assets/{name}/pivots.json").read_text())

        self.parts = {p: Image.open(parts_dir / f"{p}.png").convert("RGBA") for p in PART_NAMES}
        self.eye_open = {"L": Image.open(parts_dir / "eye_L.png").convert("RGBA"),
                          "R": Image.open(parts_dir / "eye_R.png").convert("RGBA")}
        self.eye_half = {"L": Image.open(states_dir / "eye_L_half.png").convert("RGBA"),
                          "R": Image.open(states_dir / "eye_R_half.png").convert("RGBA")}
        self.eye_closed = {"L": Image.open(states_dir / "eye_L_closed.png").convert("RGBA"),
                            "R": Image.open(states_dir / "eye_R_closed.png").convert("RGBA")}
        self.mouths = {}
        for p in mouths_dir.glob("mouth_*.png"):
            key = p.stem[len("mouth_"):]
            self.mouths[key] = Image.open(p).convert("RGBA")

    def eyes(self, state):
        return {"half": self.eye_half, "closed": self.eye_closed}.get(state, self.eye_open)

    def pivot(self, part):
        x, y = self.pivots[part]
        return (float(x), float(y))


def _new():
    return Image.new("RGBA", CANVAS, (0, 0, 0, 0))


def _build_chain(rig, chain, pose):
    """Tip-to-root: merge part, then rotate the accumulated layer around that
    part's own pivot (that joint's local angle) before merging the next one out."""
    layer = _new()
    for part in chain:
        layer.alpha_composite(rig.parts[part])
        angle = pose.get(part, 0)
        if angle:
            layer = layer.rotate(angle, center=rig.pivot(part), resample=Image.BICUBIC)
    return layer


def render_body(rig, pose, viseme="neutral", eye_state="open", brow_up=False):
    """Full-body FK composite -> 1000x1400 RGBA, ready to be cropped/scaled onto
    the stage by the caller. `pose` is a flat dict of joint-angle deltas (degrees)
    from rest, keyed by part name, plus optional `hips_rot`, `hip_dx`, `hip_dy` for
    root lean/stepping/bobbing. Missing keys default to 0 (today's rest pose)."""
    eyes = rig.eyes(eye_state)
    brow_dy = -6 if brow_up else 0

    head_layer = _new()
    head_layer.alpha_composite(rig.parts["head"])
    head_layer.alpha_composite(eyes["L"])
    head_layer.alpha_composite(eyes["R"])
    head_layer.alpha_composite(rig.mouths.get(viseme, rig.mouths["neutral"]))
    head_layer.alpha_composite(rig.parts["brow_L"], (0, brow_dy))
    head_layer.alpha_composite(rig.parts["brow_R"], (0, brow_dy))
    head_layer.alpha_composite(rig.parts["hair_front"])
    head_angle = pose.get("head", 0)
    if head_angle:
        head_layer = head_layer.rotate(head_angle, center=rig.pivot("head"), resample=Image.BICUBIC)

    neck_head = _new()
    neck_head.alpha_composite(rig.parts["neck"])
    neck_head.alpha_composite(head_layer)
    neck_angle = pose.get("neck", 0)
    if neck_angle:
        neck_head = neck_head.rotate(neck_angle, center=rig.pivot("neck"), resample=Image.BICUBIC)

    # hair_back rides with neck/head (same rotation) but stays the backmost layer.
    hair_back = _new()
    hair_back.alpha_composite(rig.parts["hair_back"])
    if neck_angle:
        hair_back = hair_back.rotate(neck_angle, center=rig.pivot("neck"), resample=Image.BICUBIC)

    arm_L = _build_chain(rig, CHAINS["arm_L"], pose)
    arm_R = _build_chain(rig, CHAINS["arm_R"], pose)
    leg_L = _build_chain(rig, CHAINS["leg_L"], pose)
    leg_R = _build_chain(rig, CHAINS["leg_R"], pose)

    torso_subtree = _new()
    torso_subtree.alpha_composite(arm_L)
    torso_subtree.alpha_composite(arm_R)
    torso_subtree.alpha_composite(rig.parts["torso"])
    torso_subtree.alpha_composite(neck_head)
    torso_angle = pose.get("torso", 0)
    if torso_angle:
        torso_subtree = torso_subtree.rotate(torso_angle, center=rig.pivot("torso"), resample=Image.BICUBIC)

    body = _new()
    body.alpha_composite(hair_back)
    body.alpha_composite(leg_L)
    body.alpha_composite(leg_R)
    body.alpha_composite(rig.parts["hips"])
    body.alpha_composite(torso_subtree)
    hips_angle = pose.get("hips_rot", 0)
    if hips_angle:
        body = body.rotate(hips_angle, center=rig.pivot("hips"), resample=Image.BICUBIC)

    dx, dy = pose.get("hip_dx", 0), pose.get("hip_dy", 0)
    if dx or dy:
        shifted = _new()
        shifted.alpha_composite(body, (round(dx), round(dy)))
        body = shifted
    return body


def pose_signature(pose):
    return tuple(sorted((k, round(v, 1)) for k, v in pose.items() if v))


class PosedBodyCache:
    """Caches full render_body() output keyed by (pose, viseme, eye_state, brow_up).
    Doesn't help while a mouth is actively talking (viseme changes every frame),
    but collapses the idle listener (held pose, static neutral viseme, occasional
    blink) and any held speaking pose down to a handful of unique renders instead
    of one per frame."""

    def __init__(self, rig):
        self.rig = rig
        self._cache = {}

    def get(self, pose, viseme="neutral", eye_state="open", brow_up=False):
        key = (pose_signature(pose), viseme, eye_state, brow_up)
        img = self._cache.get(key)
        if img is None:
            img = render_body(self.rig, pose, viseme, eye_state, brow_up)
            self._cache[key] = img
        return img


def interpolate_pose(a, b, t):
    keys = set(a) | set(b)
    return {k: a.get(k, 0) + (b.get(k, 0) - a.get(k, 0)) * t for k in keys}


def ease_in_out(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


# --- Pose library: plain data, hand-tuned angles (degrees), verified by rendering
# stills to tools/tmp_pose_check/ and eyeballing them (see build notes). The rig's
# rest/T-pose (all zeros) has arms straight out horizontally — arm_upper_R: +90
# swings the arm down to hang at the side, arm_upper_R: -90 swings it straight up
# overhead (arm_upper_L mirrors: -90 down, +90 up). Every pose below is a *complete*
# dict (both arms explicit), not a delta on top of rest_stand, so interpolating from
# rest_stand to any gesture sweeps the resting arm smoothly rather than snapping it
# back to the T-pose. ---
REST_STAND = {"arm_upper_L": -90, "arm_upper_R": 90}

POSES = {
    "rest_stand": REST_STAND,
    # v4 fix: these two were swapped — rendered stills (tools/tmp_pose_check/
    # kai_point_screen_L.png etc.) showed "point_screen_L" raising the arm that
    # reads on the *frame-right* side and vice versa. A front-facing character's
    # own left arm swings up toward the viewer's right, so "point toward a
    # screen that's on my frame-right" (point_screen_R) has to raise arm_upper_L,
    # not arm_upper_R. Swapped the two dicts' contents so the names now match
    # what they visually point at; every call site (make_episode.py's default
    # gesture pick, episode.json's explicit "gesture" fields, the listener
    # glance) already assumed this frame-relative meaning, so nothing else
    # needed to change.
    "point_screen_R": {"arm_upper_R": 90, "arm_upper_L": 35, "arm_lower_L": 15, "neck": 3},
    "point_screen_L": {"arm_upper_L": -90, "arm_upper_R": -35, "arm_lower_R": -15, "neck": -3},
    "open_hands": {"arm_upper_L": 40, "arm_upper_R": -40, "arm_lower_L": 10, "arm_lower_R": -10},
    "explain_chop": {"arm_upper_L": -90, "arm_upper_R": 5, "arm_lower_R": -75},
    "count_one": {"arm_upper_L": -90, "arm_upper_R": -55, "arm_lower_R": -25},
    "shrug": {"arm_upper_L": 55, "arm_upper_R": -55, "arm_lower_L": -25, "arm_lower_R": 25, "neck": 3},
}


def get_pose(name):
    return POSES.get(name, REST_STAND)


_MIRROR_ARM_LEG_PAIRS = [
    ("arm_upper_L", "arm_upper_R"), ("arm_lower_L", "arm_lower_R"),
    ("leg_upper_L", "leg_upper_R"), ("leg_lower_L", "leg_lower_R"),
]
_MIRROR_SIGN_FLIP = ("neck", "torso", "hips_rot")


def mirror_pose(pose):
    """Left-right mirror of a pose dict: swap each L/R joint pair (negating the
    angle, since arm_upper_R: +90 hangs down but arm_upper_L: -90 hangs down —
    see the angle-convention comment above POSES) and flip the sign on
    turn/lean angles. A fully symmetric pose (rest_stand, shrug, open_hands)
    mirrors to itself; an asymmetric one (explain_chop, count_one) mirrors to
    the other arm.

    v5: every gesture in POSES *except* point_screen_R/L happens to raise the
    character's own right arm, which — for a front-facing character — reads on
    the audience's *left*. That's a coincidence of authoring, not something
    tied to anatomy, but it means every one of those gestures reads as
    gesturing toward Kai's screen-side (frame-left) and away from Nate's
    (frame-right, see make_stage.py's SHARED_SCREEN_CENTER). make_episode.py
    mirrors Nate's non-point_screen gestures with this so his generic
    emphasis beats don't wave away from the shared screen he's standing next
    to. point_screen_R/L are excluded at the call site — they already encode
    a specific frame side by name, and mirroring one turns it into the other."""
    mirrored = {k: v for k, v in pose.items() if k not in _MIRROR_SIGN_FLIP
                and k not in {p for pair in _MIRROR_ARM_LEG_PAIRS for p in pair}}
    for a, b in _MIRROR_ARM_LEG_PAIRS:
        if a in pose:
            mirrored[b] = -pose[a]
        if b in pose:
            mirrored[a] = -pose[b]
    for k in _MIRROR_SIGN_FLIP:
        if k in pose:
            mirrored[k] = -pose[k]
    return mirrored


# --- Walk cycle: procedural sine gait, not hand-authored keyframes. Loops cleanly
# at any cycle length, easy to scale for speed/stride via `stride`. ---
def walk_pose(phase, stride=1.0):
    """phase in [0, 1). Returns a pose dict for the leg/arm/hip articulation at
    that point in the gait cycle. Caller owns translating hip_dx across frames —
    this only returns the articulation + a vertical bob, not horizontal travel."""
    theta = phase * 2 * math.pi
    thigh_swing = 24 * stride
    knee_lift = 20 * stride
    arm_swing = 18 * stride
    bob = 9 * stride

    right_thigh = thigh_swing * math.sin(theta)
    left_thigh = -thigh_swing * math.sin(theta)
    right_knee = max(0.0, knee_lift * math.sin(theta - math.pi / 2))
    left_knee = max(0.0, knee_lift * math.sin(theta + math.pi / 2))
    # contralateral arm swing (opposite arm leads with the opposite leg), layered on
    # top of the resting hang (+90 R / -90 L — see POSES/REST_STAND above), not the
    # T-pose horizontal.
    right_arm = 90 + left_thigh * (arm_swing / thigh_swing)
    left_arm = -90 + right_thigh * (arm_swing / thigh_swing)
    hip_dy = -abs(bob * math.sin(2 * theta))
    torso_lean = 2.0 * stride

    return {
        "leg_upper_R": right_thigh, "leg_lower_R": right_knee,
        "leg_upper_L": left_thigh, "leg_lower_L": left_knee,
        "arm_upper_R": right_arm, "arm_upper_L": left_arm,
        "hip_dy": hip_dy, "torso": torso_lean,
    }


def walk_cycle_frames(n_frames, cycle_frames=16, stride=1.0):
    return [walk_pose((f % cycle_frames) / cycle_frames, stride) for f in range(n_frames)]


# --- Emphasis bounce: a damped-harmonic-oscillator accent for punching a specific
# word, layered on top of whatever pose is already active (see make_episode.py's
# resolve_speaker_motion, which triggers this from episode.json's `emphasis` field). ---
def emphasis_pulse(dt, amplitude=48.0, decay=8.0, freq=5.5):
    """0 before the trigger; a decaying cosine spring after it — a literal harmonic
    oscillator, not just a linear bounce, so it pops down and springs back through a
    couple of shrinking oscillations before settling within a few hundred ms.
    dt = seconds since the trigger (negative = hasn't happened yet this frame)."""
    if dt < 0:
        return 0.0
    return amplitude * math.exp(-decay * dt) * math.cos(2 * math.pi * freq * dt)


if __name__ == "__main__":
    # Smoke test: render rest + a couple of gesture poses for both characters to
    # tools/tmp_pose_check/ so they can be eyeballed before wiring into the pipeline.
    out_dir = REPO / "tools/tmp_pose_check"
    out_dir.mkdir(exist_ok=True)
    chars = {
        "nate": Rig("nate", REPO / "assets/mouths/male_mouths"),
        "kai": Rig("kai", REPO / "assets/mouths/female_mouths"),
    }
    test_poses = ["rest_stand", "point_screen_R", "point_screen_L", "open_hands", "shrug"]
    for name, rig in chars.items():
        for pose_name in test_poses:
            img = render_body(rig, get_pose(pose_name), viseme="neutral")
            img.convert("RGB").save(out_dir / f"{name}_{pose_name}.png")
        walk_img = render_body(rig, walk_pose(0.25), viseme="neutral")
        walk_img.convert("RGB").save(out_dir / f"{name}_walk_phase25.png")
    print(f"wrote smoke-test stills to {out_dir}")
