#!/usr/bin/env python3
"""Postproceso de art_src/raw -> art_final: gradación común (teal/ámbar + viñeta + grano) en escenas y retratos
(JPG) y recorte de fondo blanco en los tokens (PNG con alfa).

Uso: python3 tools/post_images.py [--force]
Lo consumen tools/build_pdf.py (art_final/*.jpg) y tools/build_foundry.py (art_final/tok-*.png).
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "art_src", "raw")
OUT = os.path.join(ROOT, "art_final")
os.makedirs(OUT, exist_ok=True)
FORCE = "--force" in sys.argv
rng = np.random.default_rng(7)


def grade(im, up=1.0):
    im = im.convert("RGB")
    im = im.resize((int(im.width * up), int(im.height * up)), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.2, 60, 3))
    a = np.asarray(im).astype(np.float32) / 255.0
    lum = (a * [0.299, 0.587, 0.114]).sum(2, keepdims=True)
    a = lum + (a - lum) * 0.9                                   # desaturar
    sh = np.array([0.02, 0.07, 0.09], np.float32)               # sombras -> teal
    hi = np.array([0.07, 0.035, -0.02], np.float32)             # luces -> ámbar
    a = a + sh * (1 - lum) * 0.9 + hi * lum * 0.9
    a = np.clip((a - 0.5) * 1.07 + 0.5, 0, 1)
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    a = a * (1 - np.clip(r - 0.55, 0, 1) ** 1.6 * 0.5)[..., None]   # viñeta
    a = a + rng.normal(0, 0.018, (h, w, 1)).astype(np.float32)       # grano
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def recortar_token(im):
    """Fondo rosa/magenta con degradado: se estima el color de fondo de cada fila con las columnas de los bordes
    y es fondo todo píxel cercano a él (también los huecos entre brazos y piernas)."""
    rgb = im.convert("RGB")
    f = np.asarray(rgb).astype(np.float32)
    h, w = f.shape[:2]
    edge = np.concatenate([f[:, :10], f[:, -10:]], axis=1)                    # (h, 20, 3)
    row = np.median(edge, axis=1)                                             # color de fondo por fila
    row = np.stack([np.convolve(np.pad(row[:, c], 12, mode="edge"), np.ones(25) / 25, mode="valid") for c in range(3)], 1)
    d = np.abs(f - row[:, None, :]).sum(2)
    m = np.clip(np.minimum(f[..., 0], f[..., 2]) - f[..., 1], 0, None)
    sat = f.max(2) - f.min(2)
    bg = (d < 70) & (m > 18) & (sat > 30)
    # crecimiento desde los bordes por píxeles rosados saturados (cubre degradados que el modelo por filas no alcanza)
    from collections import deque
    ok = (m > 22) & (sat > 38)
    a16 = f.astype(np.int16)
    seen = np.zeros((h, w), bool)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if ok[y, x]:
                seen[y, x] = True; q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if ok[y, x] and not seen[y, x]:
                seen[y, x] = True; q.append((y, x))
    while q:
        y, x = q.popleft()
        c = a16[y, x]
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and ok[ny, nx] and np.abs(a16[ny, nx] - c).sum() < 24:
                seen[ny, nx] = True; q.append((ny, nx))
    bg = bg | seen
    alpha = np.where(bg, 0.0, 255.0)
    # suavizado del borde
    al = Image.fromarray(alpha.astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.0))
    near = np.asarray(al.filter(ImageFilter.MaxFilter(7))) < 255
    spill = np.where(near, m * 0.75, 0)
    f[..., 0] = np.clip(f[..., 0] - spill, 0, 255); f[..., 2] = np.clip(f[..., 2] - spill, 0, 255)
    out = Image.fromarray(f.astype(np.uint8)).convert("RGBA")
    out.putalpha(al)
    bbox = al.point(lambda v: 255 if v > 40 else 0).getbbox()
    if bbox:
        pad = 6
        out = out.crop((max(0, bbox[0] - pad), max(0, bbox[1] - pad), min(w, bbox[2] + pad), min(h, bbox[3] + pad)))
    return out


LOGO = os.path.join(ROOT, "brand", "MR_09_Monograma_Marfil_Transparente.png")
_logo = None


def marca(im, frac=0.05, alpha=0.42, margen=0.018, token=False):
    """Monograma MR discreto: esquina inferior derecha (en tokens, junto a los pies)."""
    global _logo
    if _logo is None:
        _logo = Image.open(LOGO).convert("RGBA")
        bb = _logo.getchannel("A").getbbox()
        _logo = _logo.crop(bb)
    im = im.convert("RGBA")
    w, h = im.size
    lw = max(18, int(w * frac))
    lg = _logo.resize((lw, int(lw * _logo.height / _logo.width)), Image.LANCZOS)
    a = lg.getchannel("A").point(lambda v: int(v * alpha))
    lg.putalpha(a)
    m = int(min(w, h) * margen)
    if token:
        al = im.getchannel("A")
        bb = al.point(lambda v: 255 if v > 40 else 0).getbbox() or (0, 0, w, h)
        x, y = bb[2] - lw - m, bb[3] - lg.height - m
    else:
        x, y = w - lw - m, h - lg.height - m
    im.alpha_composite(lg, (max(0, x), max(0, y)))
    return im


def main():
    n = 0
    for f in sorted(os.listdir(RAW)):
        if not f.endswith(".png"):
            continue
        iid = f[:-4]
        if iid.startswith("tok-"):
            dst = os.path.join(OUT, iid + ".png")
            if os.path.exists(dst) and not FORCE:
                continue
            im = Image.open(os.path.join(RAW, f))
            if im.mode == "RGBA" and im.getextrema()[3][0] == 0:      # Codex ya entrega alfa real
                bbox = im.getchannel("A").point(lambda v: 255 if v > 30 else 0).getbbox()
                marca(im.crop(bbox) if bbox else im, 0.09, 0.5, 0.0, token=True).save(dst)
            else:
                recortar_token(im).save(dst)
        else:
            dst = os.path.join(OUT, iid + ".jpg")
            if os.path.exists(dst) and not FORCE:
                continue
            marca(grade(Image.open(os.path.join(RAW, f)))).convert("RGB").save(dst, quality=88, optimize=True)
        n += 1
        print("ok", iid)
    print(n, "procesadas")


if __name__ == "__main__":
    main()
