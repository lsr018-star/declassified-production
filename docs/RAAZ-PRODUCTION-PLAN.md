# RAAZ PRODUCTION PLAN — channel standard (lucky's order 2026-10-18)

Goal: every RAAZ short plays at the level of StudyIQ, Nitish Rajput, Think
School. No compromise. Research first (done), plan locked, then demo.

## 1. What "their level" means (verified from watching them)

| Channel | Proven formula |
|---|---|
| StudyIQ (news lane) | Photorealistic cinematic renders of REAL people (Musk, Modi, Ambani) — not cartoons; Esri-style topographic maps, country filled solid red; NO word captions — bold YELLOW ALL-CAPS callout cards at key beats; journalistic brisk VO; hard cuts ~6s; news-article graphics as evidence |
| Nitish Rajput (story lane) | Stylized 3D dioramas, black void, neon map accents; static 3D typography cards — gold-embossed names, red/white numbers; top hook banner; fast documentary VO; map per location beat |
| Think School (explainer) | Curiosity-gap question titles; bold YELLOW burned-in captions; white keyword cards swapping every few seconds; COLD OPEN (no intro); payoff ending (no CTA); real footage cut-ins; news-source credits; epic background score |

Shared law: 50–70s, 9:16, hook in first 3s, 8–12 scenes, a cut every 3–6s,
maps mandatory, numbers/names/dates as graphic objects, research underneath.

## 2. RAAZ visual system — REAL images in 3D treatment (boss correction)

The boss's correction 2026-10-18: their videos use REAL imagery treated in
3D — not 100% AI fantasy worlds. New hierarchy for every shot:
1. **Real licensed imagery first** — Pixabay/Pexels stills & footage of real
   places, real news-article screenshots, real documents, programmatic real
   maps (Esri-style). Downloaded locally, visually verified.
2. **Photorealistic cinematic renders of real people/places** where no
   licensed image exists (StudyIQ does exactly this) — cinematic, not cartoon.
3. **3D treatment on everything**: MiDaS depth parallax (2.5D camera drift),
   HUD overlays, glowing map fly-throughs, evidence-board framing.
4. Pure AI diorama ONLY as last resort.

Multi-clip law (locked): 10–12 shots minimum, cut every 3–6s. One static
visual = dead video = rejected at QA.

## 3. Voice — ElevenLabs ultra-realistic (after key lands)

- Test key on arrival (`voices` list must 200). Never log the key.
- Documentary voice: deep, steady, authoritative English narration —
  ElevenLabs stock voice (e.g. deep male narrator class), NOT his clone
  (clone reserved for his personal approval later).
- Settings for documentary: stability ~0.55–0.65 (natural, not robotic),
  similarity_boost ~0.75, style exaggeration low. Pace: fast but clear
  (~150–160 wpm, Nitish/StudyIQ cadence).
- Post: loudnorm to −14 LUFS, 0.22s silence trim, breath cleanup.
- Fallback if ElevenLabs fails: built-in TTS — demo NEVER ships without
  ElevenLabs once the key is connected (boss order: no mistakes).

## 4. Sound — RAAZ's own theme (like theirs, but ours)

- **RAAZ theme bed** (fully procedural, zero copyright risk, ownable):
  D-minor dark cinematic, ~90 BPM — sub-bass pulse, tense pad, risers into
  every cut, deep hit on reveals/numbers. Built from sfx_hud.py (boom/tick)
  extended into a full 60s composed bed.
- Sidechain: VO ducks the bed (−6 dB) so narration is always king.
- Beat cuts: whoosh on every scene change, tick on HUD data, boom on money/
  death numbers. Silence 0.3s before the final payoff line (tension trick).

## 5. Captions — stylish 3D (boss order: "3D me")

- Rendered 3D text (PIL, embossed/beveled with drop shadow + subtle
  perspective tilt) — not flat ASS.
- Word-pop: 2–3 words per pop, 90ms pop-in, lower-center safe zone.
- Color grammar: WHITE narration, GOLD #FFD700 money/names, CYAN #00F0FF
  agencies/places, RED #FF2A2A deaths/danger. Black 6px outline always.
- Plus StudyIQ-style YELLOW ALL-CAPS callout cards on the 2–3 biggest beats.

## 6. Edit cadence & structure (every short)

1. 0–3s: HOOK (question or impossible claim, top banner + VO)
2. Map/premise → 3. Tech/how → 4. Conflict → 5. Evidence → 6. Twist →
   7. Payoff/verdict. 10–12 shots, no shot longer than 6s.

## 7. Zero-mistake QA gate (demo does not ship until ALL pass)

- [ ] Every fact verified against 2+ sources (logged in research-notes.txt)
- [ ] All on-screen text spell-checked, no cut-off, no overlap
- [ ] 4+ frames extracted and VIEWED (not just generated)
- [ ] Hook lands in first 3s; duration 50–70s; 10+ shots confirmed
- [ ] ElevenLabs voice (no fallback), −14 LUFS, bed ducked under VO
- [ ] Real-image-first hierarchy followed; no pure-AI shot unless justified
- [ ] Captions readable on phone at arm's length

## 8. Demo spec (builds the moment the ElevenLabs key lands)

- Topic: **"The Fake Country That Fooled Europe"** — Gregor MacGregor's
  Poyais scam (1820s): invented a country, sold its bonds, ships sailed to
  nothing. Global, money, mystery — perfect for USA/UK audience.
- English, ~60s, 11 shots, full 5-layer engine + this plan's upgrades.
- Delivered as file + 4 verified frames. Publishing stays tap-gated
  (IG) / auto (YT Shorts) per standing rules.

## 9. Rollout after demo approval

- This plan merges into local-3d-reel-factory SKILL.md as the permanent
  standard; daily factory adopts real-image-first + ElevenLabs + RAAZ theme.
- Style audits: each upload scored against the §1 table (the old Think
  School rubric is superseded by this three-channel standard).
