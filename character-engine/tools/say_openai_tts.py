#!/usr/bin/env python3
"""Generate one WAV line with OpenAI Speech API."""
import argparse
import json
import os
import sys
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


MODEL = os.environ.get("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
VOICE_BY_SPEAKER = {
    "nate": os.environ.get("OPENAI_TTS_NATE_VOICE", "cedar"),
    "kai": os.environ.get("OPENAI_TTS_KAI_VOICE", "marin"),
}

RETRYABLE_HTTP_CODES = {429, 500, 502, 503, 529}


def post_speech(text, voice, instructions, out_path, max_attempts=5):
    """v9: raises RuntimeError instead of calling sys.exit() on failure — this
    runs inside a ThreadPoolExecutor worker (batch_openai_tts.py), and
    sys.exit() there gets wrapped into a SystemExit that propagates straight
    through the batch's own `except Exception` and kills the whole process
    instead of just failing that one line. Also retries with backoff on
    429/5xx — batch_openai_tts.py's worker count now scales to the episode's
    line count instead of a fixed cap (see its own changelog), so a burst of
    simultaneous requests hitting a rate limit is an expected, recoverable
    case now, not a rare one."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for OpenAI TTS")

    payload = {
        "model": MODEL,
        "voice": voice,
        "input": text,
        "instructions": instructions,
        "response_format": "wav",
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/speech",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    delay = 1.5
    raw = None
    for attempt in range(max_attempts):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                raw = resp.read()
            break
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            if exc.code in RETRYABLE_HTTP_CODES and attempt < max_attempts - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise RuntimeError(f"OpenAI TTS HTTP {exc.code}: {detail}") from None
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        tmp.write(raw)
    try:
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp_path),
            "-ac", "1", "-ar", "22050", "-sample_fmt", "s16", str(out_path),
        ], check=True)
    finally:
        tmp_path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("speaker", choices=sorted(VOICE_BY_SPEAKER))
    parser.add_argument("text")
    parser.add_argument("wav_path")
    parser.add_argument("--instructions", default="")
    args = parser.parse_args()
    try:
        post_speech(args.text, VOICE_BY_SPEAKER[args.speaker], args.instructions, Path(args.wav_path))
    except RuntimeError as exc:
        sys.exit(str(exc))


if __name__ == "__main__":
    main()
