#!/usr/bin/env python3
"""
tools/make_audio.py — synthesizes the show's music bed and SFX purely with ffmpeg's
own audio sources (sine/anoisesrc) and filters. No samples, no external audio, so
nothing to license: every sound is a mathematically generated tone or noise burst
shaped with envelopes (afade), tone-shaped (lowpass/highpass), and placed on a
timeline (adelay), then summed (amix).

Produces:
    assets/music/bed_loop.wav     - 8s synthwave-ish loop (bass, pad, kick, hat)
    assets/sfx/ding.wav           - citation / source-pop notification
    assets/sfx/intro_stinger.wav  - riser + chord stab, cold-open hit
    assets/sfx/outro_stinger.wav  - descending resolve, sign-off tail

Run: python3 tools/make_audio.py [--force]
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MUSIC_DIR = REPO / "assets/music"
SFX_DIR = REPO / "assets/sfx"
SR = 44100


def synth(events, total_duration, out_path):
    """events: list of dicts -
    type: 'sine'|'noise', freq (sine only), start, dur, vol, attack, release, filt (optional)
    """
    inputs = []
    filter_parts = []
    labels = []
    for i, e in enumerate(events):
        if e["type"] == "sine":
            inputs += ["-f", "lavfi", "-i",
                       f"sine=frequency={e['freq']}:duration={e['dur']}:sample_rate={SR}"]
        else:
            inputs += ["-f", "lavfi", "-i",
                       f"anoisesrc=color=white:duration={e['dur']}:sample_rate={SR}"]
        steps = []
        if e.get("filt"):
            steps.append(e["filt"])
        attack = e.get("attack", 0.01)
        release = e.get("release", 0.05)
        st_out = max(e["dur"] - release, 0.0)
        steps.append(f"afade=t=in:st=0:d={attack}")
        steps.append(f"afade=t=out:st={st_out:.4f}:d={release}")
        steps.append(f"volume={e['vol']}")
        delay_ms = int(e["start"] * 1000)
        if delay_ms > 0:
            steps.append(f"adelay={delay_ms}")
        label = f"e{i}"
        filter_parts.append(f"[{i}:a]" + ",".join(steps) + f"[{label}]")
        labels.append(f"[{label}]")

    mix = "".join(labels) + f"amix=inputs={len(events)}:duration=longest:normalize=0[mixraw]"
    tail = f"[mixraw]alimiter=limit=0.9,apad=whole_dur={total_duration},atrim=0:{total_duration}[aout]"
    filter_complex = ";".join(filter_parts) + ";" + mix + ";" + tail

    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error"] + inputs + [
        "-filter_complex", filter_complex, "-map", "[aout]", "-ac", "2", str(out_path),
    ]
    subprocess.run(cmd, check=True)
    print(f"wrote {out_path}")


def make_bed_loop():
    """8s loop, four 2s chords (Am-F-C-G): sub bass + soft pad triad + kick + hat."""
    chords = [
        (55.00, [220.00, 261.63, 329.63]),   # Am
        (43.65, [174.61, 220.00, 261.63]),   # F
        (65.41, [261.63, 329.63, 392.00]),   # C
        (49.00, [196.00, 246.94, 293.66]),   # G
    ]
    events = []
    for i, (bass_f, pad_freqs) in enumerate(chords):
        t0 = i * 2.0
        events.append({"type": "sine", "freq": bass_f, "start": t0, "dur": 1.9,
                        "vol": 0.35, "attack": 0.02, "release": 0.9, "filt": "lowpass=f=300"})
        for pf in pad_freqs:
            events.append({"type": "sine", "freq": pf, "start": t0, "dur": 1.95,
                            "vol": 0.07, "attack": 0.4, "release": 0.9, "filt": "lowpass=f=3500"})
        for kt in (t0, t0 + 1.0):
            events.append({"type": "sine", "freq": 58, "start": kt, "dur": 0.15,
                            "vol": 0.5, "attack": 0.005, "release": 0.13, "filt": "lowpass=f=150"})
        for ht in (t0 + 0.5, t0 + 1.5):
            events.append({"type": "noise", "start": ht, "dur": 0.05,
                            "vol": 0.12, "attack": 0.002, "release": 0.045, "filt": "highpass=f=6000"})
    synth(events, 8.0, MUSIC_DIR / "bed_loop.wav")


def make_ding():
    events = [
        {"type": "sine", "freq": 880.00, "start": 0.0, "dur": 0.18,
         "vol": 0.5, "attack": 0.005, "release": 0.15},
        {"type": "sine", "freq": 1108.73, "start": 0.02, "dur": 0.22,
         "vol": 0.4, "attack": 0.005, "release": 0.19},
    ]
    synth(events, 0.35, SFX_DIR / "ding.wav")


def make_intro_stinger():
    events = [
        {"type": "noise", "start": 0.00, "dur": 0.40, "vol": 0.06,
         "attack": 0.05, "release": 0.30, "filt": "highpass=f=1000"},
        {"type": "noise", "start": 0.35, "dur": 0.40, "vol": 0.08,
         "attack": 0.05, "release": 0.30, "filt": "highpass=f=2500"},
        {"type": "noise", "start": 0.70, "dur": 0.35, "vol": 0.10,
         "attack": 0.03, "release": 0.25, "filt": "highpass=f=5000"},
        {"type": "sine", "freq": 58, "start": 1.05, "dur": 0.25,
         "vol": 0.6, "attack": 0.005, "release": 0.22, "filt": "lowpass=f=150"},
        {"type": "sine", "freq": 220.00, "start": 1.05, "dur": 0.30, "vol": 0.25, "attack": 0.005, "release": 0.28},
        {"type": "sine", "freq": 261.63, "start": 1.05, "dur": 0.30, "vol": 0.20, "attack": 0.005, "release": 0.28},
        {"type": "sine", "freq": 329.63, "start": 1.05, "dur": 0.30, "vol": 0.20, "attack": 0.005, "release": 0.28},
    ]
    synth(events, 1.3, SFX_DIR / "intro_stinger.wav")


def make_outro_stinger():
    events = [
        {"type": "sine", "freq": 261.63, "start": 0.00, "dur": 0.35, "vol": 0.30, "attack": 0.01, "release": 0.30},
        {"type": "sine", "freq": 196.00, "start": 0.30, "dur": 0.40, "vol": 0.30, "attack": 0.01, "release": 0.35},
        {"type": "sine", "freq": 130.81, "start": 0.65, "dur": 0.90, "vol": 0.35,
         "attack": 0.02, "release": 0.80, "filt": "lowpass=f=800"},
        {"type": "sine", "freq": 65.41, "start": 0.70, "dur": 0.85, "vol": 0.30,
         "attack": 0.02, "release": 0.80, "filt": "lowpass=f=200"},
    ]
    synth(events, 1.6, SFX_DIR / "outro_stinger.wav")


TARGETS = {
    MUSIC_DIR / "bed_loop.wav": make_bed_loop,
    SFX_DIR / "ding.wav": make_ding,
    SFX_DIR / "intro_stinger.wav": make_intro_stinger,
    SFX_DIR / "outro_stinger.wav": make_outro_stinger,
}


def main():
    force = "--force" in sys.argv
    for path, fn in TARGETS.items():
        if force or not path.exists():
            fn()
        else:
            print(f"skip (exists): {path}")


if __name__ == "__main__":
    main()
