#!/usr/bin/env python3
"""Plano operativo de C-7 (esquema, no a escala) en SVG para el PDF.

Muestra atmósferas, zonas inundables según H-4, compuertas con su estado, rutas, conducciones
y equipos críticos. La topología coincide con la planta cuadriculada de tools/maps.py.
Uso: python3 tools/plano_operativo.py  ->  build/maps/c7-operativo.svg
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "build", "maps", "c7-operativo.svg")

W, H = 1700, 1120
C = dict(vacio="#1f2a2e", roca="#ebe5d8", pres="#cfe6e2", sinaire="#d9d4c7", cav="#d8c3a5", agua="#9cc3d8",
         tinta="#1d2224", amb="#c8791c", teal="#0f3a40", rojo="#b0301e", verde="#2f7d4a", gris="#6c7476", ama="#d6a400")

S = []


def add(x):
    S.append(x)


def rect(x, y, w, h, fill, stroke=C["tinta"], sw=2.5, extra=""):
    add('<rect x="%d" y="%d" width="%d" height="%d" fill="%s" stroke="%s" stroke-width="%s" %s/>' % (x, y, w, h, fill, stroke, sw, extra))


def text(x, y, t, size=15, weight=600, fill=None, anchor="middle", italic=False):
    fill = fill or C["tinta"]
    halo = '' if fill in ("#fff", "#e9eeee", "#9fb0b3", "#c9d4d6") else ' paint-order="stroke" stroke="#fbf9f4" stroke-width="4" stroke-linejoin="round"'
    add('<text x="%d" y="%d" font-size="%d" font-weight="%d" fill="%s" text-anchor="%s"%s%s>%s</text>' % (
        x, y, size, weight, fill, anchor, ' font-style="italic"' if italic else "", halo, t))


def zona(x, y, w, h, kind, num, nombre, sub=""):
    fill = {"pres": C["pres"], "sinaire": "url(#sinaire)", "cav": "url(#cav)", "agua": "url(#agua)"}[kind]
    rect(x, y, w, h, fill)
    if num:
        add('<circle cx="%d" cy="%d" r="15" fill="%s"/>' % (x + 20, y + 20, C["amb"]))
        text(x + 20, y + 25, num, 13, 800, "#fff")
    text(x + w / 2, y + h / 2 - (6 if sub else -5), nombre, 17, 800)
    if sub:
        text(x + w / 2, y + h / 2 + 16, sub, 12.5, 500, C["gris"])


def puerta(x, y, horizontal, estado, etiqueta, lado="d"):
    col = {"abierta": C["verde"], "esclusa": C["teal"], "atascada": C["rojo"], "atornillada": C["amb"], "cerrada": C["tinta"]}[estado]
    if horizontal:
        add('<rect x="%d" y="%d" width="28" height="12" fill="%s" stroke="#fff" stroke-width="2"/>' % (x - 14, y - 6, col))
    else:
        add('<rect x="%d" y="%d" width="12" height="28" fill="%s" stroke="#fff" stroke-width="2"/>' % (x - 6, y - 14, col))
    if etiqueta:
        dx, anc = {"d": (20, "start"), "i": (-20, "end"), "a": (0, "middle"), "b": (0, "middle")}[lado]
        dy = {"a": -16, "b": 26}.get(lado, 5)
        text(x + dx, y + dy, etiqueta, 12, 700, col, anc)


def linea(pts, col, sw=4, dash="", marker=""):
    d = " ".join("%s%d,%d" % ("M" if i == 0 else "L", px, py) for i, (px, py) in enumerate(pts))
    add('<path d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round" %s %s/>' % (
        d, col, sw, ('stroke-dasharray="%s"' % dash) if dash else "", ('marker-end="url(#%s)"' % marker) if marker else ""))


def etiqueta(x, y, t, col=None, anchor="start", size=12):
    text(x, y, t, size, 600, col or C["gris"], anchor, italic=True)


add('<defs>'
    '<pattern id="sinaire" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="14" height="14" fill="%s"/><line x1="0" y1="0" x2="0" y2="14" stroke="#b9b2a2" stroke-width="3"/></pattern>'
    '<pattern id="cav" width="18" height="18" patternUnits="userSpaceOnUse"><rect width="18" height="18" fill="%s"/><circle cx="9" cy="9" r="2.2" fill="#b39572"/></pattern>'
    '<pattern id="agua" width="20" height="10" patternUnits="userSpaceOnUse"><rect width="20" height="10" fill="#d9e8f0"/><path d="M0,6 Q5,2 10,6 T20,6" stroke="%s" stroke-width="2.4" fill="none"/></pattern>'
    '<marker id="flecha" markerWidth="10" markerHeight="10" refX="6" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="%s"/></marker>'
    '<marker id="flechaa" markerWidth="10" markerHeight="10" refX="6" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="%s"/></marker>'
    '</defs>' % (C["sinaire"], C["cav"], "#4f8db0", "#3f7fa6", C["amb"]))

# fondo
rect(0, 0, W, H, C["roca"], "none", 0)
rect(0, 0, 1420, 120, C["vacio"], "none", 0)
text(20, 30, "SUPERFICIE · VACÍO", 14, 800, "#e9eeee", "start")
text(20, 50, "sin aire, sin sonido por el aire; traje cerrado", 12, 500, "#9fb0b3", "start")
text(710, 1100, "SECTOR C-7 · PLANO OPERATIVO (esquema, no a escala)", 20, 800, C["teal"])

# --- conducciones (debajo de las zonas) ---
# línea de producción: bolsa de salmuera -> V-12 -> J-17
linea([(1400, 880), (1180, 880), (1080, 880), (1080, 820)], "#3f7fa6", 9)
linea([(1080, 880), (480, 880), (480, 975), (450, 975)], "#3f7fa6", 9)
add('<path d="M452,962 L430,975 L452,988 z" fill="#3f7fa6"/>')
etiqueta(1395, 870, "línea de producción: salmuera a presión desde la bolsa del macizo", "#3f7fa6", "end")
# drenaje H-4: J-17 -> fondo -> inspección H-4 -> túnel -> P-2
linea([(250, 1045), (1275, 1045), (1275, 670)], "#2b5d7a", 6, "2,6")
etiqueta(700, 1035, "drenaje H-4 (lleva el agua del tramo bajo a P-2)", "#2b5d7a")
# bypass DB-3 (derivación B) en L-4
linea([(720, 445), (985, 445), (985, 640), (1200, 640)], C["rojo"], 3, "8,6")
etiqueta(992, 600, "derivación B", C["rojo"])
etiqueta(992, 616, "bypass DB-3 de Ivo", C["rojo"])
# línea del actuador de V-12
linea([(800, 300), (860, 300), (860, 395), (950, 395), (950, 700), (1040, 700)], C["ama"], 4, "4,5")
etiqueta(870, 388, "línea del actuador V-12 (cortada en EL-4)", "#8a6c00")

# --- zonas ---
rect(560, 30, 220, 70, "#33454a", "#9fb0b3")
text(670, 60, "[X] ATRACADERO", 15, 800, "#fff")
text(670, 80, "rovers · sin toma de red", 12, 500, "#c9d4d6")
rect(1250, 30, 160, 70, "#33454a", "#9fb0b3")
text(1330, 60, "[2] PORTILLA P-2", 14, 800, "#fff")
text(1330, 80, "conector · costra", 12, 500, "#c9d4d6")
linea([(780, 65), (1250, 65)], "#9fb0b3", 2, "6,6")
etiqueta(1015, 58, "5 min a pie · carrete de cable 200 m", "#c9d4d6", "middle")

zona(520, 170, 300, 160, "pres", "1", "CONTROL C-0", "aire · banco 48 UE · 6 trajes")
puerta(670, 145, False, "esclusa", "esclusa exterior (10 min)", "d")
linea([(670, 100), (670, 170)], C["teal"], 3)

# pasillo oeste y E-1
rect(300, 230, 220, 40, C["pres"])
text(410, 256, "pasillo oeste", 12, 500, C["gris"])
zona(230, 200, 70, 100, "sinaire", "3", "E-1", "")
puerta(300, 250, False, "atascada", "", "d")
etiqueta(225, 196, "deformada · igualar si H-4 ≤ 3 (6 UE)", C["rojo"], "end")
add('<text x="265" y="290" font-size="11" text-anchor="middle" fill="%s">Serrat</text>' % C["rojo"])

# ruta baja (inundable)
rect(210, 300, 60, 370, "url(#agua)")
text(240, 470, "RUTA", 12, 800, C["teal"])
text(240, 486, "BAJA", 12, 800, C["teal"])
etiqueta(205, 420, "agua según H-4:", "#2b5d7a", "end")
etiqueta(205, 436, "≤1 tobillo · 2 media pierna", "#2b5d7a", "end")
etiqueta(205, 452, "3 rodilla · 4+ cerrada", "#2b5d7a", "end")
# corredor dañado (Milena) hacia J-17
rect(40, 560, 170, 36, "url(#agua)")
rect(25, 596, 30, 324, "url(#agua)")
etiqueta(60, 552, "corredor dañado · Milena", C["rojo"])

# R-3
zona(90, 670, 330, 200, "pres", "7", "REFUGIO R-3", "13 personas · 6 kg CO₂ a las 09:36")
puerta(240, 670, True, "esclusa", "", "a")
etiqueta(292, 664, "esclusa principal · 4 por ciclo", C["teal"])
add('<circle cx="160" cy="830" r="14" fill="#fff" stroke="%s" stroke-width="3"/><text x="160" y="835" font-size="10" text-anchor="middle">⊗</text>' % C["tinta"])
etiqueta(180, 850, "sumidero (agua a H-4 = 4)", "#2b5d7a")
add('<line x1="90" y1="870" x2="420" y2="870" stroke="%s" stroke-width="7" stroke-dasharray="14,8"/>' % C["rojo"])
etiqueta(255, 890, "sello inferior: falla 120 min tras H-4 = 6", C["rojo"], "middle")

# cámara de servicio y portillo
zona(420, 720, 100, 80, "sinaire", "", "cámara", "de servicio")
puerta(420, 760, False, "esclusa", "", "i")
etiqueta(425, 712, "compuerta pequeña (2 por ciclo)", C["teal"], "start")
puerta(520, 760, False, "atornillada", "", "d")

# J-17 tramo bajo
zona(60, 920, 380, 110, "agua", "12", "J-17 · TRAMO BAJO", "fractura · Teo Mahr · 3 costreros")

# L-4
rect(680, 330, 40, 200, "url(#sinaire)")
rect(560, 470, 160, 40, "url(#sinaire)")
puerta(700, 330, True, "cerrada", "compuerta L-4", "i")
text(700, 420, "4", 13, 800, C["amb"])
text(650, 495, "GALERÍA L-4 · gas de cavidad", 12, 700)
add('<rect x="722" y="372" width="22" height="16" fill="%s" stroke="%s"/>' % (C["ama"], C["tinta"]))
etiqueta(748, 378, "caja EL-4 (10 min)", "#8a6c00")

# cría
zona(520, 520, 300, 170, "cav", "5", "CAVIDAD DE CRÍA", "puesta · 3 defensores · Lisán")
etiqueta(830, 560, "válvula auxiliar: fuga de aire", C["gris"])

# paso alto y fractura
zona(520, 700, 300, 46, "sinaire", "6", "PASO ALTO", "")
rect(520, 746, 300, 110, "#bdb3a0", C["tinta"], 1.5, 'stroke-dasharray="4,4"')
text(670, 838, "tramo hundido · caída 3d10", 13, 600, C["gris"])
etiqueta(530, 768, "[11] PORTILLO superior", C["amb"], "start", 14)
etiqueta(530, 786, "atornillado por este lado · armario: 2 C-12", C["amb"])
etiqueta(530, 802, "costra: +20 min desde las 17:36", C["amb"])

# galería de servicio, V-12, H-4, túnel, P-2
rect(820, 710, 180, 30, "url(#sinaire)")
text(910, 731, "galería de servicio", 12, 600, C["gris"])
zona(1000, 680, 170, 120, "sinaire", "10", "VÁLVULA V-12", "seca · actuador muerto")
add('<circle cx="1080" cy="820" r="16" fill="#fff" stroke="%s" stroke-width="4"/>' % C["teal"])
etiqueta(1100, 826, "V-12 (abierta)", C["teal"])
zona(1200, 560, 160, 110, "agua", "9", "H-4 · INSPECCIÓN", "bypass soldado a mano")
rect(1260, 360, 30, 200, "url(#agua)")
etiqueta(1300, 470, "túnel interior inundado", "#2b5d7a")
etiqueta(1300, 486, "40 min a ciegas · H-4 ≤ 4", "#2b5d7a")
zona(1150, 200, 300, 160, "pres", "8", "ESTACIÓN P-2", "Quiroga e Ivo · bomba B")
add('<circle cx="1210" cy="320" r="18" fill="#fff" stroke="%s" stroke-width="4"/><text x="1210" y="325" font-size="11" text-anchor="middle">B</text>' % C["tinta"])
rect(1390, 290, 50, 60, "#e6eef2")
text(1415, 318, "dep.", 11, 600, C["gris"])
text(1415, 332, "decant.", 9, 600, C["gris"])
rect(1310, 100, 40, 100, C["pres"])
puerta(1330, 110, True, "atascada", "", "a")
etiqueta(1360, 150, "cámara de paso", C["teal"])
etiqueta(1360, 166, "1 persona · 5 min", C["teal"])

# --- rutas ---
linea([(520, 285), (300, 285)], C["verde"], 5, "1,0")
linea([(255, 300), (255, 665)], C["verde"], 5)
etiqueta(275, 640, "RUTA BAJA 15–20 min", C["verde"])
linea([(700, 335), (700, 470), (640, 470), (640, 600), (600, 700), (560, 723), (522, 760)], C["amb"], 5, "10,6")
etiqueta(505, 512, "RUTA ALTA", C["amb"], "end")
etiqueta(505, 528, "1 h 30 min–2 h 30 min", C["amb"], "end")
linea([(1275, 560), (1275, 362)], C["rojo"], 3, "3,6")

# --- leyenda ---
lx, ly = 1450, 150
rect(lx - 10, ly - 30, 255, 950, "#fbf9f4", C["tinta"], 1.5)
text(lx + 117, ly - 6, "LEYENDA", 15, 800, C["teal"])
items = [("pres", "presurizado y respirable"), ("sinaire", "sin aire: gas de cavidad"), ("cav", "cavidad natural (hábitat)"),
         ("agua", "inunda según H-4"), ("vacio", "superficie al vacío")]
y = ly + 20
for k, t in items:
    fill = {"pres": C["pres"], "sinaire": "url(#sinaire)", "cav": "url(#cav)", "agua": "url(#agua)", "vacio": C["vacio"]}[k]
    rect(lx, y, 36, 22, fill, C["tinta"], 1.5)
    text(lx + 46, y + 16, t, 13, 500, anchor="start")
    y += 34
y += 6
text(lx, y, "Compuertas", 13, 800, C["teal"], "start")
y += 18
for est, t in [("esclusa", "esclusa operativa"), ("cerrada", "cerrada, se abre"), ("atascada", "deformada / atascada"), ("atornillada", "atornillada por fuera")]:
    puerta(lx + 14, y + 4, True, est, "", "d")
    text(lx + 46, y + 9, t, 13, 500, anchor="start")
    y += 28
y += 6
text(lx, y, "Rutas", 13, 800, C["teal"], "start")
y += 16
for col, dash, t in [(C["verde"], "", "ruta baja (camillas)"), (C["amb"], "10,6", "ruta alta (una a una)"), (C["rojo"], "3,6", "túnel desesperado")]:
    linea([(lx, y + 4), (lx + 36, y + 4)], col, 5, dash)
    text(lx + 46, y + 9, t, 13, 500, anchor="start")
    y += 26
y += 6
text(lx, y, "Conducciones", 13, 800, C["teal"], "start")
y += 16
for col, sw, dash, t in [("#3f7fa6", 8, "", "línea de producción"), ("#2b5d7a", 5, "2,6", "drenaje H-4"), (C["rojo"], 3, "8,6", "bypass DB-3"), (C["ama"], 4, "4,5", "línea actuador V-12")]:
    linea([(lx, y + 4), (lx + 36, y + 4)], col, sw, dash)
    text(lx + 46, y + 9, t, 13, 500, anchor="start")
    y += 26
y += 10
text(lx, y, "Cambian con los relojes", 13, 800, C["teal"], "start")
for t in ["H-4 ≥ 2: J-17 solo con V-12 cerrada", "H-4 ≥ 4: ruta baja cerrada;", "   agua en el sumidero de R-3", "H-4 = 6: sello de R-3 en 120 min",
          "V-12 cerrada: H-4 −1 y −1/h;", "   migración por la galería", "17:36: costra en el portillo",
          "E-1 igualada: costreros al marco", "cada 2 ciclos en L-4: Atención +1"]:
    y += 19
    text(lx, y, t, 12, 500, anchor="start")

svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" font-family="Avenir Next Condensed, Avenir Next, Helvetica, sans-serif">%s</svg>' % (W, H, "".join(S))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w").write(svg)
# versión girada 90° para ocupar una página A4 vertical entera en el PDF
vert = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" font-family="Avenir Next Condensed, Avenir Next, Helvetica, sans-serif"><g transform="translate(%d,0) rotate(90)">%s</g></svg>' % (H, W, H, "".join(S))
open(OUT.replace(".svg", "-v.svg"), "w").write(vert)
print(OUT)
