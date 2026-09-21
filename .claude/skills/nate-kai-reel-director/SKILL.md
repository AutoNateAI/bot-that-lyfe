---
name: nate-kai-reel-director
description: Produce a Nate & Kai 9:16 vertical video (Reel/TikTok/Short) using the character-engine pipeline's `--format reel` path. Use this whenever the user asks for a reel, a short, a vertical video, a TikTok, or a 9:16 cut — or says "the reel one" after already having a YouTube cut. Builds directly on the nate-kai-video-director skill's episode.json schema; load that skill first if you haven't already, this one only covers what's different for portrait.
---

# Nate & Kai Reel Director

Same character-engine pipeline as `nate-kai-video-director` (episode.json → OpenAI TTS + contextual gpt-image memes → rendered video), rendered with `--format reel` instead of `--format youtube`. This skill only documents what's actually different for portrait — read `nate-kai-video-director` first for the base schema, screen types, gesture reference, and render mechanics.

**Do not reuse a YouTube episode's full script for the reel.** A reel is its own tight, single-topic script, not the long-form video squeezed into a taller frame — see "One focused topic" below.

## What's different in reel

- **One focused topic, told with some depth — not a recap.** Pick the single most interesting angle (the specific mechanism behind a claim, not a list of facts) and stay on it start to finish. No side-quests into other angles — those are what the YouTube cut is for.
- **Duration: 45-55 seconds is the sweet spot — a target, not a ceiling.** Keep each line's spoken audio under ~6 seconds for the quick back-and-forth cadence. Watch out: an exaggerated/comedic delivery runs noticeably slower per word than plain delivery — a script that hits 40s read straight can hit 55s read with real comedic timing. **Never trim content, cut a joke, or shorten a beat just to force the render under 60s** — some jokes and some real facts genuinely need the extra few seconds to land, and a rushed punchline is worse than a slightly-long reel. Write for the sweet spot as your aim, check the actual `ffprobe` duration once rendered, and if it runs long because the content earned it, leave it — don't hack lines down after the fact to hit a number. If a render comes in noticeably short (under 40s) that's a sign to add real content (another beat, another fact), not padding.
- **Default tone: high-voltage informal parody, heavy cussing, metaphor-first punchlines** — same house style as the base skill, just compressed into one focused story:
  - Every reel should keep a live-wire stand-up rhythm throughout, not just one hot opening line. If a line is only exposition, rewrite it until it has a turn, a reversal, a simile, a metaphor, or a hard tag.
  - Cussing is part of the cadence: fuck/shit/damn/hell should land naturally and often, not as decoration. Avoid timid "mild swearing" unless the user explicitly asks for restraint.
  - Build jokes from a real, verified mechanism when the reel leans on a fact or number (see the base skill's "pick the topic" step) — the joke rides the fact; it never replaces it. When there's no specific stat to hang the reel on, build from a relatable mechanism instead (the grind before a technical interview, a group project falling apart the night before demo day, an internship posting's fine print) rather than inventing a number.
  - **Hooks must be A-material and start like an interruption.** The first spoken line needs real collision energy: a famous promise, slogan, hype claim, or public assumption crashing into the concrete, uglier reality. Start in a dramatic conversational register, e.g. "Yoooo, guess what the fuck," "Broooo, this shit wild," or "My ninja, you won't believe this shit:" — then land the point immediately. Do not start with "Nate..." or "Kai..." unless it's part of a sharper interruption. No soft openers, no "today we're talking about," no generic headline read.
  - **Story before bit-stack.** A reel must have one clean story spine a distracted viewer can repeat: "the hype/promise met reality; reality hit the actual workflow; here's who's left holding it." Do not assemble a reel as eight adjacent jokes about the same topic. Each line should answer the previous line or escalate it.
  - **Core plot engine, not literal questions.** Under the jokes, extract the topic into a hidden sequence: setup -> the hype/promise -> what it glosses over -> the real mechanism -> where it bites someone -> the twist/complication -> the payoff or unresolved tension. Don't put those as direct Q&A lines unless the bit specifically calls for it; make them feel like story beats.
  - Use a simple reel structure unless there's a better topic-specific one: line 1 hook, line 2 why this is happening, line 3 explain the mechanism with a metaphor, line 4 bring it home to a specific person/scenario, line 5 show the pain point, line 6 twist/complication, line 7 unresolved stakes, line 8 curiosity gap / payoff. If a line could be moved anywhere without breaking the story, rewrite it.
  - Keep one recurring object/metaphor across the reel — the receipt, the red button, the group chat, the deploy button, the whiteboard — and let that object carry the viewer through the whole video. Avoid switching metaphors every line unless the switch itself is the joke.
  - If a spoken line is long or contains multiple story beats, use multiple visuals inside that line instead of letting one image sit there. Prefer splitting the line when dialogue rhythm allows it; otherwise use `screens[]` with `start_word` or `at` so the panel changes exactly when the line turns.
  - Use punchy, conversational substitutions instead of slurs. Do **not** write the n-word. If the intended casual beat wants that shape, use "my ninja" instead.
  - Prefer analogies that feel like somebody explaining it out loud: "the deadline ate the weekend," "the recruiter's promise caught him outside," "the group project is a house of cards in a wind tunnel." Keep the metaphor specific enough that the audience learns the real mechanism while laughing.
  - Roast the situation, the hype, the policy/process, the receipt, or the public contradiction; do not invent facts and do not cruelly attack a real person.
  - Put the delivery direction in each line's `voice_instructions`, and put the strongest punchlines directly in the spoken text. Do not trust TTS instructions to invent the joke.
  - Ask first only if the user's request suggests they want a more restrained tone instead (see `nate-kai-video-director`'s tone section).
- **The dialogue builds curiosity — it is not the ad.** End on a line that makes people want to know more (a cliffhanger, "that's only half of it") rather than a direct pitch. The outro/CTA screen (already built, don't touch its mechanics) is the actual promotional beat — keep the promotion there, not in the jokes.
- **The screen is a picture-in-picture panel, not part of the camera shot.** In 16:9, the camera crops the speaking anchor and the shared screen together. In portrait that's impossible without a distant, tiny-subject wide shot — so reel instead composites the screen as a fixed panel across the top of frame, with the character cropped into the space below it. This is already fully built; you don't need to touch `camera.py` or `make_episode.py` to use it, just render with `--format reel` and it happens automatically for every line plus the intro/outro.
- **Use a contextual full-video background.** Add `background_meme` to the reel's `episode.json`. The image pipeline generates/crops it to the reel delivery size (`1080x1920`) and the renderer blends it behind the hosts for the entire video. Prompt it like a cinematic environment tied to the topic — a dorm room at 2am, a hackathon floor, a dev lab, a campus quad at night — not a punchline panel. Avoid text, logos, real public figures, and busy center details; leave the top readable behind the screen panel and the lower/middle readable behind the character.
- **No burned-in caption bar.** Reel is audio-first — only a small brand pill and footer, no karaoke-style dialogue text. Don't add one back.
- **Camera still cuts per line, favoring whoever's speaking** — inherited automatically, same push-transition as youtube. This is what gives reel the same "quick switching" feel as the 16:9 cut; nothing to configure.
- **Reuse images across script rewrites.** If you're iterating on the dialogue but a line's visual beat hasn't changed, leave that line's `screen.prompt` and `screen.path` exactly as they were — the meme generator caches by prompt, so unchanged prompts never re-hit the image API. Only write a new prompt when the actual visual concept for that line changes. (Only regenerate images when the user actually asks for new ones — "the images are fine on this one" means don't touch them.)

## Timed Screens Inside One Line

For a long hook or explanation, a line may use `screens[]` instead of `screen`:

```json
"screens": [
  { "start_word": 0, "screen": { "type": "meme", "path": ".../line01a.png", "prompt": "..." } },
  { "start_word": 7, "screen": { "type": "meme", "path": ".../line01b.png", "prompt": "..." } },
  { "start_word": 14, "screen": { "type": "meme", "path": ".../line01c.png", "prompt": "..." } }
]
```

Use this whenever one spoken line has two or more visual story turns: interruption -> the real mechanism -> the local/lived consequence. Keep captions short and make each timed visual add information, not just novelty.

## Render

```bash
OPENAI_API_KEY=<key> USE_OPENAI_TTS=true python3 character-engine/tools/make_episode.py \
  character-engine/episodes/<slug>/episode.json --format reel
```

Everything else (caching, worker parallelism, the generation-phase timing breakdown) works exactly as documented in `nate-kai-video-director`.

**Output**: lands at `character-engine/output/reels/<slug>.mp4` — a single flat folder for every rendered reel, alongside its YouTube sibling `character-engine/output/youtube/`. Same move-not-copy behavior as the base skill: the episode folder keeps its build cache (frames/audio/QA material) but the one finished video relocates there as `make_episode.py`'s last step.

## QA — reel-specific checks

Do the base skill's QA pass, plus:

- **Screen panel** sits with real margin from the top edge, not touching it.
- **No screen bleed into the character region.** Look at the top-left and top-right corners of the character crop (just below the panel) on a few different lines/gestures — there should be nothing there but grid floor. If you see any sliver of color or a border line at those corners, the camera window is reaching into the shared screen's stage-space bounds again; that's `camera.single_shot_portrait`'s clamp (`screen_left`/`screen_right` vs `window["center_x"]`) — don't loosen it without re-verifying against both anchors' marks.
- **No caption bar anywhere.** If one appears, `build_line_overlay`'s reel branch has regressed.
- **Outro is vertically balanced** — the meme card and the CTA card should read as one centered group with roughly equal empty space above and below, not hugging the top with a big gap before the CTA card.
- **Actual duration via `ffprobe`**, aiming for the 45-55s sweet spot. If it's noticeably under 45s, that's a sign to add real content (another beat/fact), not to pad. If it runs past 60s because the jokes/facts genuinely needed the room, **that's fine — leave it.** Do not cut content or rush a punchline just to hit a duration number; a slightly-long reel that lands beats a trimmed one that doesn't.

## Sync to Google Drive

Once the render passes QA, upload it so it's reachable from every device:

```bash
rclone copy character-engine/output/reels/<slug>.mp4 "gdrive:BTL Marketing Videos/Reels/"
```

Idempotent — re-running after a re-render overwrites the same filename in Drive. Requires the `gdrive:` rclone remote (`rclone listremotes` should list it) — already set up on this machine as of the port from the original project. This is the last step before reporting the reel finished.
