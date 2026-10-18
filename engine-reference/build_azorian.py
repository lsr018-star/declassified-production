#!/usr/bin/env python3
"""Azorian 3D documentary engine build.
Depth-displacement parallax (MiDaS) + programmatic map + ASS kinetic subs
+ procedural SFX + sidechain mix. No ffmpeg zoompan anywhere.
"""
import os, sys, json, subprocess, math, wave, struct
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

D = os.path.dirname(os.path.abspath(__file__))
os.chdir(D)
sys.path.insert(0, os.path.dirname(D))
from sfx_hud import (synthesize_sub_bass_boom, synthesize_tactical_tick,
                     build_sfx_track, apply_investigative_hud_overlay)

W, H, FPS = 1080, 1920, 60
OV = 1.2  # overscan
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("FAIL:", " ".join(cmd[:6])); print(r.stderr[-2000:])
        raise SystemExit(1)
    return r

def probe(p):
    r = run(["ffprobe","-v","error","-show_entries","format=duration",
             "-of","default=noprint_wrappers=1",p])
    return float(r.stdout.strip().split("=")[1])

cfg = json.load(open("reel.json"))
align = json.load(open("align.json"))
spans = align["spans"]          # 12 (start,end) in vo_clean.mp3
N = len(spans)
slug = cfg["slug"]

# ---------- 1. HUD overlays on shots 2 and 6 ----------
for key, h in cfg.get("hud", {}).items():
    i = int(key)
    out = f"s{i}-hud.jpg"
    if not os.path.exists(out):
        apply_investigative_hud_overlay(
            f"s{i}.webp", out,
            hud_header=h.get("header", "DECLASSIFIED // CASE FILE"),
            location_tag=h.get("location", ""), date_tag=h.get("date", ""))
        print("hud", i, flush=True)

def shot_src(i):
    p = f"s{i}-hud.jpg"
    return p if os.path.exists(p) else f"s{i}.webp"

# ---------- 2. depth maps (MiDaS_small, CPU) ----------
def depth_map(img_path, out_path):
    if os.path.exists(out_path):
        return
    import torch
    global _midas
    if "_midas" not in globals():
        _midas = torch.hub.load("intel-isl/MiDaS", "MiDaS_small",
                                trust_repo=True, verbose=False)
        _midas.eval()
    img = Image.open(img_path).convert("RGB")
    W0, H0 = img.size
    w, h = W0 - W0 % 32, H0 - H0 % 32
    im = np.array(img.resize((w, h))) / 255.0
    im = (im - np.array([0.485, 0.456, 0.406])) / np.array([0.229, 0.224, 0.225])
    batch = torch.from_numpy(im.transpose(2, 0, 1)).unsqueeze(0).float()
    with torch.no_grad():
        pred = _midas(batch)
        pred = torch.nn.functional.interpolate(
            pred.unsqueeze(1), size=(H0, W0), mode="bicubic",
            align_corners=False).squeeze()
    d = pred.numpy()
    d = ((d - d.min()) / (d.max() - d.min())).astype(np.float32)
    Image.fromarray((d * 255).astype(np.uint8)).save(out_path)
    print("depth", out_path, flush=True)

for i in range(1, N + 1):
    if i == 3:
        continue  # map clip instead
    depth_map(shot_src(i), f"depth{i}.png")

# ---------- 3. depth-displacement parallax renderer ----------
def render_parallax(i, dur, out_mp4):
    if os.path.exists(out_mp4):
        return
    img = np.array(Image.open(shot_src(i)).convert("RGB").resize((W, H)))
    dep = np.array(Image.open(f"depth{i}.png").convert("L").resize((W, H))).astype(np.float32) / 255.0
    dep = cv2.GaussianBlur(dep, (21, 21), 0)
    oW, oH = int(W * OV), int(H * OV)
    img = cv2.resize(img, (oW, oH))
    dep = cv2.resize(dep, (oW, oH))
    dn = (dep - 0.5) * 2.0  # -1 far .. +1 near
    frames = int(dur * FPS)
    cx, cy = oW / 2, oH / 2
    amp = 34.0 * (1 if i % 2 else -1)  # alternate drift direction
    xs = np.arange(oW, dtype=np.float32)
    ys = np.arange(oH, dtype=np.float32)
    gx, gy = np.meshgrid(xs, ys)
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "18",
         "-pix_fmt", "yuv420p", out_mp4], stdin=subprocess.PIPE)
    for f in range(frames):
        t = f / max(frames - 1, 1)
        drift = math.sin(t * math.pi * 1.2) * amp
        zoom = 1.0 + 0.05 * t
        dx = dn * drift
        mx = (gx - cx) / zoom + cx + dx
        my = (gy - cy) / zoom + cy + dn * drift * 0.35
        frame = cv2.remap(img, mx, my, cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_REPLICATE)
        x0, y0 = (oW - W) // 2, (oH - H) // 2
        proc.stdin.write(frame[y0:y0 + H, x0:x0 + W].tobytes())
    proc.stdin.close(); proc.wait()
    print("parallax", out_mp4, flush=True)

# ---------- 4. programmatic Pacific map fly-through (shot 3) ----------
def render_map_clip(dur, out_mp4):
    if os.path.exists(out_mp4):
        return
    frames = int(dur * FPS)
    fnt_big = ImageFont.truetype(FONT, 40)
    fnt_sm = ImageFont.truetype(FONT, 30)
    # map geometry: Hawaii at (0.30,0.62), target at (0.66,0.30) in frame
    hx, hy = int(W * 0.30), int(H * 0.62)
    tx, ty = int(W * 0.66), int(H * 0.30)
    import numpy as np
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "18",
         "-pix_fmt", "yuv420p", out_mp4], stdin=subprocess.PIPE)
    for f in range(frames):
        t = f / max(frames - 1, 1)
        im = Image.new("RGB", (W, H), (7, 11, 20))
        dr = ImageDraw.Draw(im, "RGBA")
        for gx in range(0, W, 90):
            dr.line([(gx, 0), (gx, H)], fill=(0, 240, 255, 22), width=1)
        for gy in range(0, H, 90):
            dr.line([(0, gy), (W, gy)], fill=(0, 240, 255, 22), width=1)
        # trajectory draws progressively
        nseg, drawn = 60, int(60 * min(t * 1.15, 1.0))
        px, py = [], []
        for k in range(nseg + 1):
            u = k / nseg
            # curved path
            x = hx + (tx - hx) * u
            y = hy + (ty - hy) * u - math.sin(u * math.pi) * 160
            px.append(x); py.append(y)
        for k in range(1, drawn):
            if k % 2 == 0:
                dr.line([(px[k-1], py[k-1]), (px[k], py[k])],
                        fill=(255, 42, 42, 255), width=6)
        # Hawaii marker
        dr.ellipse([hx-10, hy-10, hx+10, hy+10], fill=(0, 240, 255, 255))
        dr.text((hx + 18, hy - 20), "HAWAII", font=fnt_sm, fill=(0, 240, 255, 255))
        # pulsing target reticle
        pr = 26 + 10 * math.sin(f * 0.35)
        dr.ellipse([tx-pr, ty-pr, tx+pr, ty+pr], outline=(255, 42, 42, 255), width=4)
        dr.line([(tx-44, ty), (tx-18, ty)], fill=(255, 42, 42, 255), width=4)
        dr.line([(tx+18, ty), (tx+44, ty)], fill=(255, 42, 42, 255), width=4)
        dr.line([(tx, ty-44), (tx, ty-18)], fill=(255, 42, 42, 255), width=4)
        dr.line([(tx, ty+18), (tx, ty+44)], fill=(255, 42, 42, 255), width=4)
        # coordinate + distance text
        dr.rectangle([60, 240, 700, 400], fill=(6, 12, 24, 220),
                     outline=(0, 240, 255, 160), width=2)
        dr.text((80, 258), "TARGET: 40.06N 179.54E", font=fnt_big,
                fill=(255, 70, 70, 255))
        km = int(2510 * min(t * 1.15, 1.0))
        dr.text((80, 312), f"DIST FROM HAWAII: {km} KM", font=fnt_sm,
                fill=(0, 240, 255, 255))
        dr.text((80, 352), "DEPTH: 16,500 FT", font=fnt_sm,
                fill=(200, 220, 255, 230))
        # scanlines + vignette-ish
        for yy in range(0, H, 8):
            dr.line([(0, yy), (W, yy)], fill=(0, 240, 255, 8), width=1)
        proc.stdin.write(np.array(im).tobytes())
    proc.stdin.close(); proc.wait()
    print("map clip ok", flush=True)

# ---------- 5. render all shots ----------
shot_durs = []
for i in range(1, N + 1):
    s, e = spans[i - 1]
    shot_durs.append(e - s)
for i, dur in enumerate(shot_durs, 1):
    if i == 3:
        render_map_clip(dur, f"seg{i}.mp4")
    else:
        render_parallax(i, dur, f"seg{i}.mp4")

with open("vlist.txt", "w") as f:
    f.writelines(f"file 'seg{i}.mp4'\n" for i in range(1, N + 1))
if not os.path.exists("concat.mp4"):
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", "vlist.txt", "-c", "copy", "concat.mp4"])
total = probe("concat.mp3") if False else probe("concat.mp4")
print("video total:", round(total, 1), flush=True)

# ---------- 6. ASS kinetic subtitles ----------
def ass_color(hex6):
    r, g, b = int(hex6[1:3], 16), int(hex6[3:5], 16), int(hex6[5:7], 16)
    return f"&H00{b:02X}{g:02X}{r:02X}&"

CYAN, GOLD = ass_color("#00F0FF"), ass_color("#FFD700")
AGENCIES = {"CIA", "FBI", "KGB", "RAW", "SOSUS"}
def hl(w):
    bare = w.strip(".,!?")
    if any(ch.isdigit() for ch in bare) or "million" in w.lower() or "dollar" in w.lower():
        return f"{{\\c{GOLD}}}{w}{{\\c&HFFFFFF&}}"
    if bare.upper() in AGENCIES:
        return f"{{\\c{CYAN}}}{w}{{\\c&HFFFFFF&}}"
    return w

def ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

words = align["words"]
events = []
k = 0
while k < len(words):
    # 3-word chunks, but don't cross line boundaries
    ln = words[k]["line"]
    chunk = [words[k]]
    while len(chunk) < 3 and k + len(chunk) < len(words) and words[k + len(chunk)]["line"] == ln:
        chunk.append(words[k + len(chunk)])
    k += len(chunk)
    txt = " ".join(hl(x["w"]) for x in chunk)
    events.append((chunk[0]["s"], chunk[-1]["e"] + 0.08, txt))

with open("subs.ass", "w") as f:
    f.write("""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Fern,DejaVu Sans Bold,82,&H00FFFFFF,&H000019FF,&H00000000,&H99000000,-1,0,0,0,100,100,0,0,1,6,2,2,40,40,440,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""")
    for s, e, txt in events:
        f.write(f"Dialogue: 0,{ts(s)},{ts(e)},Fern,,0,0,0,,"
                f"{{\\fscx120\\fscy120\\t(0,90,\\fscx100\\fscy100)}}{txt}\n")
print("ass events:", len(events), flush=True)

# ---------- 7. whoosh synth + SFX track ----------
def synth_whoosh(path="/tmp/_whoosh.wav", dur=0.5):
    sr = 44100
    n = int(sr * dur)
    x = np.random.randn(n)
    # sweeping bandpass: simple one-pole HP with rising cutoff via cumsum trick
    # use FFT filter with time-varying mask (approx via STFT-ish blocks)
    out = np.zeros(n)
    nb = 24
    bl = n // nb
    for b in range(nb):
        seg = x[b*bl:(b+1)*bl]
        fc = 400 * (4000/400) ** (b / nb)  # 400 -> 4000 Hz sweep
        F = np.fft.rfft(seg)
        freqs = np.fft.rfftfreq(len(seg), 1/sr)
        mask = np.exp(-0.5 * ((freqs - fc) / (fc * 0.6)) ** 2)
        out[b*bl:(b+1)*bl] = np.fft.irfft(F * mask, len(seg))
    env = np.exp(-np.linspace(0, 4.5, n)) * np.minimum(1, np.linspace(0, 8, n))
    out = out * env
    out = out / max(1e-6, np.abs(out).max()) * 0.9
    with wave.open(path, "w") as wv:
        wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(sr)
        wv.writeframes(struct.pack("<%dh" % n, *(int(v*32767) for v in out)))
    return path

def build_full_sfx(cuts, total, out="sfx_track.wav"):
    sr = 44100
    n = int(sr * total)
    mix = np.zeros(n, dtype=np.float64)
    def read(p):
        with wave.open(p) as wv:
            raw = wv.readframes(wv.getnframes())
        return np.array(struct.unpack("<%dh" % (len(raw)//2), raw), dtype=np.float64) / 32767.0
    boom = read(synthesize_sub_bass_boom("/tmp/_boom.wav")) * 0.55
    whoosh = read(synth_whoosh()) * 0.35
    tick = read(synthesize_tactical_tick("/tmp/_tick.wav")) * 0.15
    hud_lines = {2, 3, 6}
    for idx, ct in enumerate(cuts):
        o = int(ct * sr)
        for sig in (boom, whoosh):
            m = min(len(sig), n - o)
            mix[o:o+m] += sig[:m]
        if idx + 1 in hud_lines:
            to = o + int(0.15 * sr)
            m = min(len(tick), n - to)
            mix[to:to+m] += tick[:m]
    mix = np.clip(mix, -0.95, 0.95)
    with wave.open(out, "w") as wv:
        wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(sr)
        wv.writeframes(struct.pack("<%dh" % n, *(int(v*32767) for v in mix)))
    return out

cuts = [0.0] + [round(sum(shot_durs[:i]), 2) for i in range(1, N)]
if not os.path.exists("sfx_track.wav"):
    build_full_sfx(cuts, total + 1.0)
    print("sfx ok", flush=True)

# ---------- 8. audio: VO loudnorm + EQ, drone bed, sidechain ----------
if not os.path.exists("vo_norm.m4a"):
    run(["ffmpeg","-y","-v","error","-i","vo_clean.mp3","-af",
         "loudnorm=I=-14:TP=-1.5:LRA=11,equalizer=f=115:t=h:w=100:g=3",
         "-c:a","aac","vo_norm.m4a"])
    print("vo norm ok", flush=True)
if not os.path.exists("bed.wav"):
    run(["ffmpeg","-y","-v","error",
         "-f","lavfi","-i",f"sine=frequency=55:duration={total+1}",
         "-f","lavfi","-i",f"sine=frequency=82.5:duration={total+1}",
         "-f","lavfi","-i",f"anoisesrc=color=brown:duration={total+1}:sample_rate=44100",
         "-filter_complex",
         "[2:a]lowpass=f=220,volume=0.5[ns];[0:a][1:a]amix=inputs=2:normalize=0[dr];"
         "[dr]volume=0.08[dl];[ns]volume=0.04[nl];[dl][nl]amix=inputs=2:normalize=0[bed]",
         "-map","[bed]","bed.wav"])
    print("bed ok", flush=True)

# ---------- 9. final assembly: concat video + burned ASS + full mix ----------
run(["ffmpeg","-y","-v","error","-i","concat.mp4","-i","vo_norm.m4a",
     "-i","bed.wav","-i","sfx_track.wav",
     "-filter_complex",
     "[2:a][1:a]sidechaincompress=threshold=0.02:ratio=12:attack=20:release=400[duck];"
     "[1:a]volume=1.0[vo];[duck]volume=1.0[bd];[3:a]volume=0.9[fx];"
     "[vo][bd][fx]amix=inputs=3:normalize=0[a]",
     "-vf", f"ass={D}/subs.ass",
     "-map","0:v","-map","[a]","-c:v","libx264","-preset","medium","-crf","19",
     "-c:a","aac","-r","60","-shortest", f"{slug}-3d-reel.mp4"])
print("DONE:", f"{slug}-3d-reel.mp4", round(probe(f"{slug}-3d-reel.mp4"),1), flush=True)
