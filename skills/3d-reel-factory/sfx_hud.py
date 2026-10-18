#!/usr/bin/env python3
"""Procedural Hollywood SFX + tactical HUD overlay for the 3D reel factory.

Source: user-provided script (2026-10-18), integrated with two fixes:
- HUD text uses DejaVuSans-Bold (load_default() bitmap font is unreadably tiny
  at 1080x1920).
- HUD header/location/date are parameters per shot (defaults were CIA-specific).

Stdlib + PIL only. No external SFX files needed.
"""
import math
import wave
import struct
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFont as IF

FONT_LATN = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# ==============================================================================
# 1. PROCEDURAL HOLLYWOOD SFX GENERATOR (Zero External SFX Files Needed!)
# ==============================================================================

def synthesize_sub_bass_boom(filename="sfx_boom.wav", duration=0.85):
    """Deep 90Hz -> 32Hz cinematic sub-bass impact hit for scene cuts."""
    sr = 44100
    n = int(sr * duration)
    with wave.open(filename, "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sr)
        for i in range(n):
            t = i / sr
            freq = 30.0 + 65.0 * math.exp(-t * 6.5)
            env = math.exp(-t * 4.2)
            s = env * math.sin(2.0 * math.pi * freq * t)
            s += 0.25 * env * math.sin(2.0 * math.pi * (freq * 2.0) * t)
            s = max(-0.95, min(0.95, s))
            wav.writeframes(struct.pack("<h", int(s * 32767)))
    return filename


def synthesize_tactical_tick(filename="sfx_tick.wav", duration=0.06):
    """Crisp telemetry blip for HUD/caption appearance."""
    sr = 44100
    n = int(sr * duration)
    with wave.open(filename, "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sr)
        for i in range(n):
            t = i / sr
            env = math.exp(-t * 45.0)
            s = env * math.sin(2.0 * math.pi * 1850.0 * t)
            wav.writeframes(struct.pack("<h", int(s * 24000)))
    return filename


def build_sfx_track(cut_times, total, out="sfx_track.wav",
                    boom_vol=0.5, tick_vol=0.15):
    """Place a boom + tick at every scene cut. cut_times: seconds list."""
    sr = 44100
    n = int(sr * total)
    mix = [0.0] * n

    def read_wav(path):
        with wave.open(path) as w:
            raw = w.readframes(w.getnframes())
        return [v / 32767.0 for v in struct.unpack("<%dh" % (len(raw) // 2), raw)]

    boom = read_wav(synthesize_sub_bass_boom("/tmp/_boom.wav"))
    tick = read_wav(synthesize_tactical_tick("/tmp/_tick.wav"))
    for ct in cut_times:
        o = int(ct * sr)
        for i, s in enumerate(boom):
            if o + i < n:
                mix[o + i] += s * boom_vol
        to = o + int(0.12 * sr)  # tick lands just after the boom attacks
        for i, s in enumerate(tick):
            if to + i < n:
                mix[to + i] += s * tick_vol
    with wave.open(out, "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sr)
        for s in mix:
            s = max(-0.95, min(0.95, s))
            wav.writeframes(struct.pack("<h", int(s * 32767)))
    return out


# ==============================================================================
# 2. TACTICAL DOCUMENTARY HUD & EVIDENCE OVERLAY COMPOSITOR
#    Optional per-shot layer (reel.json "hud": {...}). Default OFF — the locked
#    style has no HUD; enable only on investigative beats (evidence boards,
#    FBI/IB rooms, map reveals).
# ==============================================================================

def apply_investigative_hud_overlay(input_image_path, output_image_path,
                                    hud_header="DECLASSIFIED // CASE FILE",
                                    location_tag="",
                                    date_tag=""):
    img = Image.open(input_image_path).convert("RGBA")
    img = img.resize((1080, 1920), Image.Resampling.LANCZOS)

    overlay = Image.new("RGBA", (1080, 1920), (5, 10, 20, 45))
    draw = ImageDraw.Draw(overlay)
    for y in range(0, 1920, 8):
        draw.line([(0, y), (1080, y)], fill=(0, 240, 255, 10), width=1)

    c = (0, 240, 255, 180)
    m, bl = 48, 45
    draw.line([(m, m), (m + bl, m)], fill=c, width=4)
    draw.line([(m, m), (m, m + bl)], fill=c, width=4)
    draw.line([(1080 - m - bl, m), (1080 - m, m)], fill=c, width=4)
    draw.line([(1080 - m, m), (1080 - m, m + bl)], fill=c, width=4)

    f_head = ImageFont.truetype(FONT_LATN, 30)
    f_body = ImageFont.truetype(FONT_LATN, 26)
    draw.rectangle([72, 72, 760, 200], fill=(6, 12, 24, 210),
                   outline=(0, 240, 255, 140), width=2)
    draw.rectangle([88, 94, 108, 114], fill=(255, 42, 42, 255))
    draw.text((124, 90), hud_header, fill=(255, 70, 70, 255), font=f_head)
    y = 130
    if location_tag:
        draw.text((88, y), "LOC: " + location_tag, fill=(0, 240, 255, 230),
                  font=f_body)
        y += 34
    if date_tag:
        draw.text((88, y), "TIMESTAMP: " + date_tag, fill=(200, 220, 255, 210),
                  font=f_body)

    Image.alpha_composite(img, overlay).convert("RGB").save(output_image_path,
                                                            quality=95)
    return output_image_path


# ==============================================================================
# 3. 2.5D PARALLAX RENDERER — 60fps drift + thriller grade + vignette.
#    (Single-layer drift zoom; the "multi-plane" feel comes from the drift
#    vector + grade. True multi-plane would need depth maps.)
# ==============================================================================

def render_25d_parallax_clip(image_path, duration, output_mp4,
                             motion_type="push_tilt", fps=60):
    frames = int(duration * fps)
    if motion_type == "push_tilt":
        z = "min(zoom+0.0012,1.26)"
        x = "iw/2-(iw/zoom/2)+sin(on/35)*18"
        y = "ih/2-(ih/zoom/2)"
    else:
        z = "if(eq(on,1),1.24,max(1.02,zoom-0.0010))"
        x = "iw/2-(iw/zoom/2)-sin(on/40)*16"
        y = "ih/2-(ih/zoom/2)"
    vf = (f"scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,"
          f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s=1080x1920:fps={fps},"
          f"eq=contrast=1.15:brightness=-0.03:saturation=1.18,"
          f"vignette=PI/4.2,format=yuv420p")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", image_path,
                    "-vf", vf, "-t", f"{duration:.2f}",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "17",
                    output_mp4], check=True)
    return output_mp4


if __name__ == "__main__":
    synthesize_sub_bass_boom()
    synthesize_tactical_tick()
    print("[READY] Procedural SFX & tactical HUD module loaded.")
