#!/usr/bin/env python3
"""Planos de Véspera-9: rejilla de regiones -> PNG (tema 'dark' para Foundry, 'paper' para el PDF)
y muros/puertas para las escenas. Salida: build/maps/<deck>-<tema>.png y build/maps/walls.json

Unidad: 1 casilla = 1 cuadro de Foundry (100 px). Lienzo 40x26 casillas -> 4000x2600 px.
"""
import json
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "build", "maps")
G = 100                      # px por casilla
W, H = 40, 26                # casillas

# ---------------------------------------------------------------- diseño
# región -> lista de rectángulos (x, y, w, h). 'hall' = pasillos + núcleo (una sola región)
CORE = (0, 0, 0, 0)

DECKS = {
    "c7": {
        "titulo": "SECTOR C-7 · ESQUEMA FUNCIONAL",
        "nocore": True,
        "rooms": {
            "X": [(17, 0, 6, 2)],
            "1": [(15, 2, 10, 6)],
            "3": [(4, 3, 4, 4)],
            "2": [(27, 3, 3, 3)],
            "8": [(27, 6, 9, 6)],
            "9": [(30, 12, 3, 5)],
            "10": [(28, 17, 6, 4)],
            "4": [(19, 8, 2, 5), (14, 13, 7, 2)],
            "5": [(14, 15, 7, 5)],
            "6": [(14, 20, 7, 2)],
            "11": [(12, 20, 2, 2)],
            "7": [(2, 16, 10, 6)],
            "12": [(2, 22, 10, 4)],
        },
        "hall": [(8, 4, 7, 2), (5, 7, 2, 9), (25, 4, 2, 2), (21, 20, 7, 2)],
        "doors": [((19, 2), "h", 2), ((8, 4), "v", 2), ((15, 4), "v", 2), ((5, 7), "h", 2), ((5, 16), "h", 2), ((25, 4), "v", 2),
                  ((27, 4), "v", 1), ((28, 6), "h", 1), ((31, 12), "h", 1), ((30, 17), "h", 2), ((19, 8), "h", 2), ((16, 15), "h", 2),
                  ((16, 20), "h", 2), ((14, 20), "v", 2), ((12, 20), "v", 2), ((6, 22), "h", 2), ((21, 20), "v", 2), ((28, 20), "v", 1)],
        "labels": {"X": "ATRACADERO", "1": "CONTROL C-0", "2": "PORTILLA P-2", "3": "ESCLUSA E-1", "4": "GALERÍA L-4", "5": "CAVIDAD DE CRÍA", "6": "PASO ALTO",
                   "7": "REFUGIO R-3", "8": "BOMBA P-2", "9": "DRENAJE H-4", "10": "VÁLVULA V-12", "11": "PORTILLO", "12": "JUNTA J-17"},
        "decor": {
            "1": [("rect", 16, 2.5, 8, 1, "consola")],
            "7": [("row", 3, 17, 8, 1, "colchón"), ("row", 3, 20, 8, 1, "colchón"), ("circle", 9.5, 18.8, 0.4, "sumidero")],
            "8": [("circle", 30, 9, 1.3, "bomba"), ("rect", 33, 7, 2, 4, "depósito")],
            "10": [("circle", 31, 19, 1.2, "válvula")],
            "5": [("circle", 16, 17.5, 0.5, "huevo"), ("circle", 17.3, 17, 0.5, "huevo"), ("circle", 18.6, 17.6, 0.5, "huevo"), ("circle", 17.6, 18.6, 0.5, "huevo")],
            "12": [("rect", 3, 23, 8, 1, "colector roto")],
        },
    },
    "b4": {
        "titulo": "FRENTE B-4 · MANTENIMIENTO DE BOMBEO",
        "nocore": True,
        "rooms": {
            "B1": [(4, 4, 12, 8)], "B2": [(16, 4, 8, 8)], "B3": [(24, 4, 10, 8)],
            "B4": [(4, 14, 10, 7)], "B5": [(14, 14, 14, 9)], "B6": [(28, 14, 6, 7)], "B7": [(18, 23, 6, 2)],
        },
        "hall": [(4, 12, 30, 2)],
        "doors": [((9, 12), "h", 2), ((19, 12), "h", 2), ((28, 12), "h", 2), ((8, 14), "h", 2), ((20, 14), "h", 2), ((30, 14), "h", 2), ((20, 23), "h", 2)],
        "labels": {"B1": "COLECTOR B-4", "B2": "LABORATORIO", "B3": "BARRACÓN", "B4": "TALLER", "B5": "GARAJE LINCE-6", "B6": "SOPORTE VITAL", "B7": "ESCLUSA"},
        "decor": {
            "B1": [("circle", 8, 8, 2, "colector"), ("rect", 12, 5, 3, 1, "filtro")],
            "B2": [("rect", 17, 5, 6, 1, "terminal")],
            "B3": [("row", 25, 5, 8, 1, "litera"), ("row", 25, 10, 8, 1, "litera")],
            "B4": [("rect", 5, 15, 8, 1, "banco")],
            "B5": [("rect", 16, 16, 9, 5, "rover")],
            "B6": [("rect", 29, 15, 4, 1, "cartuchos")],
        },
    },
}

RUTA = {
    "nodos": {"BASTIÓN": (8, 4), "B-4": (12, 9), "R-12": (13, 19), "C-7": (30, 20), "P-0 · D-1 · F-2": (3, 1)},
    "tramos": [("BASTIÓN", "B-4", "8 km · 25–40 min"), ("B-4", "R-12", "18 km · roca"), ("R-12", "C-7", "25 km · glaciar fracturado")],
    "atajo": ("B-4", "C-7", "Atajo 32 km · llanura fracturada"),
}

TEMAS = {
    "crt": dict(bg=(2, 9, 4), grid=(6, 34, 12), floor=(4, 20, 8), hall=(5, 27, 10), wall=(90, 255, 130), label=(170, 255, 180),
                text=(90, 225, 120), decor=(8, 44, 18), decor_line=(60, 190, 90), door=(220, 255, 140), blind=(255, 90, 70)),
    "dark": dict(bg=(9, 24, 30), grid=(22, 52, 60), floor=(16, 44, 52), hall=(20, 56, 64), wall=(205, 232, 228), label=(224, 162, 74),
                 text=(190, 220, 216), decor=(34, 82, 92), decor_line=(120, 176, 176), door=(224, 162, 74), blind=(210, 70, 60)),
    "paper": dict(bg=(244, 240, 230), grid=(214, 210, 198), floor=(250, 248, 242), hall=(232, 230, 220), wall=(30, 30, 30), label=(176, 70, 20),
                  text=(60, 60, 60), decor=(220, 216, 204), decor_line=(120, 116, 108), door=(176, 70, 20), blind=(176, 30, 30)),
}


def font(size, bold=False):
    for p in ("/System/Library/Fonts/Helvetica.ttc", "/System/Library/Fonts/Supplemental/Arial.ttf"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size, index=1 if bold and p.endswith(".ttc") else 0)
            except Exception:  # noqa: BLE001
                pass
    return ImageFont.load_default()


def raster(deck):
    """celdas -> región. Devuelve dict (x,y)->id"""
    cell = {}
    for rid, rects in deck["rooms"].items():
        for (x, y, w, h) in rects:
            for i in range(x, x + w):
                for j in range(y, y + h):
                    cell[(i, j)] = rid
    for (x, y, w, h) in deck["hall"]:
        for i in range(x, x + w):
            for j in range(y, y + h):
                cell[(i, j)] = "hall"
    return cell


def door_edges(doors):
    s = set()
    for (x, y), o, n in doors:
        for k in range(n):
            s.add((o, x + (k if o == "h" else 0), y + (k if o == "v" else 0)))
    return s


def edges(cell):
    """aristas entre regiones distintas: ('h', x, y) = horizontal en y; ('v', x, y) = vertical en x."""
    out = set()
    for (x, y), r in cell.items():
        for (dx, dy, o, ex, ey) in ((1, 0, "v", x + 1, y), (-1, 0, "v", x, y), (0, 1, "h", x, y + 1), (0, -1, "h", x, y)):
            if cell.get((x + dx, y + dy)) != r:
                out.add((o, ex, ey))
    return out


def join(lst):
    lst = sorted(set(lst))
    res = []
    for a, b in lst:
        if res and a <= res[-1][1]:
            res[-1] = (res[-1][0], max(res[-1][1], b))
        else:
            res.append((a, b))
    return res


def walls_for(deck):
    cell = raster(deck)
    doors = door_edges(deck["doors"])
    blind = door_edges(deck.get("blind", []))
    hw, vw, hd, vd, hb, vb = {}, {}, {}, {}, {}, {}
    for (o, ex, ey) in edges(cell):
        key = (o, ex, ey)
        if o == "h":
            seg = (ex, ex + 1)
            (hb if key in blind else hd if key in doors else hw).setdefault(ey, []).append(seg)
        else:
            seg = (ey, ey + 1)
            (vb if key in blind else vd if key in doors else vw).setdefault(ex, []).append(seg)
    out = []

    def add(dic, horizontal, door, ds):
        for k, lst in dic.items():
            for a, b in join(lst):
                c = [a * G, k * G, b * G, k * G] if horizontal else [k * G, a * G, k * G, b * G]
                out.append({"c": c, "door": door, "ds": ds, "move": 1, "sense": 1, "sound": 1, "light": 1})
    add(hw, True, 0, 0); add(vw, False, 0, 0)
    add(hd, True, 1, 0); add(vd, False, 1, 0)
    add(hb, True, 1, 2); add(vb, False, 1, 2)     # ds=2 -> cerrada con llave (puerta ciega)
    return out


# ---------------------------------------------------------------- dibujo
S = 2  # supersampling


def brillo(img):
    """Fósforo: halo de las líneas + viñeta de tubo + marca discreta."""
    from PIL import ImageChops, ImageFilter
    glow = img.filter(ImageFilter.GaussianBlur(9))
    img = ImageChops.add(img, glow, scale=1.0)
    vig = Image.new("L", img.size, 0)
    dv = ImageDraw.Draw(vig)
    w, h = img.size
    for k in range(40):
        dv.rectangle([k * w // 120, k * h // 120, w - k * w // 120, h - k * h // 120], fill=int(255 * (k + 1) / 40))
    from PIL import ImageFilter as F
    vig = vig.filter(F.GaussianBlur(60)).point(lambda v: 150 + v * 105 // 255)
    black = Image.new("RGB", img.size, (0, 4, 1))
    return Image.composite(img, black, vig)


def render(deck, tema, conductos=False, redactado=False):
    """redactado=True: plano de portada sin spoilers (nombres de sala tachados y sin mobiliario)."""
    t = TEMAS[tema]
    img = Image.new("RGB", (W * G * S, H * G * S), t["bg"])
    d = ImageDraw.Draw(img)
    px = lambda v: int(v * G * S)  # noqa: E731

    def grid():
        for i in range(W + 1):
            d.line([(px(i), 0), (px(i), px(H))], fill=t["grid"], width=2)
        for j in range(H + 1):
            d.line([(0, px(j)), (px(W), px(j))], fill=t["grid"], width=2)
    grid()

    if not conductos:
        cell = raster(deck)
        for (x, y), r in cell.items():
            d.rectangle([px(x), px(y), px(x + 1), px(y + 1)], fill=t["hall"] if r == "hall" else t["floor"])
        grid()
        for rid, items in ([] if redactado else deck["decor"].items()):
            for it in items:
                if it[0] in ("rect", "row"):
                    kind, x, y, w, h, tipo = it
                    if kind == "row":
                        step = 2
                        for k in range(int(w // step)):
                            x0 = x + k * step
                            d.rectangle([px(x0 + 0.15), px(y + 0.1), px(x0 + step - 0.35), px(y + h - 0.1)], fill=t["decor"], outline=t["decor_line"], width=3)
                    else:
                        d.rectangle([px(x), px(y), px(x + w), px(y + h)], fill=t["decor"], outline=t["decor_line"], width=3)
                else:
                    _, x, y, r, tipo = it
                    d.ellipse([px(x - r), px(y - r), px(x + r), px(y + r)], fill=t["decor"], outline=t["decor_line"], width=3)
        for w in walls_for(deck):
            x1, y1, x2, y2 = [v * S for v in w["c"]]
            if w["door"]:
                col = t["blind"] if w.get("ds") == 2 else t["door"]
                d.line([(x1, y1), (x2, y2)], fill=col, width=14)
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                d.ellipse([mx - 10, my - 10, mx + 10, my + 10], fill=col)
            else:
                d.line([(x1, y1), (x2, y2)], fill=t["wall"], width=12)
        cx, cy, cw, ch = CORE
        if not deck.get("nocore"):
            d.rectangle([px(cx + 0.4), px(cy + 0.5), px(cx + 1.8), px(cy + 2.4)], outline=t["decor_line"], width=4)
            d.line([(px(cx + 0.4), px(cy + 0.5)), (px(cx + 1.8), px(cy + 2.4))], fill=t["decor_line"], width=3)
            d.line([(px(cx + 1.8), px(cy + 0.5)), (px(cx + 0.4), px(cy + 2.4))], fill=t["decor_line"], width=3)
            for k in range(6):
                d.line([(px(cx + 2.2), px(cy + 0.6 + k * 0.8)), (px(cx + 3.6), px(cy + 0.6 + k * 0.8))], fill=t["decor_line"], width=4)
            d.text((px(cx + 2), px(cy + 5.45)), "NÚCLEO", fill=t["text"], font=font(34, True), anchor="mm")
        fn, ft = font(88, True), font(30, True)
        for rid, rects in deck["rooms"].items():
            x, y, w, h = max(rects, key=lambda r: r[2] * r[3])
            cx_, cy_ = px(x + w / 2), px(y + h / 2)
            if rid in deck["labels"]:
                d.text((cx_, cy_ - 22), rid, fill=t["label"], font=fn, anchor="mm")
                if redactado:   # barra de censura del ancho del nombre
                    bw = d.textlength(deck["labels"][rid], font=ft) / 2
                    d.rectangle([cx_ - bw, cy_ + 32, cx_ + bw, cy_ + 68], fill=t["wall"])
                else:
                    d.text((cx_, cy_ + 50), deck["labels"][rid], fill=t["text"], font=ft, anchor="mm")
            else:
                d.text((cx_, cy_), rid, fill=t["label"], font=font(46, True), anchor="mm")
        if "blind" in deck:
            (bx, by), _, n = deck["blind"][0]
            d.text((px(bx + 1), px(by + 0.55)), "PUERTA CIEGA", fill=t["blind"], font=font(24, True), anchor="mm")
    else:
        wd = int(G * S * 0.62)
        for (x1, y1, x2, y2) in deck["segs"]:
            d.line([(px(x1 + .5), px(y1 + .5)), (px(x2 + .5), px(y2 + .5))], fill=t["wall"], width=wd + 14)
        for (x1, y1, x2, y2) in deck["segs"]:
            d.line([(px(x1 + .5), px(y1 + .5)), (px(x2 + .5), px(y2 + .5))], fill=t["hall"], width=wd - 6)
        for (x, y, code, nombre) in deck["nodos"]:
            r = 0.55
            d.ellipse([px(x + .5 - r), px(y + .5 - r), px(x + .5 + r), px(y + .5 + r)], fill=t["bg"], outline=t["label"], width=6)
            d.text((px(x + .5), px(y + .5)), code, fill=t["label"], font=font(30, True), anchor="mm")
            d.text((px(x + .5), px(y + 1.5)), nombre, fill=t["text"], font=font(26, True), anchor="mm")
    d.text((px(0.5), px(0.35)), deck["titulo"] + (" · EXTRACTO CLASIFICADO" if redactado else ""), fill=t["label"], font=font(40, True), anchor="lm")
    d.text((px(W - 0.5), px(H - 0.35)), "NÁDIR · 1 casilla = 1,5 m", fill=t["text"], font=font(26), anchor="rm")
    img = img.resize((W * G, H * G), Image.LANCZOS)
    if tema == "crt":
        img = brillo(img)
    return img


def render_ruta(tema):
    t = TEMAS[tema]
    S2 = 2
    img = Image.new("RGB", (W * G * S2 // 2, H * G * S2 // 2), t["bg"])
    d = ImageDraw.Draw(img)
    u = G * S2 // 2
    for i in range(0, W + 1, 2):
        d.line([(i * u, 0), (i * u, H * u)], fill=t["grid"], width=1)
    for j in range(0, H + 1, 2):
        d.line([(0, j * u), (W * u, j * u)], fill=t["grid"], width=1)
    N = RUTA["nodos"]
    a, b, lab = RUTA["atajo"]
    (x1, y1), (x2, y2) = N[a], N[b]
    for k in range(0, 40, 2):
        f0, f1 = k / 40, (k + 1) / 40
        d.line([((x1 + (x2 - x1) * f0) * u, (y1 + (y2 - y1) * f0) * u), ((x1 + (x2 - x1) * f1) * u, (y1 + (y2 - y1) * f1) * u)], fill=t["blind"], width=8)
    d.text((((x1 + x2) / 2 + 1) * u, ((y1 + y2) / 2 - 1.2) * u), lab, fill=t["blind"], font=font(40, True))
    for a_, b_, lab in RUTA["tramos"]:
        (x1, y1), (x2, y2) = N[a_], N[b_]
        d.line([(x1 * u, y1 * u), (x2 * u, y2 * u)], fill=t["wall"], width=14)
        d.text((((x1 + x2) / 2 + 0.8) * u, ((y1 + y2) / 2) * u), lab, fill=t["text"], font=font(38, True))
    for n, (x, y) in N.items():
        r = 0.7
        d.ellipse([(x - r) * u, (y - r) * u, (x + r) * u, (y + r) * u], fill=t["bg"], outline=t["label"], width=8)
        d.text(((x + 1.1) * u, y * u), n, fill=t["label"], font=font(56, True), anchor="lm")
    d.text((u, H * u - u), "SUPERFICIE DE NÁDIR · RUTAS DE B-4 A C-7 (esquema, no a escala)", fill=t["text"], font=font(36, True), anchor="lm")
    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    allw = {}
    for name, deck in DECKS.items():
        allw[name] = walls_for(deck)
        for tema in TEMAS:
            render(deck, tema).save(os.path.join(OUT, "%s-%s.png" % (name, tema)))
    for tema in TEMAS:
        im = render_ruta(tema)
        if tema == "crt":
            im = brillo(im)
        im.save(os.path.join(OUT, "ruta-%s.png" % tema))
    json.dump(allw, open(os.path.join(OUT, "walls.json"), "w"), indent=1)
    print({k: len(v) for k, v in allw.items()})


if __name__ == "__main__":
    main()
