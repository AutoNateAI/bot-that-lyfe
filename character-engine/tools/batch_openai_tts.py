#!/usr/bin/env python3
"""Batch-generate missing OpenAI TTS WAVs for an episode manifest, in parallel."""
import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from say_openai_tts import MODEL, VOICE_BY_SPEAKER, post_speech  # noqa: E402


# v6: rewritten for actual character voice direction instead of generic
# "expressive baritone/alto" adjectives — gpt-4o-mini-tts follows specific,
# concrete acting direction (a person, a vibe, a relationship) far more
# reliably than abstract tone words, which is what was making both voices
# read as flat/AI-generic even with instructions attached. Written as two
# people talking *to each other*, not two narrators each reading solo.
BASE_INSTRUCTIONS = {
    "nate": (
        "You are Nate: a sharp, curious young Black professional from the Midwest, cohosting "
        "a fast-moving research show with Kai. You talk like you're actually explaining "
        "something to a friend who asked you a real question — not reading copy. Grounded, "
        "conversational baritone. Let real reactions show: a flicker of disbelief on a wild "
        "number, quiet confidence when you're citing a hard source, a dry half-smile on a "
        "joke. Vary your pace — slow down and land the specific number, then pick back up."
    ),
    "kai": (
        "You are Kai: a quick-witted, warm young Black woman cohosting a fast-moving research "
        "show with Nate. You talk like you're actually riffing with a friend — not narrating "
        "a script. Bright, playful alto with real editorial bite: a genuine little laugh or "
        "smirk when you're skeptical, real surprise when a number lands hard, a raised eyebrow "
        "you can hear in a pointed question. Never flat, never robotic — react like you mean it."
    ),
}

MOOD_INSTRUCTIONS = {
    "neutral": "Keep the delivery clear, confident, and conversational — like mid-conversation, not a cold open.",
    "smile": "Let a real, warm smile color the voice — audibly happy to be saying this, not performative.",
    "halflid": "Sound dry, amused, and a little skeptical — one eyebrow up, like you're not fully buying it yet.",
    "brows_up": "Sound genuinely caught off guard and impressed — a small intake of breath before the line lands.",
}


def line_instructions(line):
    speaker = line["speaker"]
    mood = line.get("mood", "neutral")
    parts = [BASE_INSTRUCTIONS[speaker], MOOD_INSTRUCTIONS.get(mood, MOOD_INSTRUCTIONS["neutral"])]
    if line.get("emphasis"):
        parts.append("Really lean into the key numbers and contrast words — don't rush past them.")
    popup = line.get("popup")
    if isinstance(popup, dict) and popup.get("headline"):
        parts.append(f"Treat this as a visual beat titled '{popup['headline']}'.")
    if line.get("delivery"):
        parts.append(str(line["delivery"]))
    if line.get("voice_instructions"):
        parts.append(str(line["voice_instructions"]))
    return " ".join(parts)


def expected_meta(line):
    speaker = line["speaker"]
    return {
        "speaker": speaker,
        "text": line["text"],
        "engine": "openai_tts",
        "model": MODEL,
        "voice": VOICE_BY_SPEAKER[speaker],
        "format": "wav_pcm_s16le_22050_mono",
        "instructions": line_instructions(line),
    }


def cache_valid(wav_path, meta_path, meta):
    if not wav_path.exists() or not meta_path.exists():
        return False
    try:
        return json.loads(meta_path.read_text()) == meta
    except Exception:
        return False


def probe_duration(wav_path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(wav_path)],
        capture_output=True, text=True,
    )
    return float(out.stdout.strip() or 0)


def generate_one(line, audio_dir):
    n = line["n"]
    wav_path = audio_dir / f"line{n:02d}.wav"
    meta_path = wav_path.with_suffix(".voice.json")
    meta = expected_meta(line)
    if cache_valid(wav_path, meta_path, meta):
        return f"openai voice cache hit: line{n:02d}.wav", False

    # Sanity check + retry: the Speech API occasionally returns a truncated
    # clip (silent success, no HTTP error — caught this for real on a
    # 40-word line that came back 0.3s long). Even brisk speech is well
    # under 5 words/sec, so a clip shorter than that for its word count is
    # broken, not just fast — retry a couple of times before giving up.
    word_count = len(line["text"].split())
    min_expected = max(0.6, word_count / 5.0)
    last_duration = None
    for attempt in range(3):
        post_speech(line["text"], meta["voice"], meta["instructions"], wav_path)
        last_duration = probe_duration(wav_path)
        if last_duration >= min_expected:
            break
    else:
        raise RuntimeError(
            f"line{n:02d}: TTS returned a {last_duration:.2f}s clip for a {word_count}-word "
            f"line (expected >= {min_expected:.2f}s) after {attempt + 1} attempts"
        )

    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    return f"openai voice generated: line{n:02d} {line['speaker']} {meta['voice']} ({last_duration:.1f}s)", True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("episode_json")
    # v9: was a flat default of 6 regardless of episode length, so a 14-line
    # episode ran its TTS batch in ~3 waves instead of 1 — these are network-
    # bound threads (mostly idle waiting on OpenAI, not competing for CPU), so
    # the natural cap is "one per line," not a fixed pool size. post_speech's
    # own retry-with-backoff on 429/5xx (see say_openai_tts.py) is what makes
    # firing all of them at once safe instead of just fast.
    parser.add_argument("--workers", type=int, default=None)
    args = parser.parse_args()
    ep_path = Path(args.episode_json).resolve()
    ep = json.loads(ep_path.read_text())
    audio_dir = ep_path.parent / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    workers = args.workers if args.workers else len(ep["lines"])
    generated = 0
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {pool.submit(generate_one, line, audio_dir): line for line in ep["lines"]}
        for future in as_completed(futures):
            line = futures[future]
            try:
                message, was_generated = future.result()
                print(message)
                generated += int(was_generated)
            except Exception as exc:
                sys.exit(f"line{line['n']:02d} FAILED: {exc}")

    print(f"OpenAI TTS batch complete: {generated} generated, {len(ep['lines']) - generated} cached")


if __name__ == "__main__":
    main()
