#!/usr/bin/env python3
"""Genera el contenido Foundry de «Nádir» (Adventure para el sistema mosh) a partir de docs/ + art_final/ + build/maps.

Salida: _data/aventura.json (documentos) y assets/{art,tokens,maps}/*.webp. Luego `npm run build` lo compila a packs/aventura (LevelDB).
Uso: python3 tools/build_foundry.py   (necesita haber ejecutado tools/maps.py y tools/post_images.py)
"""
import hashlib
import json
import os
import re
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_pdf as B  # noqa: E402
import maps as M  # noqa: E402

ROOT = B.ROOT
B.MODO[0] = "foundry"
MOD = "modules/mr-nadir"
CANON = B.CANON
ART = B.ART
ASSETS = os.path.join(ROOT, "assets")
CHAR = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def fid(key):
    h = int(hashlib.sha256(("nadir:" + key).encode()).hexdigest(), 16)
    return "".join(CHAR[(h >> (6 * i)) % 62] for i in range(16))


def webp(src, dst, q=84, lossless=False):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    Image.open(src).save(dst, "WEBP", quality=q, lossless=lossless, method=6)


def preparar_assets():
    n = 0
    for f in sorted(os.listdir(ART)) if os.path.isdir(ART) else []:
        iid, ext = os.path.splitext(f)
        if iid.startswith("tok-"):
            webp(os.path.join(ART, f), os.path.join(ASSETS, "tokens", iid + ".webp"), q=92)
        else:
            webp(os.path.join(ART, f), os.path.join(ASSETS, "art", iid + ".webp"), q=82)
        n += 1
    for deck in list(M.DECKS) + ["ruta"]:
        src = os.path.join(M.OUT, deck + "-dark.png")
        if os.path.exists(src):
            webp(src, os.path.join(ASSETS, "maps", deck + ".webp"), q=88)
    return n


def art(iid, tipo="art"):
    d = "tokens" if tipo == "tokens" else "art"
    ok = os.path.exists(os.path.join(ASSETS, d, iid + ".webp"))
    return "%s/assets/%s/%s.webp" % (MOD, d, iid) if ok else "icons/svg/mystery-man.svg"


FOLDERS = {}


def folder(tipo, nombre, color="#c8791c", sort=0):
    key = tipo + nombre
    if key not in FOLDERS:
        FOLDERS[key] = {"_id": fid("folder:" + key), "name": nombre, "type": tipo, "color": color, "sorting": "m", "sort": sort, "folder": None, "description": "", "flags": {}}
    return FOLDERS[key]["_id"]


def page(key, name, html, sort):
    return {"_id": fid("page:" + key), "name": name, "type": "text", "title": {"show": True, "level": 1}, "text": {"format": 1, "content": '<div class="mr-nadir-j">%s</div>' % html},
            "sort": sort, "ownership": {"default": -1}, "flags": {}}


def split_pages(texto, nombre):
    rooms = False
    pages, cur, title = [], [], None
    for l in texto.splitlines():
        if l.startswith("# "):
            continue
        if l.startswith("## ") or (rooms and re.match(r"^### \d\.\d\b", l)):
            if cur or title:
                pages.append((title, "\n".join(cur)))
            title, cur = l.lstrip("# ").strip(), [l]
        else:
            cur.append(l)
    pages.append((title, "\n".join(cur)))
    return pages


JOURNALS, ROOM_PAGE = [], {}


def diarios():
    fol = folder("JournalEntry", "Nádir · Guía del Guardián", sort=100)
    for num, nombre in enumerate(B.ORDEN):
        texto = open(os.path.join(ROOT, "docs", "texto", nombre + ".md")).read()
        ctx = {}
        B.md_blocks(texto, ctx)
        titulo = ctx.get("titulo", nombre)
        pgs = []
        for k, (pt, md) in enumerate(split_pages(texto, nombre)):
            html = "".join(h for kind, h in B.md_blocks(md, {}))
            if k == 0:
                res = ctx.get("resumen", "")
                kw = re.search(r"Palabras clave:\s*(.*)", res)
                res2 = re.sub(r"Palabras clave:.*", "", res).strip()
                html = ('<div class="abstract"><b>Resumen</b><p>%s</p>%s</div>' % (B.inline(res2), ('<p class="kw"><b>Palabras clave:</b> %s</p>' % B.esc(kw.group(1))) if kw else "")) + html
                pt = pt or titulo
                if not html.strip() or len(re.sub(r"\s+", "", md)) < 4:
                    pass
            pg = page("%s:%d" % (nombre, k), pt or titulo, html, (k + 1) * 100)
            pgs.append(pg)
            m = re.match(r"^\[(\d+|X)\]", (pt or "").strip()) if nombre == "05-acto-3" else None
            if m:
                ROOM_PAGE[m.group(1)] = (fid("je:" + nombre), pg["_id"])
        JOURNALS.append({"_id": fid("je:" + nombre), "name": "%02d · %s" % (num, titulo), "pages": pgs, "folder": fol, "sort": num * 100,
                         "ownership": {"default": 0}, "flags": {}})
    fol2 = folder("JournalEntry", "Nádir · Documentos para los jugadores", sort=200)
    texto = open(os.path.join(ROOT, "docs", "texto", "09-documentos.md")).read()
    for i, m in enumerate(re.finditer(r"^::: documento (.+?)\n(.*?)\n^:::\s*$", texto, re.S | re.M)):
        titulo, body = m.group(1).strip(), m.group(2)
        html = '<div class="documento"><h4>%s</h4>%s</div>' % (B.esc(titulo), "".join(h for k, h in B.md_blocks(body, {})))
        JOURNALS.append({"_id": fid("doc:" + titulo), "name": titulo, "pages": [page("doc:" + titulo, titulo, html, 100)], "folder": fol2, "sort": i * 10,
                         "ownership": {"default": 0}, "flags": {}})


def bio_pnj(p):
    armas = "".join("<li>%s — %s</li>" % (B.esc(a["n"]), B.esc(a["dano"])) for a in p["armas"])
    ras = "".join("<li>%s</li>" % B.esc(r) for r in p["rasgos"])
    return '<div class="mr-nadir-j"><p><b>%s</b> · %s</p><h4>Armas</h4><ul>%s</ul><h4>Rasgos</h4><ul>%s</ul></div>' % (B.esc(p["nombre"]), B.esc(p["rol"]), armas, ras)


PRESENTACION = {"mara": ("ret-mara", "tok-mara", 1), "quiroga": ("ret-quiroga", "tok-quiroga", 1), "ivo": ("ret-ivo", "tok-ivo", 0),
                "duarte": ("ret-duarte", "tok-duarte", 1), "vidal": ("ret-vidal", "tok-vidal", 0), "oria": ("ret-oria", "tok-oria", 0),
                "ines": ("ret-ines", "tok-ines", 1), "nora": ("ret-nora", "tok-nora", 0), "kroll": ("ret-kroll", "tok-kroll", 0),
                "salcedo": ("ret-salcedo", "tok-salcedo", 1), "preso": ("tok-preso-a", "tok-preso-a", 0),
                "costrero": ("lam-costrero", "tok-costrero", -1), "defensor": ("lam-costrero", "tok-defensor", -1), "enjambre": ("lam-costrero", "tok-costrero", -1)}


def token(nombre, tok, disp=0, link=False):
    return {"name": nombre, "displayName": 30, "actorLink": link, "disposition": disp, "texture": {"src": tok, "scaleX": 1, "scaleY": 1, "fit": "contain"},
            "width": 1, "height": 1, "bar1": {"attribute": "health"}, "sight": {"enabled": link}}


ACTORS = []


def actores():
    f1 = folder("Actor", "Nádir · PNJ", sort=100)
    f2 = folder("Actor", "Nádir · Tripulación (pregenerados)", sort=200)
    for pid, p in CANON["pnj"].items():
        ret, tk, disp = PRESENTACION[pid]
        sysd = {"description": "", "biography": bio_pnj(p), "health": {"value": p["salud"], "min": 0, "max": p["salud"], "label": "Health"},
                "hits": {"value": 0, "min": 0, "max": p["heridas"], "label": "Wounds"},
                "stats": {"combat": {"value": p["combate"], "min": 0, "max": 99, "label": "Combat", "rollLabel": "Combat Check", "enabled": True},
                          "instinct": {"value": p["instinto"], "min": 0, "max": 99, "label": "Instinct", "rollLabel": "Instinct Check", "enabled": True},
                          "armor": {"value": p["armadura"], "mod": 0, "min": 0, "max": 99, "damageReduction": 0, "cover": "none", "label": "Armor", "rollLabel": "Armor Save", "enabled": p["armadura"] > 0}}}
        img = art(ret) if not ret.startswith("tok-") else art(ret, "tokens")
        ACTORS.append({"_id": fid("actor:" + pid), "name": p["nombre"], "type": "creature", "img": img, "system": sysd,
                       "prototypeToken": token(p["nombre"], art(tk, "tokens"), disp), "items": [], "effects": [], "folder": f1, "sort": len(ACTORS) * 10,
                       "ownership": {"default": 0}, "flags": {}})
    RANK = {"entrenado": ("Trained", 10), "experto": ("Expert", 15), "maestro": ("Master", 20)}
    for pid, p in CANON["pregenerados"].items():
        items = []
        for rk, lst in p["habilidades"].items():
            for sk in lst:
                rank, bonus = RANK[rk]
                items.append({"_id": fid("item:%s:sk:%s" % (pid, sk)), "name": sk, "type": "skill", "img": "icons/svg/book.svg",
                              "system": {"description": "", "rank": rank, "bonus": bonus, "prerequisite_ids": []}, "effects": [], "flags": {}, "sort": len(items) * 10})
        for eq in p["equipo"]:
            m = re.search(r"\((\d+d\d+)", eq)
            name = re.sub(r"\s*\(.*?\)", "", eq)
            if m:
                items.append({"_id": fid("item:%s:eq:%s" % (pid, eq)), "name": name, "type": "weapon", "img": "icons/svg/sword.svg",
                              "system": {"description": eq, "damage": m.group(1), "settings": {"firstEdition": True}}, "effects": [], "flags": {}, "sort": len(items) * 10})
            else:
                items.append({"_id": fid("item:%s:eq:%s" % (pid, eq)), "name": eq, "type": "item", "img": "icons/svg/item-bag.svg",
                              "system": {"description": "", "quantity": 1}, "effects": [], "flags": {}, "sort": len(items) * 10})
        rec = "".join("<li><b>%s</b> — %s</li>" % (k, B.inline(v)) for k, v in p["recuerdos"].items())
        bio = '<div class="mr-nadir-j"><p><b>%s</b> · %s</p><h4>Expediente personal</h4><ul>%s</ul></div>' % (
            B.esc(p["nombre"]), B.esc(p["papel"]), rec)
        e, s = p["estadisticas"], p["salvaciones"]
        sysd = {"biography": bio, "class": {"value": p["clase"]}, "health": {"value": p["salud"], "min": 0, "max": p["salud"], "label": "Health"},
                "hits": {"value": 0, "min": 0, "max": p["heridas"], "label": "Wounds"},
                "other": {"stress": {"value": 2, "min": 2, "max": 20, "label": "Stress"}, "resolve": {"value": 0, "min": 0, "max": 15, "label": "Resolve"}},
                "stats": {k: {"value": v, "mod": 0, "min": 0, "max": 99} for k, v in {"strength": e["fuerza"], "speed": e["velocidad"], "intellect": e["intelecto"], "combat": e["combate"],
                                                                                     "sanity": s["cordura"], "fear": s["miedo"], "body": s["cuerpo"]}.items()}}
        ACTORS.append({"_id": fid("actor:" + pid), "name": p["nombre"], "type": "character", "img": art("ret-" + pid), "system": sysd,
                       "prototypeToken": token(p["nombre"], art("tok-" + pid, "tokens"), 1, True), "items": items, "effects": [], "folder": f2, "sort": len(ACTORS) * 10,
                       "ownership": {"default": 0}, "flags": {}})


SCENES = []
NOMBRES = {"b4": "Frente B-4", "ruta": "Superficie: rutas a C-7", "c7": "Sector C-7"}


def nota(deck, rid, x, y, size, fs):
    eid, pid = ROOM_PAGE[rid]
    return {"_id": fid("note:%s:%s" % (deck, rid)), "entryId": eid, "pageId": pid, "x": x, "y": y, "elevation": 0, "sort": 0,
            "texture": {"src": "icons/svg/book.svg", "tint": "#f0a64a"}, "iconSize": size, "text": "[%s]" % rid, "fontFamily": "Signika", "fontSize": fs, "textAnchor": 1,
            "textColor": "#ffffff", "global": False, "flags": {}}


def escenas():
    walls = json.load(open(os.path.join(M.OUT, "walls.json")))
    for i, (deck, nom) in enumerate(NOMBRES.items()):
        notes = []
        if deck in M.DECKS:
            for rid, rects in M.DECKS[deck]["rooms"].items():
                if rid in ROOM_PAGE:
                    x, y, w, h = max(rects, key=lambda r: r[2] * r[3])
                    notes.append(nota(deck, rid, int((x + w / 2) * M.G), int((y + h / 2 + 0.9) * M.G), 40, 32))
        ws = walls.get(deck, [])
        SCENES.append({
            "_id": fid("scene:" + deck), "name": "Nádir · " + nom, "active": False, "navigation": True, "navOrder": i, "navName": nom,
            "background": {"src": "%s/assets/maps/%s.webp" % (MOD, deck)},
            "width": M.W * M.G, "height": M.H * M.G, "padding": 0, "initial": {"x": 2000, "y": 1300, "scale": 0.4}, "backgroundColor": "#06141a",
            "grid": {"type": 1 if deck != "ruta" else 0, "size": M.G, "style": "solidLines", "thickness": 1, "color": "#000000", "alpha": 0.15, "distance": 1.5, "units": "m"},
            "tokenVision": deck != "ruta", "fog": {"exploration": deck != "ruta"},
            "environment": {"darknessLevel": 0.55 if deck == "c7" else 0.2, "globalLight": {"enabled": deck == "ruta"}},
            "walls": [{"_id": fid("wall:%s:%d" % (deck, k)), "c": w["c"], "move": 1, "sense": 1, "sound": 1, "light": 1, "door": w["door"], "ds": w["ds"], "dir": 0, "flags": {}} for k, w in enumerate(ws)],
            "notes": notes, "tokens": [], "lights": [], "sounds": [], "tiles": [], "drawings": [], "templates": [], "regions": [],
            "folder": None, "sort": i * 10, "ownership": {"default": 0}, "flags": {}})


TABLES = []


def tablas():
    fol = folder("RollTable", "Nádir · Tablas", sort=300)
    for nombre in B.ORDEN:
        lines = open(os.path.join(ROOT, "docs", "texto", nombre + ".md")).read().splitlines()
        head = ""
        i = 0
        while i < len(lines):
            l = lines[i]
            if l.startswith("#"):
                head = l.lstrip("# ").strip()
            mt = re.match(r"^\|\s*(1?d10|1?d6)\s*\|", l, re.I)
            if mt:
                rows = []
                i += 2
                while i < len(lines) and lines[i].startswith("|"):
                    c = [x.strip() for x in lines[i].strip().strip("|").split("|")]
                    if re.match(r"^\d+(\s*[–-]\s*\d+)?$", c[0]):
                        rows.append(c)
                    i += 1
                if len(rows) >= 6:
                    name = re.sub(r"^1?d(10|6)\s*", "", re.sub(r"^[a-d]\)\s*", "", head), flags=re.I).strip() or head
                    res = []
                    for r in rows:
                        a = re.split(r"\s*[–-]\s*", r[0])
                        lo, hi = int(a[0]), int(a[-1])
                        txt = r[1] if len(r) == 2 else "%s <i>(%s)</i>" % (r[1], " · ".join(r[2:]))
                        res.append({"_id": fid("res:%s:%s:%s" % (nombre, name, r[0])), "type": "text", "name": "", "img": "icons/svg/d10-grey.svg",
                                    "description": "<p>%s</p>" % (txt if "<i>" in txt else B.inline(txt)), "weight": 1, "range": [lo, hi], "drawn": False, "flags": {}})
                    TABLES.append({"_id": fid("table:" + nombre + name), "name": name, "formula": "1d6" if "6" in mt.group(1) else "1d10", "replacement": True, "displayRoll": True, "results": res, "folder": fol,
                                   "description": "", "sort": len(TABLES) * 10, "ownership": {"default": 0}, "flags": {}})
                continue
            i += 1


MACROS = []


def macros():
    fol = folder("Macro", "Nádir", sort=400)

    def mac(name, cmd, img):
        MACROS.append({"_id": fid("macro:" + name), "name": name, "type": "script", "scope": "global", "img": img, "command": cmd, "author": "0000000000000000", "folder": fol, "sort": len(MACROS) * 10,
                       "ownership": {"default": 0}, "flags": {"mr-nadir": {"macro": True}}})
    mac("Panel de emergencia", 'game.modules.get("mr-nadir")?.api?.abrirPanel();', "icons/svg/clockwork.svg")
    for tbl, nom in (("Ecos del hielo", "Eco del hielo"), ("complicaciones", "Complicación (1d6)")):
        mac(nom, "const t = game.tables.find(x => x.name.toLowerCase().includes(%s)); if (!t) return ui.notifications.warn('Importa la aventura para tener la tabla.'); t.draw();" % json.dumps(tbl.lower()), "icons/svg/d10-grey.svg")
    mac("Tirada de Cuerpo por CO₂ (seleccionados)", """// Hipercapnia: salvación de Cuerpo para los tokens seleccionados (d100 igual o inferior).
const toks = canvas.tokens.controlled;
if (!toks.length) return ui.notifications.warn("Selecciona al menos un token.");
let out = "";
for (const t of toks) {
  const body = t.actor?.system?.stats?.body?.value ?? 0;
  const r = (await new Roll("1d100").evaluate()).total;
  out += `<p><b>${t.name}</b> · Cuerpo ${body} · tirada ${r} → <b>${r <= body ? "resiste" : "mareo, confusión: [−] en esfuerzos"}</b></p>`;
}
ChatMessage.create({content: out});""", "icons/svg/biohazard.svg")


def aventura():
    desc = ('<p><b>Nádir: Sangre bajo el hielo</b> — aventura de horror industrial y rescate para Mothership 1e (3–5 jugadores, 6–9 h).</p>'
            '<p>Incluye: guía del Guardián en %d diarios, documentos para jugadores, %d PNJ y criaturas, 5 pregenerados con tokens de cuerpo entero, mapas con muros y puertas, %d tablas, macros y el <b>Panel de emergencia</b> (botón en los controles de token).</p>') % (
        len(B.ORDEN), len(CANON["pnj"]), len(TABLES))
    return {"_id": fid("adventure"), "name": "MR- Nádir: Sangre bajo el hielo", "img": art("fig-portada"), "caption": "<p>Anales de Biología de Frontera · Número especial ND-17</p>", "description": desc,
            "actors": ACTORS, "combats": [], "items": [], "journal": JOURNALS, "scenes": SCENES, "tables": TABLES, "macros": MACROS, "cards": [], "playlists": [],
            "folders": list(FOLDERS.values()), "folder": None, "sort": 0, "flags": {}}


def main():
    n = preparar_assets()
    diarios()
    actores()
    escenas()
    tablas()
    macros()
    adv = aventura()
    os.makedirs(os.path.join(ROOT, "_data"), exist_ok=True)
    json.dump([adv], open(os.path.join(ROOT, "_data", "aventura.json"), "w"), ensure_ascii=False)
    print("assets:", n, "| diarios:", len(JOURNALS), "| páginas:", sum(len(j["pages"]) for j in JOURNALS), "| actores:", len(ACTORS), "| escenas:", len(SCENES),
          "| tablas:", len(TABLES), [t["name"] for t in TABLES], "| macros:", len(MACROS), "| salas con página:", sorted(ROOM_PAGE))


if __name__ == "__main__":
    main()
