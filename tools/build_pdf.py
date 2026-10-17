#!/usr/bin/env python3
"""Maqueta «Nádir: Sangre bajo el hielo» como revista científica (A4) a partir de docs/texto/*.md.

Pipeline: markdown propio -> HTML + CSS -> Chrome headless (--print-to-pdf) -> PyMuPDF (índice con páginas, 2.ª pasada).
Uso: python3 tools/build_pdf.py [--draft]     (--draft: sin 2.ª pasada)
Salida: build/Hora-de-Silencio.pdf  (+ build/pdf/libro.html)
"""
import html
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
ART = os.path.join(ROOT, "art_final")
MAPS = os.path.join(BUILD, "maps")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CANON = json.load(open(os.path.join(ROOT, "docs", "biblia", "canon.json")))
PROMPTS = {}
for _i in json.load(open(os.path.join(ROOT, "docs", "arte", "prompts.json")))["imagenes"]:
    _i["w"], _i["h"] = map(int, _i["size"].split("x"))
    PROMPTS[_i["id"]] = _i

ORDEN = ["00-presentacion", "01-nadir", "02-verdad", "03-costreros", "04-actos-1-2", "05-acto-3", "06-acto-4",
         "07-pnj", "08-reglas", "09-documentos", "10-tripulacion"]
SECCION = {"00-presentacion": "Presentación", "01-nadir": "Contexto", "02-verdad": "Informe técnico", "03-costreros": "Artículo",
           "04-actos-1-2": "Actos I y II", "05-acto-3": "Acto III", "06-acto-4": "Acto IV", "07-pnj": "Personas",
           "08-reglas": "Métodos", "09-documentos": "Anexos", "10-tripulacion": "Cuadrilla M-4"}
MAPAS = {"04-actos-1-2": [("b4", "Plano del Frente B-4, punto de partida."), ("ruta", "Rutas de superficie de B-4 a C-7.")],
         "05-acto-3": [("c7", "Esquema funcional del Sector C-7 con sus doce localizaciones.")]}

fig_n = [0]
usadas = set()
MODO = ["pdf"]          # "foundry": rutas relativas al módulo y sin láminas de página completa
MODULE_ART = "modules/mr-nadir/assets/art/"


def esc(s):
    return html.escape(s, quote=False)


def inline(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?![\*\w])", r"<i>\1</i>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def img_path(iid):
    if MODO[0] == "foundry":
        return MODULE_ART + iid + ".webp" if os.path.exists(os.path.join(ART, iid + ".jpg")) else None
    for ext in ("jpg", "png"):
        p = os.path.join(ART, "%s.%s" % (iid, ext))
        if os.path.exists(p):
            return "file://" + p
    return None


def is_portrait(iid):
    if MODO[0] == "foundry":
        return False
    it = PROMPTS.get(iid)
    return bool(it) and it["h"] > it["w"] * 1.2 and it["tipo"] == "escena"


def figure(iid, cap, mode):
    fig_n[0] += 1
    usadas.add(iid)
    src = img_path(iid)
    inner = '<img src="%s">' % src if src else '<div class="falta">%s</div>' % iid
    pref = "Lám." if iid.startswith("lam-") else "Fig."
    c = '<figcaption><b>%s %d.</b> %s</figcaption>' % (pref, fig_n[0], inline(cap))
    return '<figure class="%s">%s%s</figure>' % (mode, inner, c)


def parse_table(lines):
    rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines if not re.match(r"^\s*\|?\s*:?-{2,}", l)]
    if not rows:
        return ""
    head, body = rows[0], rows[1:]
    h = "".join("<th>%s</th>" % inline(c) for c in head)
    b = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c) for c in r) for r in body)
    cls = ' class="wide"' if len(head) >= 4 else ""
    return '<table%s><thead><tr>%s</tr></thead><tbody>%s</tbody></table>' % (cls, h, b)


def ficha(title, body):
    ls = [l for l in body.strip().splitlines() if l.strip()]
    sub = ls[0] if ls else ""
    stats = ls[1] if len(ls) > 1 else ""
    chips = ""
    for m in re.finditer(r"([A-Za-zÁÉÍÓÚáéíóúñ]+)\s+(\S+)", stats):
        chips += '<span class="chip"><em>%s</em><b>%s</b></span>' % (esc(m.group(1)), esc(m.group(2).strip("·")))
    rest = ""
    for l in ls[2:]:
        m = re.match(r"^([^:]{2,30}):\s*(.*)$", l)
        rest += ("<p><b>%s.</b> %s</p>" % (esc(m.group(1)), inline(m.group(2)))) if m else "<p>%s</p>" % inline(l)
    return '<aside class="ficha"><header><h4>%s</h4><span>%s</span></header><div class="chips">%s</div>%s</aside>' % (
        esc(title), inline(sub), chips, rest)


def md_blocks(text, ctx):
    """Convierte markdown a lista de segmentos [('flow', html) | ('plate', html)]"""
    lines = text.splitlines()
    segs, cur = [], []
    i = 0
    para = []
    state = {"head": None}

    def flush():
        nonlocal para
        if para:
            cur.append("<p>%s</p>" % inline(" ".join(para)))
            para = []

    def emit_head():
        if state["head"]:
            lvl, t, hid = state["head"]
            cur.append('<h%d id="%s">%s</h%d>' % (lvl, hid, inline(t), lvl))
            state["head"] = None
    while i < len(lines):
        l = lines[i]
        if l.startswith("::: "):
            flush()
            emit_head()
            m = re.match(r"^::: (\w+)\s*(.*)$", l)
            kind, title = m.group(1), m.group(2).strip()
            j = i + 1
            buf = []
            while j < len(lines) and not re.match(r"^:::\s*$", lines[j]):
                buf.append(lines[j])
                j += 1
            body = "\n".join(buf)
            i = j + 1
            if kind == "ficha":
                cur.append(ficha(title, body))
            elif kind == "resumen":
                ctx["resumen"] = body
            elif kind == "documento":
                inner = "".join(x for k, x in md_blocks(body, {}) if k == "flow")
                cur.append('<div class="documento"><span class="tape">DOCUMENTO</span><h4>%s</h4>%s</div>' % (esc(title), inner))
            else:
                inner = "".join(x for k, x in md_blocks(body, {}) if k == "flow")
                cur.append('<aside class="caja"><h4>%s</h4>%s</aside>' % (esc(title), inner))
            continue
        if not l.strip():
            flush()
            i += 1
            continue
        m = re.match(r"^(#{1,3}) (.*)$", l)
        if m:
            flush()
            emit_head()
            lvl = len(m.group(1))
            t = m.group(2).strip()
            if lvl == 1:
                ctx["titulo"] = t
            else:
                state["head"] = (lvl, t, "s-" + slug(t))
            i += 1
            continue
        m = re.match(r"^!\[(.*?)\]\((.+?)\)\s*$", l)
        if m:
            flush()
            cap, iid = m.group(1), m.group(2)
            if is_portrait(iid) and state["head"]:
                lvl, t, hid = state["head"]
                state["head"] = None
                if cur:
                    segs.append(("flow", "".join(cur)))
                    cur = []
                fig_n[0] += 1
                usadas.add(iid)
                src = img_path(iid)
                bg = ('<img class="bgimg" src="%s">' % src) if src else ""
                segs.append(("plate", '<section class="plate">' + bg + '<div class="plate-t"><span>Fig. %d</span><h2 id="%s">%s</h2><p>%s</p></div></section>' % (fig_n[0], hid, inline(t), inline(cap))))
            else:
                emit_head()
                mode = "ret" if iid.startswith("ret-") else ("tall" if is_portrait(iid) else "wide")
                cur.append(figure(iid, cap, mode))
            i += 1
            continue
        if l.startswith(">"):
            flush()
            emit_head()
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip("> ").rstrip())
                i += 1
            cur.append("<blockquote>%s</blockquote>" % inline(" ".join(b for b in buf if b)))
            continue
        if l.lstrip().startswith("|"):
            flush()
            emit_head()
            buf = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                buf.append(lines[i])
                i += 1
            cur.append(parse_table(buf))
            continue
        if re.match(r"^\s*([-*]|\d+\.) ", l):
            flush()
            emit_head()
            ordered = bool(re.match(r"^\s*\d+\.", l))
            items = []
            while i < len(lines) and re.match(r"^\s*([-*]|\d+\.) ", lines[i]):
                items.append(re.sub(r"^\s*([-*]|\d+\.) ", "", lines[i]))
                i += 1
                while i < len(lines) and lines[i].startswith("  ") and lines[i].strip() and not re.match(r"^\s*([-*]|\d+\.) ", lines[i]):
                    items[-1] += " " + lines[i].strip()
                    i += 1
            tag = "ol" if ordered else "ul"
            cur.append("<%s>%s</%s>" % (tag, "".join("<li>%s</li>" % inline(x) for x in items), tag))
            continue
        if re.match(r"^-{3,}\s*$", l):
            flush()
            emit_head()
            cur.append("<hr>")
            i += 1
            continue
        emit_head()
        para.append(l.strip())
        i += 1
    flush()
    emit_head()
    if cur:
        segs.append(("flow", "".join(cur)))
    return segs


def mapa(deck, cap):
    fig_n[0] += 1
    src = "file://%s/%s-paper.png" % (MAPS, deck)
    return '<figure class="wide plano"><img src="%s"><figcaption><b>Fig. %d.</b> %s</figcaption></figure>' % (src, fig_n[0], cap)


def capitulo(nombre, num):
    texto = open(os.path.join(ROOT, "docs", "texto", nombre + ".md")).read()
    ctx = {}
    segs = md_blocks(texto, ctx)
    out = list(segs)
    if nombre in MAPAS and out:
        figs = "".join(mapa(d, c) for d, c in MAPAS[nombre])
        k = next(i for i, (kd, _) in enumerate(out) if kd == "flow")
        out[k] = ("flow", figs + out[k][1])
    res = ctx.get("resumen", "")
    kw = ""
    m = re.search(r"Palabras clave:\s*(.*)", res)
    if m:
        kw = m.group(1)
        res = res.replace(m.group(0), "").strip()
    cid = "cap-%d" % num
    op = ('<section class="opener" id="%s"><div class="kicker">%s · N.º %02d</div><h1>%s</h1>'
          '<div class="abstract"><b>Resumen</b><p>%s</p>%s</div></section>') % (
        cid, esc(SECCION[nombre]), num, inline(ctx.get("titulo", "")), inline(res),
        ('<p class="kw"><b>Palabras clave:</b> %s</p>' % esc(kw)) if kw else "")
    body = "".join(('<section class="cols">%s</section>' % h) if k == "flow" else h for k, h in out)
    return cid, ctx.get("titulo", ""), op + body


def hojas():
    out = ['<section class="opener" id="cap-hojas"><div class="kicker">Apéndice · Imprimible</div><h1>Archivos personales</h1>'
           '<div class="abstract"><b>Resumen</b><p>Cinco hojas de la cuadrilla M-4 listas para imprimir: estadísticas, salvaciones, equipo, motivo, vínculo, conflicto e información privada.</p></div></section>']
    for pid, p in CANON["pregenerados"].items():
        e, s = p["estadisticas"], p["salvaciones"]
        sk = "".join("<li><b>%s</b> · entrenado</li>" % esc(x) for x in p["habilidades"].get("entrenado", [])) + \
             "".join("<li><b>%s</b> · experto</li>" % esc(x) for x in p["habilidades"].get("experto", []))
        rec = "".join('<div class="rec"><span>%s</span><p>%s</p><i></i></div>' % (k, inline(v)) for k, v in p["recuerdos"].items())
        ret = img_path("ret-" + pid)
        out.append('''<section class="hoja">
<header><div><div class="kicker">%s%s</div><h2>%s</h2><p>%s</p></div>%s</header>
<div class="stats">%s</div><div class="stats sv">%s</div>
<div class="vit"><div><em>Salud</em><b>%s</b></div><div><em>Heridas</em><b>%s</b></div><div><em>Estrés</em><b>2</b></div><div><em>Pánico</em><b></b></div></div>
<div class="dos"><div><h3>Habilidades</h3><ul>%s</ul></div><div><h3>Equipo</h3><ul>%s</ul></div></div>
<h3>Expediente personal</h3><div class="recs">%s</div>
<p class="nota">Las cifras son sugerencias de aventura; si tu mesa genera personajes con el manual, manda tu hoja.</p></section>''' % (
            esc(p["clase"]), (" · %d años" % p["edad"]) if p["edad"] else "", esc(p["nombre"]), esc(p["papel"]), ('<img src="%s">' % ret) if ret else "",
            "".join('<div><em>%s</em><b>%s</b></div>' % (k.capitalize(), v) for k, v in e.items()),
            "".join('<div><em>%s</em><b>%s</b></div>' % (k.capitalize(), v) for k, v in s.items()),
            p["salud"], p["heridas"], sk, "".join("<li>%s</li>" % esc(x) for x in p["equipo"]), rec))
    return "".join(out)


def plano_conductos():
    fig_n[0] += 1
    n1 = fig_n[0]
    fig_n[0] += 1
    return ('<section class="opener" id="cap-planos"><div class="kicker">Apéndice</div><h1>Planos</h1>'
            '<figure class="plano"><img src="file://%s/c7-paper.png"><figcaption><b>Fig. %d.</b> Sector C-7.</figcaption></figure>'
            '<figure class="plano"><img src="file://%s/ruta-paper.png"><figcaption><b>Fig. %d.</b> Superficie de Nádir: rutas y atajo.</figcaption></figure></section>') % (MAPS, n1, MAPS, fig_n[0])


CSS = r"""
@page { size: A4; margin: 20mm 15mm 22mm 15mm;
  @top-left { content: "NÁDIR · SANGRE BAJO EL HIELO"; font: 600 6.5pt 'Avenir Next Condensed'; letter-spacing: .22em; color:#9a5a14; }
  @top-right { content: "Anales de Biología de Frontera · Vol. 12, n.º 3"; font: 400 7pt 'Avenir Next'; color:#777; }
  @bottom-center { content: counter(page); font: 500 8pt 'Avenir Next'; color:#555; }
  @bottom-left { content: "Mothership 1e · 3–5 jugadores · Número especial ND-17"; font: 400 6.5pt 'Avenir Next'; color:#999; } }
@page plate { size: A4; margin: 0; @top-left{content:none} @top-right{content:none} @bottom-center{content:none} @bottom-left{content:none} }
@page cover { size: A4; margin: 0; @top-left{content:none} @top-right{content:none} @bottom-center{content:none} @bottom-left{content:none} }
@page opener { size: A4; @top-left{content:none} @top-right{content:none} }
:root { --amb:#c8791c; --teal:#0f3a40; --paper:#fbf9f4; --ink:#1d2224; --mut:#6c7476; }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { margin:0; background:#fff; color:var(--ink); font: 9pt/1.42 'Iowan Old Style','Charter','Georgia',serif; hyphens: auto; }
.cover { page: cover; width:100%; height:296.4mm; contain:paint; position:relative; background:#0a1a1f center/cover; color:#fff; break-after:page; overflow:hidden; }
.cover .shade { position:absolute; inset:0; background:linear-gradient(180deg,rgba(5,15,18,.78) 0%,rgba(5,15,18,.0) 32%,rgba(5,15,18,0) 58%,rgba(5,15,18,.88) 100%); }
.cover .mast { position:absolute; top:14mm; left:14mm; right:14mm; display:flex; justify-content:space-between; font:600 8pt 'Avenir Next Condensed'; letter-spacing:.3em; text-transform:uppercase; border-bottom:.4mm solid rgba(255,255,255,.7); padding-bottom:3mm; }
.cover h1 { position:absolute; left:14mm; right:14mm; bottom:50mm; margin:0; font:700 68pt/0.9 'Avenir Next Condensed'; text-transform:uppercase; letter-spacing:.02em; }
.cover h1 span { color:#f0a64a; display:block; font-size:34pt; letter-spacing:.08em; margin-top:3mm; }
.cover .sub { position:absolute; left:14mm; right:14mm; bottom:30mm; font:italic 400 13pt 'Iowan Old Style'; opacity:.92; }
.cover .tag { position:absolute; left:14mm; right:14mm; bottom:14mm; display:flex; justify-content:space-between; font:500 7.5pt 'Avenir Next'; letter-spacing:.18em; text-transform:uppercase; opacity:.85; }
.contra { page: cover; width:100%; height:296.4mm; contain:paint; background:#0a1a1f center/cover; color:#e9eeee; position:relative; break-before:page; overflow:hidden; }
.contra .shade { position:absolute; inset:0; background:linear-gradient(0deg,rgba(5,15,18,.92),rgba(5,15,18,.35) 70%,rgba(5,15,18,.6)); }
.contra .txt { position:absolute; left:20mm; right:20mm; bottom:22mm; font:9pt/1.5 'Iowan Old Style'; }
.contra h3 { font:700 22pt/1 'Avenir Next Condensed'; text-transform:uppercase; color:#f0a64a; margin:0 0 5mm; }
.contra small { display:block; margin-top:6mm; font:400 6.8pt/1.45 'Avenir Next'; opacity:.7; }
.toc { break-before: page; page: opener; padding-top: 8mm; }
.toc h1 { font:700 34pt 'Avenir Next Condensed'; text-transform:uppercase; margin:0 0 2mm; }
.toc .rule { height:.6mm; background:var(--amb); width:40mm; margin-bottom:8mm; }
.toc li { list-style:none; display:flex; align-items:baseline; gap:3mm; padding:2.6mm 0; border-bottom:.2mm solid #ddd; font:500 11pt 'Avenir Next'; }
.toc li i { font:normal 600 7pt 'Avenir Next Condensed'; letter-spacing:.2em; color:var(--amb); width:24mm; text-transform:uppercase; }
.toc li .d { flex:1; border-bottom:.3mm dotted #aaa; transform:translateY(-1mm); }
.toc ul { padding:0; margin:0; }
.toc .nota { font:400 8pt/1.5 'Avenir Next'; color:var(--mut); margin-top:10mm; max-width:120mm; }
.opener { page: opener; break-before: page; padding-top: 6mm; }
.opener .kicker { font:600 8pt 'Avenir Next Condensed'; letter-spacing:.3em; text-transform:uppercase; color:var(--amb); border-top:.8mm solid var(--ink); padding-top:3mm; }
.opener h1 { font:700 44pt/0.95 'Avenir Next Condensed'; text-transform:uppercase; margin:4mm 0 8mm; letter-spacing:.01em; }
.abstract { background:var(--paper); border-left:1.2mm solid var(--amb); padding:5mm 6mm; margin-bottom:8mm; font:400 9.2pt/1.5 'Avenir Next'; color:#333; break-inside:avoid; }
.abstract b { font:700 7pt 'Avenir Next Condensed'; letter-spacing:.3em; text-transform:uppercase; color:var(--teal); }
.abstract p { margin:2mm 0 0; }
.abstract .kw { font-size:8pt; color:var(--mut); }
.cols { column-count:2; column-gap:7mm; column-fill:balance; orphans:3; widows:3; }
.cols p { margin:0 0 2.3mm; text-align:justify; }
h2 { font:700 17pt/1.05 'Avenir Next Condensed'; text-transform:uppercase; letter-spacing:.015em; color:var(--teal); margin:6mm 0 2.5mm; break-after:avoid; border-top:.3mm solid #c9c9c9; padding-top:2.2mm; }
h2::before { content:"§ "; color:var(--amb); }
h3 { font:700 10.5pt 'Avenir Next Condensed'; text-transform:uppercase; letter-spacing:.1em; color:var(--amb); margin:4mm 0 1.2mm; break-after:avoid; }
blockquote { margin:2.5mm 0 3mm; padding:1mm 0 1mm 4mm; border-left:.8mm solid var(--amb); font-style:italic; color:#33393b; background:linear-gradient(90deg,rgba(200,121,28,.07),transparent); break-inside:avoid; }
ul,ol { margin:0 0 2.5mm; padding-left:5mm; } li { margin:0 0 1mm; }
code { font:8pt 'Menlo',monospace; background:#f0eee8; padding:0 1mm; }
table { width:100%; border-collapse:collapse; margin:2mm 0 3.5mm; font:7.6pt/1.3 'Avenir Next'; }
th { text-align:left; font:700 6.8pt 'Avenir Next Condensed'; letter-spacing:.12em; text-transform:uppercase; background:var(--teal); color:#fff; padding:1.3mm 1.6mm; }
td { padding:1.2mm 1.6mm; border-bottom:.2mm solid #ddd; vertical-align:top; }
table.wide { column-span:all; }
td, th { overflow-wrap:anywhere; hyphens:auto; }
tr:nth-child(even) td { background:#f6f4ee; } tr { break-inside:avoid; }
.caja { break-inside:avoid; background:#eef3f2; border-top:1mm solid var(--teal); padding:3mm 4mm 2mm; margin:3mm 0; font:8.2pt/1.4 'Avenir Next'; }
.caja h4 { margin:0 0 1.5mm; font:700 8pt 'Avenir Next Condensed'; letter-spacing:.2em; text-transform:uppercase; color:var(--teal); }
.caja p { text-align:left; margin:0 0 1.5mm; } .caja ul { margin:0; }
.ficha { break-inside:avoid; margin:3mm 0; background:#fff; border:.3mm solid var(--ink); font:8pt/1.38 'Avenir Next'; }
.ficha header { background:var(--ink); color:#fff; padding:1.8mm 3mm; display:flex; justify-content:space-between; align-items:baseline; }
.ficha h4 { margin:0; font:700 11pt 'Avenir Next Condensed'; text-transform:uppercase; letter-spacing:.05em; } .ficha header span { font-size:7pt; opacity:.8; }
.chips { display:flex; flex-wrap:wrap; border-bottom:.2mm solid #bbb; } .chip { flex:1; text-align:center; padding:1.2mm 1mm; border-right:.2mm solid #ddd; }
.chip em { display:block; font:normal 600 5.8pt 'Avenir Next Condensed'; letter-spacing:.14em; text-transform:uppercase; color:var(--mut); } .chip b { font:700 11pt 'Avenir Next Condensed'; }
.ficha p { margin:0; padding:1.1mm 3mm; text-align:left; }
.documento { break-inside:avoid; position:relative; background:#f4ecd6; border:.2mm solid #cdbf98; box-shadow:0 .6mm 2mm rgba(0,0,0,.18); padding:6mm 5mm 3mm; margin:5mm 0 4mm; font:7.9pt/1.45 'American Typewriter','Courier New',monospace; color:#2b2a24; }
.documento h4 { margin:0 0 2mm; font:700 9pt 'American Typewriter'; text-transform:uppercase; border-bottom:.3mm solid #8a7d55; padding-bottom:1mm; }
.documento p { text-align:left; margin:0 0 1.6mm; } .documento .tape { position:absolute; top:-2.4mm; left:5mm; background:rgba(200,121,28,.85); color:#fff; font:700 5.8pt 'Avenir Next Condensed'; letter-spacing:.25em; padding:.6mm 3mm; }
.bgimg { position:absolute; left:0; top:0; width:100%; height:100%; object-fit:cover; }
figure { margin:3mm 0; break-inside:avoid; }
figure img { width:100%; display:block; }
figcaption { font:400 7pt/1.35 'Avenir Next'; color:var(--mut); padding-top:1.2mm; border-top:.3mm solid var(--amb); margin-top:1.2mm; } figcaption b { color:var(--teal); }
figure.wide { column-span:all; margin:4mm 0 5mm; } figure.wide img { max-height:92mm; object-fit:cover; }
figure.tall img { max-height:105mm; object-fit:cover; }
figure.ret img { aspect-ratio:4/4.6; object-fit:cover; border:.3mm solid var(--ink); }
figure.plano img { border:.3mm solid #999; width:100%; max-width:100%; height:auto; max-height:none; object-fit:fill; }
figure { max-width:100%; }
.falta { background:#ccd; color:#556; padding:12mm 3mm; text-align:center; font:7pt monospace; }
.plate { page:plate; break-before:page; break-after:page; width:100%; height:296.4mm; contain:paint; position:relative; background:#0a1a1f center/cover; overflow:hidden; color:#fff; }
.plate::after { content:""; position:absolute; inset:0; background:linear-gradient(0deg,rgba(4,12,15,.92) 0%,rgba(4,12,15,.55) 22%,rgba(4,12,15,0) 48%); }
.plate-t { position:absolute; z-index:2; left:16mm; right:16mm; bottom:18mm; }
.plate-t span { font:600 7pt 'Avenir Next Condensed'; letter-spacing:.3em; text-transform:uppercase; color:#f0a64a; }
.plate-t h2 { color:#fff; font-size:34pt; border:0; margin:2mm 0 2mm; padding:0; } .plate-t h2::before { content:""; }
.plate-t p { font:400 8.5pt/1.4 'Avenir Next'; opacity:.85; max-width:120mm; margin:0; }
.hoja { page: opener; break-before:page; font-family:'Avenir Next'; }
.hoja header { display:flex; justify-content:space-between; gap:6mm; border-bottom:.8mm solid var(--ink); padding-bottom:3mm; } .hoja header img { width:34mm; height:40mm; object-fit:cover; border:.3mm solid var(--ink); }
.hoja h2 { margin:1mm 0; font-size:26pt; border:0; padding:0; } .hoja h2::before{content:"";} .hoja header p { margin:0; font-size:9pt; color:var(--mut); }
.hoja .kicker { font:600 7pt 'Avenir Next Condensed'; letter-spacing:.3em; text-transform:uppercase; color:var(--amb); }
.stats { display:flex; margin:4mm 0 0; border:.3mm solid var(--ink); } .stats div { flex:1; text-align:center; padding:2mm; border-right:.2mm solid #bbb; } .stats em { display:block; font:normal 600 6.5pt 'Avenir Next Condensed'; letter-spacing:.18em; text-transform:uppercase; color:var(--mut); } .stats b { font:700 18pt 'Avenir Next Condensed'; }
.stats.sv { margin-top:0; border-top:0; background:#f4f1e8; }
.vit { display:flex; gap:3mm; margin:4mm 0; } .vit div { flex:1; border:.3mm solid var(--ink); text-align:center; padding:2mm; min-height:14mm; } .vit em { display:block; font:normal 600 6.5pt 'Avenir Next Condensed'; letter-spacing:.18em; text-transform:uppercase; color:var(--mut);} .vit b { font:700 16pt 'Avenir Next Condensed'; }
.dos { display:flex; gap:8mm; } .dos > div { flex:1; } .hoja h3 { margin:3mm 0 1.5mm; } .hoja ul { font-size:8.6pt; margin:0; padding-left:4mm; }
.recs { display:grid; grid-template-columns:1fr 1fr; gap:3mm; } .rec { border:.3mm solid var(--ink); padding:2.4mm 3mm 3mm; position:relative; font-size:8.2pt; line-height:1.35; min-height:28mm; } .rec span { font:700 11pt 'Avenir Next Condensed'; color:var(--amb); } .rec p { margin:1mm 0 0; } .rec i { position:absolute; right:2mm; top:2mm; width:5mm; height:5mm; border:.3mm solid var(--ink); }
.hoja .nota { font-size:7.5pt; color:var(--mut); margin-top:3mm; }
"""


def portada():
    src = img_path("fig-portada")
    bg = ('<img class="bgimg" src="%s">' % src) if src else ""
    return ('<section class="cover">%s<div class="shade"></div><div class="mast"><span>Anales de Biología de Frontera</span><span>Vol. 12 · n.º 3 · Número especial ND-17</span></div>'
            '<h1>Nádir<span>Sangre bajo el hielo</span></h1><div class="sub">Expediente del suceso de C-7 y primera descripción de <i>Crustivermis nadirensis</i>. Una aventura de horror industrial para Mothership 1e.</div>'
            '<div class="tag"><span>3–5 jugadores</span><span>6–9 horas</span><span>Mothership 1e</span></div></section>') % bg


def contraportada():
    src = img_path("fig-final")
    bg = ('<img class="bgimg" src="%s">' % src) if src else ""
    return ('<section class="contra">%s<div class="shade"></div><div class="txt"><h3>Nádir tampoco deja marchar a todo el mundo</h3>'
            '<p>Una cuadrilla de presos de confianza, una operadora civil y su alguacil reparan una bomba cuando llega el último mensaje de Mara Venn. '
            'En el sector C-7 hay trece personas en un refugio para diez, dos atrapados sosteniendo una bomba que no pueden abandonar, y algo ciego que sella las grietas del hielo. '
            'Y un cadáver, para ellos, también es una grieta.</p>'
            '<p>Aventura completa de horror industrial y rescate para Mothership 1e: cuatro actos, doce localizaciones, tres relojes, quince vidas en juego y ninguna solución única.</p>'
            '<small>Obra independiente y no oficial, compatible con Mothership 1e. Mothership es una marca de Tuesday Knight Games. '
            'Texto © Manuel Romera. Imágenes generadas con IA y gradadas por el autor. Licencia: CC BY-NC-SA 4.0.</small></div></section>') % bg


def indice(items, paginas):
    lis = "".join('<li><i>%s</i><span>%s</span><span class="d"></span><span>%s</span></li>' % (esc(k), esc(t), paginas.get(cid, "")) for cid, k, t in items)
    return ('<section class="toc"><h1>En este número</h1><div class="rule"></div><ul>%s</ul>'
            '<p class="nota">Cómo leer este informe: los capítulos de acto contienen las escenas y localizaciones. '
            'Los recuadros azules son para el Guardián, los rótulos oscuros son fichas de personaje y el papel amarillo son documentos que '
            'los jugadores pueden ver. Los planos están en cada cubierta y en el apéndice.</p></section>') % lis


def construir(paginas):
    fig_n[0] = 0
    usadas.clear()
    items, cuerpo = [], []
    for n, nombre in enumerate(ORDEN):
        cid, titulo, h = capitulo(nombre, n)
        items.append((cid, SECCION[nombre], titulo))
        cuerpo.append(h)
    items.append(("cap-hojas", "Apéndice", "Archivos personales"))
    cuerpo.append(hojas())
    items.append(("cap-planos", "Apéndice", "Planos"))
    cuerpo.append(plano_conductos())
    doc = '<!doctype html><html lang="es"><meta charset="utf-8"><title>Nádir: Sangre bajo el hielo</title><style>%s</style><body>%s%s%s%s</body></html>' % (
        CSS, portada(), indice(items, paginas), "".join(cuerpo), contraportada())
    return doc, items


def pdf(htmlpath, out):
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--allow-file-access-from-files",
                    "--virtual-time-budget=20000", "--print-to-pdf=" + out, "file://" + htmlpath], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)


def paginas_de(out, items):
    """Página de cada apertura de capítulo: busca su kicker («ACTO I · N.º 01») sin espacios."""
    import fitz
    d = fitz.open(out)
    norm = lambda t: re.sub(r"\s+", "", t).upper()  # noqa: E731
    res = {}
    for cid, k, t in items:
        m = re.match(r"cap-(\d+)$", cid)
        clave = norm("%s·N.º%02d" % (k, int(m.group(1)))) if m else norm(k + ("·IMPRIMIBLE" if cid == "cap-hojas" else "")) + norm(t)
        for pno in range(2, len(d)):
            if clave in norm(d[pno].get_text()):
                res[cid] = str(pno + 1)
                break
    return res


def main():
    os.makedirs(os.path.join(BUILD, "pdf"), exist_ok=True)
    hp = os.path.join(BUILD, "pdf", "libro.html")
    out = os.path.join(BUILD, "Nadir-Sangre-bajo-el-hielo.pdf")
    doc, items = construir({})
    open(hp, "w").write(doc)
    pdf(hp, out)
    if "--draft" not in sys.argv:
        pg = paginas_de(out, items)
        doc, items = construir(pg)
        open(hp, "w").write(doc)
        pdf(hp, out)
    import fitz
    print("páginas:", len(fitz.open(out)), "figuras:", fig_n[0], "sin arte:", sorted(i for i in PROMPTS if i.startswith(("fig-", "ret-", "lam-")) and not img_path(i)))


if __name__ == "__main__":
    main()
