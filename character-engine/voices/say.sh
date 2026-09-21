#!/usr/bin/env bash
# voices/say.sh <nate|kai> "text" <out.wav>
#
# PLACEHOLDER VOICES: no cloning tool is installed on this system yet, so this wraps
# macOS's built-in `say` command with two distinct system voices as stand-ins for
# Nate and Kai. The contract below (speaker, text, out.wav path) is the only thing
# the rest of the pipeline knows about — swap in a real cloned voice later by editing
# only this file; nothing downstream (rhubarb, render_talking_head.py, make_episode.py)
# needs to change.
#
# Nate  -> Daniel (en_GB), a clear, natural, already-installed compact voice.
# Kai   -> Samantha (en_US), the standard natural US female voice.
# Rate is nudged slightly per character so they don't sound identical in cadence.
set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "usage: say.sh <nate|kai> \"text\" out.wav" >&2
  exit 1
fi

speaker="$1"
text="$2"
out="$3"

mkdir -p "$(dirname "$out")"

if [[ "${USE_OPENAI_TTS:-false}" =~ ^(1|true|TRUE|yes|YES|on|ON)$ ]]; then
  python3 "$(dirname "$0")/../tools/say_openai_tts.py" "$speaker" "$text" "$out"
  exit $?
fi

case "$speaker" in
  nate)
    if [ "${USE_CHATTERBOX_NATE:-false}" = "true" ]; then
      CHATTERBOX_PY="/Users/autonate/code/autonateai-roblox-gamelab/.venv/chatterbox/bin/python"
      if [ -x "$CHATTERBOX_PY" ] && "$CHATTERBOX_PY" "$(dirname "$0")/../tools/say_chatterbox.py" "$text" "$out"; then
        exit 0
      fi
      echo "warning: Chatterbox Nate failed; falling back to macOS Daniel" >&2
    fi
    say -v Daniel --rate=185 -o "$out" --data-format=LEI16@22050 "$text"
    ;;
  kai)
    say -v Samantha --rate=195 -o "$out" --data-format=LEI16@22050 "$text"
    ;;
  *)
    echo "unknown speaker: $speaker (expected nate|kai)" >&2
    exit 1
    ;;
esac
