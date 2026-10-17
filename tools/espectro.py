#!/usr/bin/env python3
"""Control de calidad del audio: niveles (pico, RMS) y espectrograma PNG por archivo. Uso: espectro.py out.png a.ogg b.ogg…"""
import subprocess, sys
import numpy as np
from PIL import Image, ImageDraw
SR = 22050
rows = []
for p in sys.argv[2:]:
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    peak, rms = np.abs(x).max(), np.sqrt((x ** 2).mean())
    print("%-34s %5.1fs pico %5.1f dB  rms %5.1f dB" % (p.split("/")[-1], len(x) / SR, 20 * np.log10(peak + 1e-9), 20 * np.log10(rms + 1e-9)))
    N, H = 2048, 1024
    fr = [np.abs(np.fft.rfft(x[i:i + N] * np.hanning(N))) for i in range(0, len(x) - N, H)]
    S = 20 * np.log10(np.array(fr).T + 1e-6)
    S = np.clip((S - S.max() + 70) / 70, 0, 1)[::-1]
    im = Image.fromarray((S * 255).astype(np.uint8)).resize((900, 160))
    rows.append((p.split("/")[-1], im))
out = Image.new("L", (900, 180 * len(rows)), 0)
d = ImageDraw.Draw(out)
for i, (n, im) in enumerate(rows):
    out.paste(im, (0, i * 180 + 18)); d.text((4, i * 180 + 2), n, fill=255)
out.save(sys.argv[1])
