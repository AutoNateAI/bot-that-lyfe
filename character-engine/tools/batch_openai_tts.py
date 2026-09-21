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


# v7: restructured onto OpenAI's own demonstrated labeled-field template for
# gpt-4o-mini-tts (Voice Affect / Tone / Pacing / Emotion / Emphasis /
# Pronunciation / Pauses — see the "Steering Text-to-Speech" cookbook example
# and the video-narration cookbook's full instructions block), instead of one
# joined freeform paragraph. OpenAI's own docs note the model follows
# concrete, labeled acting direction far more reliably than prose — and
# critically, a labeled Pronunciation field is the documented way to fix a
# specific word coming out wrong (e.g. "means" rendering audibly as "memes"),
# by naming the word and describing exactly how to say it, rather than just
# rewriting around the ambiguity in the spoken text.
#
# v6's baseline (kept, split across fields below): concrete character/acting
# direction — a person, a vibe, a relationship — beats abstract tone
# adjectives, which is what made both voices read flat/AI-generic even with
# instructions attached. Written as two people talking *to each other*, not
# two narrators each reading solo.

VOICE_AFFECT = {
    "nate": (
        "A sharp, curious young Black professional from the Midwest, cohosting a fast-moving "
        "research show with Kai. Talks like he's actually explaining something to a friend who "
        "asked a real question — not reading copy. Grounded, conversational baritone."
    ),
    "kai": (
        "A quick-witted, warm young Black woman cohosting a fast-moving research show with "
        "Nate. Talks like she's actually riffing with a friend — not narrating a script. "
        "Bright, playful alto with real editorial bite."
    ),
}

DEFAULT_PACING = {
    "nate": "Vary the pace — slow down and land the specific number or word, then pick back up.",
    "kai": "Quick, conversational back-and-forth energy — speed up on setup, land hard on the turn.",
}

# (tone, emotion) — split from the old single MOOD_INSTRUCTIONS sentence into
# OpenAI's separate Tone/Emotion fields.
MOOD_TONE_EMOTION = {
    "neutral": (
        "Clear, confident, and conversational — like mid-conversation, not a cold open.",
        "Even-keeled and genuinely present, not performative.",
    ),
    "smile": (
        "Warm and upbeat, audibly happy to be saying this.",
        "A real, warm smile coloring the voice.",
    ),
    "halflid": (
        "Dry and a little skeptical — one eyebrow up.",
        "Amused disbelief, like you're not fully buying it yet.",
    ),
    "brows_up": (
        "Caught off guard, leaning in.",
        "Genuine surprise and impressed energy — a small intake of breath before the line lands.",
    ),
}

DEFAULT_PRONUNCIATION = (
    "Clear, crisp enunciation — don't let word endings slur together or blur into a "
    "similar-sounding word."
)
DEFAULT_PAUSES = "Natural pause on em-dashes and right before a punchline turn."


def _resolve_emphasis(text, indices):
    """0-indexed word positions -> the actual words, so the instructions can name
    them explicitly (OpenAI's own example quotes the literal emphasized phrases
    rather than saying 'emphasize the important words')."""
    if not indices:
        return []
    words = text.split()
    out = []
    for i in indices:
        if isinstance(i, int) and 0 <= i < len(words):
            out.append(words[i].strip(".,!?—-\"'"))
    return out


def line_instructions(line):
    speaker = line["speaker"]
    mood = line.get("mood", "neutral")
    text = line.get("text", "")
    tone, emotion = MOOD_TONE_EMOTION.get(mood, MOOD_TONE_EMOTION["neutral"])

    pacing = str(line["pacing"]) if line.get("pacing") else DEFAULT_PACING[speaker]

    emphasis_words = _resolve_emphasis(text, line.get("emphasis"))
    if emphasis_words:
        quoted = ", ".join(f'"{w}"' for w in emphasis_words)
        emphasis = f"Really lean into: {quoted} — don't rush past them."
    else:
        emphasis = "Land any specific numbers and contrast words clearly; don't rush past them."

    pronunciation = DEFAULT_PRONUNCIATION
    if line.get("pronunciation"):
        pronunciation = f"{DEFAULT_PRONUNCIATION} {line['pronunciation']}"

    pauses = str(line["pauses"]) if line.get("pauses") else DEFAULT_PAUSES

    fields = [
        f"Voice Affect: {VOICE_AFFECT[speaker]}",
        f"Tone: {tone}",
        f"Pacing: {pacing}",
        f"Emotion: {emotion}",
        f"Emphasis: {emphasis}",
        f"Pronunciation: {pronunciation}",
        f"Pauses: {pauses}",
    ]

    popup = line.get("popup")
    if isinstance(popup, dict) and popup.get("headline"):
        fields.append(f"Context: this line is a visual beat titled '{popup['headline']}'.")
    if line.get("delivery"):
        fields.append(f"Additional direction: {line['delivery']}")
    if line.get("voice_instructions"):
        fields.append(f"Additional direction: {line['voice_instructions']}")

    return "\n\n".join(fields)


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
