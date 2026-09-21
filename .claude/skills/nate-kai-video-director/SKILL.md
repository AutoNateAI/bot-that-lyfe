---
name: nate-kai-video-director
description: Produce a Nate & Kai YouTube video (16:9) using the character-engine pipeline (episode.json -> OpenAI TTS + contextual gpt-image memes -> rendered/composited video). Use this whenever the user asks to make a YouTube video, video explainer, or campus/CS-culture video and mentions "Nate and Kai" / "the video" / "the channel". Standalone scripted episodes — not derived from a published article. Does NOT cover 9:16 / Reels / TikTok-format output — that's a separate skill built on top of this one's episode.json structure.
---

# Nate & Kai Video Director

Turns a topic into a two-host talk-show video: Nate and Kai, standing on a neon open-floor set, trading lines and pointing at a shared screen that shows real numbers, memes, and campus/CS culture content. Everything lives under `character-engine/` in this repo.

If the user asks for a Nate & Kai YouTube video "about" / "on" / "for" a topic, this is the skill — don't freehand a new approach, the pipeline below already solves voice, pacing, on-screen visuals, and rendering.

**Scope**: 16:9 YouTube format only (`--format youtube`). The codebase also has a `--format reel` (9:16) path, but it is *not* production-ready — camera framing for portrait is unfinished and untested end-to-end. A separate skill will cover 9:16 once that work is done. Don't attempt a finished reel deliverable with this skill.

## 0. Prerequisites

- `OPENAI_API_KEY` must be set (used for both TTS and meme image generation).
- **Always render with `USE_OPENAI_TTS=true` in the environment.** Without it, the pipeline silently falls back to macOS's built-in `say` command (a generic British-sounding male voice and a robotic-sounding female voice) instead of the actual expressive OpenAI voices. This is not a visible error — the render finishes fine, it just sounds wrong. Always double check this env var is set before rendering.

## 1. Pick the topic and nail down the real facts

These are standalone scripts — there's no source article to read first. Before writing anything, pin down:

- The single topic (a CS concept, a campus/builder-culture observation, a BTL product/drop, a "things nobody tells CS students" angle, a research/automation idea tied to AutoNateAI/BTL's "Research. Automate. Simulate." identity).
- Any real numbers, stats, or claims the script will lean on. **If a line states a fact or number, it needs to actually be true** — don't invent a statistic to make a joke land. If you don't have a verified number, write the joke around a *relatable mechanism* instead (the all-nighter before a deadline, the gap between a LeetCode grind and a real interview, the vibe-coded final project that somehow works) rather than a fabricated stat.
- If the episode does lean on a couple of verified facts, capture them in `sources[]` (step 3) so `cite` can reference them — this is optional and most episodes won't need it, unlike the article-driven model this pipeline originally shipped with.

## 2. Tone

**Default: high-voltage informal parody, heavy cussing, metaphor-first punchlines** (standing house style for every Nate & Kai video, carried over from this pipeline's original build — keep it unless the user asks for something more restrained). The target is a live-wire stand-up rhythm the whole way through, not just one hot opening line:

- Every line needs comic voltage: a reversal, metaphor, simile, callback, tag, or incredulous turn. If a line only explains, rewrite it until it teaches and hits.
- **Hooks must be A-material and start like an interruption.** Open with a dramatic conversational hit — "Yoooo, guess what the fuck," "Broooo, this shit wild," or "My ninja, you won't believe this shit:" — then immediately collide a common assumption, promise, or hype claim (a bootcamp ad, a "just automate it" hot take, career-fair hype, a professor's syllabus promise, a LinkedIn flex) with the real, uglier mechanism underneath it. Do not start with "Nate..." or "Kai..." unless it's part of a sharper interruption. No soft openers, no throat-clearing, no generic "today we're talking about."
- **Cuss heavily and by default.** Fuck/shit/damn/hell should be frequent, rhythmic, and connected to the point. Don't sprinkle profanity randomly — make it part of the timing.
- Use hard, everyday metaphors that explain the system: a broken build as a bomb nobody defused, a recruiter's promise as a red button nobody wants to press, a group project as a group chat nobody responds in, a production incident as a kitchen fire at 2am.
- **Story before bit-stack.** Every video needs a clean narrative spine, not just adjacent jokes. A viewer should be able to retell it in one sentence: "the hype/promise hit reality, reality hit the actual workflow, and here's who's left holding it." If a joke doesn't move that story forward, cut or rewrite it.
- **Core plot engine, not literal questions.** Before writing dialogue, compress the topic into a hidden sequence: setup -> the hype/promise -> what it glosses over -> the real mechanism -> where it bites someone -> the twist/complication -> the payoff or unresolved tension. Don't make the hosts mechanically walk through those beats as Q&A; turn the sequence into scenes, jokes, callbacks, and handoffs.
- For a full YouTube cut, build multiple chapters with the same logic: each chapter opens with a concrete conflict/claim, explains the mechanism, lands the metaphor, then hands off to the next chapter.
- Pick one recurring object/metaphor per episode and stay with it long enough for the audience to track the plot (the receipt, the red button, the group chat, the deploy button, the whiteboard) — avoid switching metaphors every line unless the new one clearly escalates the same story.
- If a line is long or does multiple teaching jobs, don't leave one static screen up for the whole thing. Either split it into shorter back-and-forth lines or use timed `screens[]` so the visual changes with the spoken turns. This matters most on hooks, mechanism explanations, and chapter openers.
- Do not use the n-word. If the intended casual phrasing needs that beat, write "my ninja" instead.
- Build any joke that leans on a real number/stat/claim from something actually true (step 1) — the punchline should land on the real fact, never a made-up one.
- Keep the heat up for the whole video. A YouTube cut can breathe more than a reel, but it should still have a joke engine in every segment and callbacks that make viewers stay for the next beat.
- Put delivery direction in `voice_instructions`, and put the real punchline directly in `text` so it survives TTS.

Whichever tone, use `voice_instructions` (step 5) to steer TTS delivery per-episode.

## 3. Write `episode.json`

Create `character-engine/episodes/<slug>/episode.json` (pick a slug that describes the topic).

```json
{
  "episode": "<slug>",
  "title": "<video title>",
  "cta_url": "https://botthatlyfe.com/",
  "runtime_target_sec": 60,
  "background_meme": { "path": "<abs path>/background.png", "prompt": "<full-video contextual background prompt>" },
  "intro_meme": { "path": "<abs path>/screen-memes/intro.png", "prompt": "<meme prompt>" },
  "outro_meme": { "path": "<abs path>/screen-memes/outro.png", "prompt": "<meme prompt>" },
  "sources": [
    { "id": "s1", "url": "<real source url>", "fact": "<the exact sourced fact>" }
  ],
  "lines": [
    {
      "n": 1,
      "speaker": "kai",
      "mood": "smile",
      "text": "...",
      "cite": ["s1"],
      "gesture": "point_screen_L",
      "move": "pace_out",
      "emphasis": [4, 5],
      "popup": { "headline": "...", "subhead": "..." },
      "screen": { "type": "meme", "path": "<abs path>/screen-memes/line01.png", "prompt": "<meme prompt>" },
      "voice_instructions": "<optional per-episode delivery override>"
    }
  ]
}
```

Field reference:

- `episode`: slug, used for output filenames and paths.
- `cta_url` *(optional)*: where the outro card sends viewers. Defaults to `https://botthatlyfe.com/` if omitted — **set it explicitly** whenever the episode is promoting something specific (a drop, a product page, a campus page, the Discord).
- `sources[]` *(optional)*: `id` / `url` / `fact`, only needed if a line's `cite` references a real, verified stat. Most standalone episodes will have few or none — don't force it.
- `intro_meme` / `outro_meme` *(optional but recommended)*: `{prompt, path}` — a contextual meme bookending the episode. If omitted, intro/outro fall back to a plain text card (still works, just less captivating).
- `background_meme` *(recommended for every video)*: `{prompt, path}` — one contextual full-video background generated by the same image pipeline and held behind the hosts for the entire episode. The renderer sizes it to the delivery format (`1920x1080` for YouTube, `1080x1920` for reel), then blends it with the native neon/grid set so it feels richer without fighting the speakers or screen panel. Write the prompt as a low-distraction environment, not another joke card: no text, no logos, no real public figures, no busy center detail, darker edges, clear room for hosts. Think campus/dorm/dev-lab/hackathon environments, not the old pipeline's agricultural-documentary imagery.
- Per line:
  - `n`: 1-indexed, sequential, no gaps.
  - `speaker`: `"nate"` or `"kai"`.
  - `text`: the spoken line. Keep it as short as the tone calls for (step 2).
  - `mood`: `neutral` | `smile` | `halflid` (dry/skeptical) | `brows_up` (surprised/impressed). Drives both facial expression and TTS delivery instructions.
  - `cite`: array of source `id`s. Non-empty triggers a citation "ding" sfx and defaults the gesture to pointing at the screen. Leave empty/omitted on most lines — this pipeline no longer assumes every line is sourced from an article.
  - `gesture` *(optional)*: see the gesture reference below. If omitted: `point_screen_R`/`point_screen_L` (Nate/Kai respectively) when `cite` is non-empty, else `rest_stand`.
  - `move` *(optional)*: `"pace_out"` (steps away from home mark — good for an opening line) or `"pace_back"`.
  - `emphasis` *(optional)*: 0-indexed word positions in `text` to vocally/physically emphasize.
  - `popup` *(optional)*: `{headline, subhead}` — a small secondary callout box, separate from the shared screen, for hammering one stat.
  - `screen` *(optional)*: see step 4. If omitted entirely and `cite` is empty, the screen shows a branded standby card — **never** the line's own caption text.
  - `screens` *(optional)*: timed intra-line screen sequence for longer lines. Each item can be `{ "start_word": 8, "screen": { ... } }` or `{ "at": 2.4, "screen": { ... } }`; use it when a single spoken line needs multiple visuals to stay entertaining and informative.
  - `voice_instructions` *(optional)*: appended to this line's TTS instructions — use this to set an episode-wide tone override (put the same string on every line) without touching the shared per-speaker defaults.

Validate before spending any API calls:

```bash
python3 character-engine/tools/validate_episode.py character-engine/episodes/<slug>/episode.json
```

## 4. Screen content — prefer memes, use real charts only when precision matters

`screen.type` options: `"meme"`, `"image"`, `"text"`, `"stat"`, `"timeline"`, `"table"`, `"quote"`.

**Default to `"meme"` for almost everything.** It's more entertaining, keeps attention, and still bakes in the real number/fact as part of the joke when there is one. Reserve `"image"` for a beat where the exact shape of real data matters more than a joke, and only when you actually have a chart/image asset to point at — don't fabricate a data visual to sell a fake number.

A meme screen spec:

```json
"screen": {
  "type": "meme",
  "path": "/absolute/path/to/character-engine/episodes/<slug>/screen-memes/lineNN.png",
  "prompt": "<prompt text>"
}
```

`path` and `prompt` are both required. `path` is where the generated image is cached/read from; `prompt` is only consulted when that file doesn't already exist with matching generation metadata (safe to leave both in place across re-renders — unchanged prompts never re-hit the API). Keep generated screen-memes co-located under the episode's own folder (`character-engine/episodes/<slug>/screen-memes/`) — they're gitignored build cache, same as frames/audio.

**Writing the prompt**: don't repeat the style/quality boilerplate — `generate_screen_meme.py`'s `STYLE_LOCK` already prepends "bold 2D cartoon meme, thick outlines, no logos, no real public figures, spell out captions exactly" etc. Just write:
1. The actual scene/joke, specific to *this line's* real fact or number if it has one (bake the number into the image, e.g. a price tag, a stamped percentage, a sign) — a generic reaction image is a failure.
2. A baked-in caption, ≤8 words, stated exactly (don't leave it to the model to improvise text).
3. If a person appears, vary race/ethnicity across the episode's set of memes.

Generation happens automatically — `make_episode.py` calls `generate_screen_meme.py --episode <path>` before rendering, which extracts every line's (and intro's/outro's) `{prompt, path}` and generates them all in parallel. You never need to invoke it by hand unless testing a single prompt:

```bash
python3 character-engine/tools/generate_screen_meme.py --prompt "..." --out /path/to/test.png
```

The generator targets the shared screen's exact aspect ratio automatically (computed from `make_stage.SCREEN_W`/`SCREEN_H`, currently resolves to `1248x768`) so per-line memes fill the screen edge to edge; the intro/outro cards are a wider box and will show a little padding on the sides — that's expected.

## 5. Gestures, moods, and the shared screen

Both hosts stand flanking one shared screen (not one each). Gesture names describe **which side of the frame** the screen is on relative to the speaker, not anatomy:

- `point_screen_R`: screen is on this speaker's frame-right (Nate's default when cited — his mark is frame-left, screen is to his right).
- `point_screen_L`: screen is on this speaker's frame-left (Kai's default when cited — her mark is frame-right, screen is to her left).
- Don't swap these per-speaker; the default auto-assignment already gets it right. Only set `gesture` explicitly to override with a different pose.
- Other poses: `rest_stand`, `open_hands`, `explain_chop`, `count_one`, `shrug`. Nate's non-`point_screen_*` gestures are automatically mirrored so his arm still swings toward the screen regardless of which named pose is used — you don't need to think about this, just pick whichever gesture fits the line emotionally.

## 6. Render

```bash
OPENAI_API_KEY=<key> USE_OPENAI_TTS=true python3 character-engine/tools/make_episode.py \
  character-engine/episodes/<slug>/episode.json --format youtube
```

This runs, in order: (a) voice generation (`gpt-4o-mini-tts`, `cedar` for Nate / `marin` for Kai) and screen-meme generation, concurrently, each internally parallel across every line — typically 15-20s total even for 14-16 lines; (b) per-line frame rendering + encode across a process pool (this is the dominant cost, ~90% of total wall time — expect roughly 3-4 minutes total for a 12-16 line episode on an 8-core machine); (c) assembly + music scoring.

Everything is cached by content: re-running after editing only line 6's text regenerates only line 6's voice, meme (if its prompt changed), and render — everything else is a cache hit. `RENDER_WORKERS=<n>` env var caps the render process pool if the default (one per line) is too much for the machine's RAM.

**Output**: `make_episode.py` moves the finished video to `character-engine/output/youtube/<slug>.mp4` as its last step — a single, flat, easy-to-browse folder for every rendered YouTube cut, separate from `character-engine/output/reels/` (the reel skill's equivalent). Everything else (`frames/`, `audio/`, the intermediate `_dialogue_cut.mp4`/`_video_only.mp4`) stays in `character-engine/episodes/<slug>/` as build cache/QA material (step 7 below still reads frames from there) — only the one finished deliverable per render relocates. Both `output/` subfolders are gitignored, same as the episode build cache.

## 7. QA before reporting done

Never declare a render finished without looking at actual frames — cached logic and API responses can silently produce something wrong.

```bash
python3 character-engine/tools/qa_contact_sheet.py character-engine/episodes/<slug> --out /tmp/qa.jpg
```

Then use the Read tool to pull the contact sheet and a handful of individual frames (`episodes/<slug>/frames/lineNN/f*.png`, plus `frames/intro/` and `frames/cta/`) and check:

- Both hosts point *toward* the shared screen, not away from it.
- No screen ever shows the spoken caption text verbatim — only memes/charts/standby.
- Each meme's baked-in joke/number actually matches what that line is saying, and any number shown is real (step 1).
- The outro card shows the right `cta_url` (not a dead/placeholder link).
- No caption or number is clipped at an edge.
- Per-line audio durations are sane for the tone chosen (`ffprobe` each `audio/lineNN.wav` if the tone demands short lines).

You cannot hear the audio yourself — say so explicitly when reporting, and ask the user to confirm delivery/tone landed.

## 8. Sync to Google Drive

Once the render passes QA, upload it so it's reachable from every device:

```bash
rclone copy character-engine/output/youtube/<slug>.mp4 "gdrive:BTL Marketing Videos/YouTube/"
```

Idempotent — re-running after a re-render overwrites the same filename in Drive. This is the last step before reporting the episode finished; don't skip it even for a quick render.

## Known gotchas worth remembering

- `USE_OPENAI_TTS` not set → silent fallback to robotic macOS voices. Always set it.
- A line's screen defaulting to nothing does **not** mean "no visual" — it means a branded standby card. It never means "show the caption."
- `point_screen_R`/`point_screen_L` are frame-relative, not anatomical — don't reason about them as "Nate's right hand."
- Editing a `screen.prompt` string is what invalidates the meme cache — editing only the rendered PNG by hand won't survive a re-render.
- The `gdrive:` rclone remote must be configured (`rclone listremotes` should list it) for step 8's Drive sync to work — already set up on this machine as of the port from the original project.
