#!/usr/bin/env python3
"""reel3d.py — locked 3D reel factory (see 3D-STYLE-LOCK.md).

Usage: python3 reel3d.py <reel-dir>
The reel dir must contain reel.json:
{
  "slug": "db-cooper",
  "lines":    ["...Hindi narration (romanized, for TTS)..."],
  "captions": ["...Devanagari on-screen captions..."],
}
and s1.webp..sN.webp scenes (1080x1920-ish, dark 3D cinematic).

Builds: TTS per line -> push-in animation -> dual-font caption PNGs ->
dark score bed -> final <slug>-3d-reel.mp4. Skips steps already done.
"""
import os, sys, subprocess, json
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import Layout

FONT_DEVA = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
FONT_LATN = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
RAQM = Layout.RAQM
TTS = "/opt/hatch/bin/tts"

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("FAIL:", " ".join(cmd[:8])); print(r.stderr[-2000:])
        raise SystemExit(1)
    return r

def probe(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1", path])
    return float(r.stdout.strip().split("=")[1])

def is_deva(word):
    return any("\u0900" <= ch <= "\u097f" for ch in word)

def main():
    d = os.path.abspath(sys.argv[1])
    os.chdir(d)
    cfg = json.load(open("reel.json"))
    slug = cfg["slug"]
    lines, captions = cfg["lines"], cfg["captions"]
    assert len(lines) == len(captions), "lines and captions must match"
    n = len(lines)
    for i in range(1, n + 1):
        assert os.path.exists(f"s{i}.webp"), f"s{i}.webp missing"

    # 1. Hindi TTS per line
    durs = []
    for i, line in enumerate(lines, 1):
        out = f"v{i}.mp3"
        if not os.path.exists(out):
            run([TTS, "speak", "--text", line, "--language", "hi",
                 "--output", out])
        durs.append(probe(out) + 0.45)
        print(f"v{i}: {durs[i-1]:.1f}s", flush=True)

    # 2. dual-font caption PNGs (Devanagari + Latin fallback)
    os.makedirs("cap", exist_ok=True)
    fdeva = ImageFont.truetype(FONT_DEVA, 44, layout_engine=RAQM)
    flatn = ImageFont.truetype(FONT_LATN, 42)
    SPACE = 14
    def wwidth(w):
        return (fdeva if is_deva(w) else flatn).getlength(w)
    for i, cap in enumerate(captions, 1):
        out = f"cap/c{i}.png"
        if os.path.exists(out):
            continue
        words = cap.split()
        lns, cur, curw = [], [], 0
        for w in words:
            ww = wwidth(w) + SPACE
            if curw + ww < 920 or not cur:
                cur.append(w); curw += ww
            else:
                lns.append(cur); cur = [w]; curw = ww
        lns.append(cur)
        lh, H = 64, len(lns) * 64 + 56
        img = Image.new("RGBA", (1080, H), (0, 0, 0, 0))
        dr = ImageDraw.Draw(img)
        dr.rounded_rectangle([20, 10, 1060, H - 10], radius=18,
                             fill=(0, 0, 0, 170))
        y = 36
        for ln in lns:
            total_w = sum(wwidth(w) for w in ln) + SPACE * (len(ln) - 1)
            x = (1080 - total_w) / 2
            for w in ln:
                f = fdeva if is_deva(w) else flatn
                dr.text((x, y), w, font=f, fill="white")
                x += f.getlength(w) + SPACE
            y += lh
        img.save(out)
        print("cap", i, "ok", flush=True)

    # 3. segments: slow push-in + caption overlay
    segs = []
    for i in range(1, n + 1):
        dur, frames = durs[i - 1], int(durs[i - 1] * 30)
        seg = f"seg{i}.mp4"
        if not os.path.exists(seg):
            run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", f"s{i}.webp",
                 "-i", f"cap/c{i}.png", "-i", f"v{i}.mp3",
                 "-filter_complex",
                 f"[0:v]scale=2160:3840:force_original_aspect_ratio=increase,"
                 f"crop=2160:3840,"
                 f"zoompan=z='min(zoom+0.0009,1.10)':d={frames}:"
                 f"x='iw/2-(iw/zoom/2)':y='ih/2-(iw/zoom/2)':s=1080x1920:fps=30,"
                 f"format=yuv420p[v];[v][1:v]overlay=(W-w)/2:300[vout]",
                 "-map", "[vout]", "-map", "2:a", "-t", str(dur),
                 "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                 "-c:a", "aac", seg])
        segs.append(seg)
        print("seg", i, "ok", flush=True)

    # 4. concat
    with open("vlist.txt", "w") as f:
        f.writelines(f"file '{s}'\n" for s in segs)
    if not os.path.exists("concat.mp4"):
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
             "-i", "vlist.txt", "-c", "copy", "concat.mp4"])
    total = probe("concat.mp4")
    print("total:", round(total, 1), flush=True)

    # 5. dark score bed
    if not os.path.exists("bed.wav"):
        run(["ffmpeg", "-y", "-v", "error",
             "-f", "lavfi", "-i", f"sine=frequency=55:duration={total}",
             "-f", "lavfi", "-i", f"sine=frequency=82.5:duration={total}",
             "-f", "lavfi",
             "-i", f"anoisesrc=color=brown:duration={total}:sample_rate=44100",
             "-filter_complex",
             "[2:a]lowpass=f=220,volume=0.5[noise];"
             "[0:a][1:a]amix=inputs=2:normalize=0[drone];"
             "[drone]volume=0.10[d];[noise]volume=0.05[n];"
             "[d][n]amix=inputs=2:normalize=0,tremolo=f=0.7:d=0.6,volume=0.5[bed]",
             "-map", "[bed]", "bed.wav"])

    # 6. final mix
    out = f"{slug}-3d-reel.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-i", "concat.mp4", "-i", "bed.wav",
         "-filter_complex",
         "[0:a]volume=1.0[vo];[1:a]volume=0.35[bed];"
         "[vo][bed]amix=inputs=2:normalize=0[a]",
         "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac",
         "-shortest", out])
    print("DONE:", out, round(probe(out), 1), "s", flush=True)

if __name__ == "__main__":
    main()
