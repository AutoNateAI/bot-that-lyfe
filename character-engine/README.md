# character-engine

A 2D rigged-puppet video pipeline that turns a script (`episode.json`) into a
rendered Nate & Kai talk-show video: OpenAI TTS voices, Rhubarb lip-sync,
gpt-image contextual memes, and ffmpeg compositing — no editing software, no
manual animation.

Ported from an internal AutoNateAI project (`roblox-gamelab-2/apps/marketplace`)
and rebranded for Bot That Lyfe: the on-screen show name is "Higher Thinking",
the brand tag is "BTL", and the outro card defaults to linking `shop.botthatlyfe.com`.
The engine itself is unmodified — only branding text and the two Claude skills
that drive it changed. See `.claude/skills/nate-kai-video-director/SKILL.md`
and `.claude/skills/nate-kai-reel-director/SKILL.md` at the repo root for the
actual authoring/rendering workflow; this file is just environment setup.

## Setup

```bash
pip install -r character-engine/requirements.txt
```

Also needed on the machine, not installed via pip:

- **ffmpeg / ffprobe** on `PATH` (`brew install ffmpeg` on macOS).
- **Rhubarb Lip Sync** — already bundled at `tools/bin/rhubarb` (macOS x86_64
  binary, runs fine under Rosetta on Apple Silicon). Nothing to install.
- **`OPENAI_API_KEY`** — required for both TTS (`gpt-4o-mini-tts`) and the
  contextual meme/background images (`gpt-image`). Without
  `USE_OPENAI_TTS=true` set, voice synthesis silently falls back to macOS's
  built-in `say` command instead of erroring — see the skill docs' "Known
  gotchas" section.
- **`rclone`** with a `gdrive:` remote, only if you want the skills' final
  "sync to Drive" step. Optional — skip it if you don't need that.

## Quick check

Render something with zero API calls (uses the macOS `say` fallback voice and
skips meme generation) to confirm the pipeline itself works on a given
machine:

```bash
mkdir -p character-engine/episodes/smoke-test
cat > character-engine/episodes/smoke-test/episode.json <<'EOF'
{
  "episode": "smoke-test",
  "title": "Smoke Test",
  "lines": [
    { "n": 1, "speaker": "nate", "text": "Testing the pipeline." },
    { "n": 2, "speaker": "kai", "text": "If you can see this, it works." }
  ]
}
EOF
python3 character-engine/tools/validate_episode.py character-engine/episodes/smoke-test/episode.json
OPENAI_API_KEY=dummy python3 character-engine/tools/make_episode.py character-engine/episodes/smoke-test/episode.json --format youtube
```

(`OPENAI_API_KEY` is only read for meme generation here, and this episode has
no memes to generate, so a dummy value just clears an unconditional env check
— no real API call happens.) Output lands at
`character-engine/output/youtube/smoke-test.mp4`. Delete
`character-engine/episodes/smoke-test/` and `character-engine/output/` when
done — both are gitignored build artifacts.

## Layout

```
character-engine/
  tools/          render pipeline scripts + tools/bin/rhubarb
  lib/            shared rig math (rig.py)
  assets/         kai/, nate/ (rig layers), mouths/, sets/, music/, sfx/
  voices/         say.sh — TTS dispatch (OpenAI / macOS `say` fallback)
  episodes/       episode.json scripts (tracked) + render cache (gitignored)
  output/         finished .mp4s — youtube/ and reels/ (gitignored)
```

Not ported from the source project: the old ag-policy episode content
(different show, not applicable here), and `dance-lab/` (a separate
choreography experiment, unrelated to the Nate & Kai episode pipeline —
ask if you want that ported too).
