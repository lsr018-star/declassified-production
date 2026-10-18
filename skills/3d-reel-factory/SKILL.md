# 3D Reel Factory (5-layer documentary engine)

Produce DECLASSIFIED 3D investigative documentary shorts (50–70s,
1080x1920, 60fps, ENGLISH VO — audience lock 2026-10-18: USA/UK/CA/AU).
Read `3D-STYLE-LOCK.md` and `RAAZ-PRODUCTION-PLAN.md` first — style rules
are mandatory. Brand: DECLASSIFIED ("Secrets they tried to bury —
declassified daily").

## When to use
Any RAAZ documentary short. One story per reel. Two tracks:
- **Track A (news lane):** real current event (last 7 days), journalistic Hinglish VO, yellow callout cards
- **Track B (true-story lane):** history/crime/mystery, pure-Hindi fast VO, 3D text cards

## Pipeline (5 layers — no ffmpeg zoompan, ever)

### 0. Research first
Track A: news radar (browser.search news vertical + social.search), 2+ sources logged.
Track B: verify every fact against 2+ public sources. Original scripts only —
never retell another creator's narration.

### 1. Script → reel.json
Dir `~/workspace/earn-agent/outreach/reels3d/<slug>/` with `reel.json`:
`slug`, `lines` (10–12 Hindi lines, romanized, one per shot), optional `hud`
per-shot config `{header, location, date}`. Scene prompts: always start
"Vertical 9:16. 3D Unreal Engine 5 investigative documentary diorama, style of
Fern YouTube channel, volumetric fog, teal and amber rim lighting, isometric
cutaway, 8k octane render." Locked palette #070B14 / #00F0FF / #FF2A2A.

### 2. Scenes
`media.generate_image` per prompt (max 4 calls/response). Visually verify each.

### 3. Voice + word timestamps
TTS per line (`/opt/hatch/bin/tts speak --language hi`, voice avocado_v2:MAI_03)
→ concat → `silenceremove=0.22` → faster-whisper (`word_timestamps=True`).
Shot durations = speech segment boundaries (beat-synced cuts).

### 4. Motion (real depth parallax)
MiDaS_small depth per scene (venv `~/workspace/.venvs/azorian`, torch CPU,
manual ImageNet-normalized transform) → numpy/cv2.remap displacement:
`shift = (depth-0.5) * max_shift * orbit(t)`, 60fps, 120% overscan + center crop.
Location beats → programmatic map fly-through (dark navy, red dashed
trajectory drawing itself, pulsing reticle, coords). Investigative beats →
tactical HUD overlay (`sfx_hud.py`).

### 5. Subtitles + sound
ASS kinetic subtitles from word timestamps: 2–3 words/event, 90ms pop-in
`{\fscx120\fscy120\t(0,90,\fscx100\fscy100)}`, 6px outline, lower-center;
cyan #00F0FF for numbers/agencies, gold #FFD700 for money. Font: Montserrat
ExtraBold/Impact if present, else DejaVuSans-Bold.
Audio: VO loudnorm −14 LUFS + 115Hz +3dB; dark drone −22dB sidechain-ducked
−12dB under VO; procedural boom+whoosh per cut, ticks on HUD (`sfx_hud.py`).

### 6. Verify before delivery
4+ frames viewed (subs readable, HUD clean, parallax visible), duration and
audio checked. Broken = fix and rebuild, never ship. Reference implementation:
`~/workspace/earn-agent/outreach/reels3d/azorian/build_azorian.py`.

## Hard lessons (do not relearn)
- Noto Sans Devanagari has NO Latin glyphs → dual-font rendering where needed.
- System fonts only; never download fonts from github raw (returns HTML).
- HuggingFace Hub is proxy-blocked → MiDaS via torch.hub (trust_repo=True), not transformers pipeline.
- torch/torchvision versions must match (2.8.0/0.23.0 known-good CPU pair).
- Publishing: Instagram human-gated (lucky's tap); YouTube Shorts auto-upload allowed.
