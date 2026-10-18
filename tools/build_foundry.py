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
        src = os.path.join(M.OUT, deck + "-crt.png")
        if os.path.exists(src):
            import post_images
            post_images.marca(Image.open(src), 0.035, 0.35).convert("RGB").save(os.path.join(ASSETS, "maps", deck + ".webp"), "WEBP", quality=88, method=6)
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
        JOURNALS.append({"_id": fid("je:" + nombre), "name": "%02d · %s" % (num, titulo.replace("*", "")), "pages": pgs, "folder": fol, "sort": num * 100,
                         "ownership": {"default": 0}, "flags": {}})
    fol2 = folder("JournalEntry", "Nádir · Documentos para los jugadores", sort=200)
    texto = open(os.path.join(ROOT, "docs", "texto", "09-documentos.md")).read()
    partes = {}
    for i, m in enumerate(re.finditer(r"^::: documento (.+?)\n(.*?)\n^:::\s*$", texto, re.S | re.M)):
        titulo, body = m.group(1).strip(), m.group(2)
        # el código sale del prefijo del título («D12-B · tramo 2» → D12-B); los registros por tramos comparten código y se numeran por parte
        cod = re.match(r"(D\d+(?:-[A-Z])?) · ", titulo).group(1)
        partes[cod] = partes.get(cod, 0) + 1
        html = '<div class="documento"><h4>%s</h4>%s</div>' % (B.esc(titulo), "".join(h for k, h in B.md_blocks(body, {})))
        JOURNALS.append({"_id": fid("doc:" + titulo), "name": titulo, "pages": [page("doc:" + titulo, titulo, html, 100)], "folder": fol2, "sort": i * 10,
                         "ownership": {"default": 0}, "flags": {"mr-nadir": {"doc": cod, "parte": partes[cod]}}})


def _json_opc(nombre):
    ruta = os.path.join(ROOT, "docs", "biblia", nombre)
    return json.load(open(ruta)) if os.path.exists(ruta) else {}


MEC = _json_opc("mecanica.json")   # fichas jugables de PNJ y equipo de los PJ
ICON = _json_opc("iconos.json")    # iconos (del sistema mosh o generados en assets/icons)


def icono(tipo, nombre, defecto):
    """Icono para un objeto: búsqueda exacta y luego por coincidencia parcial del nombre."""
    tabla = ICON.get(tipo, {})
    if nombre in tabla:
        return tabla[nombre]
    n = nombre.lower()
    for k, v in tabla.items():
        if k.lower() in n or n.split(" (")[0] in k.lower():
            return v
    return defecto


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
    nuevos = {pid: {"nombre": m["nombre"], "rol": m.get("rol", ""), "combate": m["combate"], "instinto": m["instinto"], "salud": m["salud"],
                    "heridas": m["heridas"], "armadura": m.get("pa", 0), "armas": [], "rasgos": []}
              for pid, m in MEC.get("pnj", {}).items() if pid not in CANON["pnj"]}
    for pid, m in MEC.get("pnj", {}).items():
        if pid in nuevos:
            tk = m.get("token") or "tok-preso-a"
            PRESENTACION[pid] = (tk, tk, 0)
    for pid, p in list(CANON["pnj"].items()) + list(nuevos.items()):
        ret, tk, disp = PRESENTACION[pid]
        sysd = {"description": "", "biography": bio_pnj(p), "health": {"value": p["salud"], "min": 0, "max": p["salud"], "label": "Health"},
                "hits": {"value": 0, "min": 0, "max": p["heridas"], "label": "Wounds"},
                "stats": {"combat": {"value": p["combate"], "min": 0, "max": 99, "label": "Combat", "rollLabel": "Combat Check", "enabled": True},
                          "instinct": {"value": p["instinto"], "min": 0, "max": 99, "label": "Instinct", "rollLabel": "Instinct Check", "enabled": True},
                          "armor": {"value": p["armadura"], "mod": 0, "min": 0, "max": 99, "damageReduction": 0, "cover": "none", "label": "Armor", "rollLabel": "Armor Save", "enabled": p["armadura"] > 0}}}
        img = art(ret) if not ret.startswith("tok-") else art(ret, "tokens")
        ACTORS.append({"_id": fid("actor:" + pid), "name": p["nombre"], "type": "creature", "img": img, "system": sysd, "_pid": pid,
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
        ACTORS.append({"_id": fid("actor:" + pid), "name": p["nombre"], "type": "character", "img": art("ret-" + pid), "system": sysd, "_pid": pid,
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
    mac("Volver al mapa (todos)", 'game.modules.get("mr-nadir")?.api?.volverAlMapa();', "icons/svg/direction.svg")
    mac("Parar efectos", 'game.modules.get("mr-nadir")?.api?.pararEfectos();', "icons/svg/sound-off.svg")
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
    desc = ('<p><b>Nádir: Sangre bajo el hielo</b> — aventura de horror industrial y rescate para Mothership 1.2 (3–5 jugadores, 6–9 h).</p>'
            '<p>Incluye: guía del Guardián en %d diarios, documentos para jugadores, %d PNJ y criaturas, 5 pregenerados con tokens de cuerpo entero, mapas con muros y puertas, %d tablas, macros y el <b>Panel de emergencia</b> (botón en los controles de token).</p>') % (
        len(B.ORDEN), len(CANON["pnj"]), len(TABLES))
    return {"_id": fid("adventure"), "name": "MR- Nádir: Sangre bajo el hielo", "img": art("fig-portada"), "caption": "<p>Anales de Biología de Frontera · Número especial ND-17</p>", "description": desc,
            "actors": ACTORS, "combats": [], "items": ITEMS, "journal": JOURNALS, "scenes": SCENES, "tables": TABLES, "macros": MACROS, "cards": [], "playlists": PLAYLISTS,
            "folders": list(FOLDERS.values()), "folder": None, "sort": 0, "flags": {}}


def main():
    n = preparar_assets()
    diarios()
    objetos()
    actores()
    enriquecer_actores()
    mecanica()
    playlists_base()
    lecturas()
    escenas()
    tablas()
    macros()
    guion()
    adv = aventura()
    os.makedirs(os.path.join(ROOT, "_data"), exist_ok=True)
    json.dump([adv], open(os.path.join(ROOT, "_data", "aventura.json"), "w"), ensure_ascii=False)
    print("assets:", n, "| diarios:", len(JOURNALS), "| páginas:", sum(len(j["pages"]) for j in JOURNALS), "| actores:", len(ACTORS), "| objetos:", len(ITEMS),
          "| escenas:", len(SCENES), "| regiones:", sum(len(x["regions"]) for x in SCENES), "| playlists:", len(PLAYLISTS), "| tablas:", len(TABLES), "| macros:", len(MACROS))




# =====================================================================================================
# v2: escenas de imagen, mapas de fósforo con zonas, audio, lecturas, guion, objetos y PNJ completos
# =====================================================================================================
ESTANCIAS = json.load(open(os.path.join(ROOT, "docs", "v2", "estancias.json")))
EST = {e["id"]: e for e in ESTANCIAS}
SFX_KEYS = ["hum", "ventilador", "bomba-b4", "bomba-p2", "goteo", "raspado", "cria-latido", "respiraciones", "casco-respiracion", "rover-motor",
            "alarma-lenta", "radar-ping", "temblor", "alarma-presion", "alarma-co2", "siseo", "golpe-metal", "chirrido", "raspado-fuerte", "compuerta",
            "rover-arranque", "soldadura", "terminal", "radio-estatica", "radio-serrat"]
MUSICAS = {"exploracion": "Nádir · Exploración", "turno": "Turno de B-4", "superficie": "Hielo negro", "control": "Control C-0", "galerias": "Galerías",
           "cria": "La cría", "refugio": "Trece respiraciones", "bomba": "La bomba", "contrarreloj": "Contrarreloj", "final": "Lo que queda"}
SFX_NOMBRE = {"hum": "Zumbido eléctrico", "ventilador": "Ventilador cansado", "bomba-b4": "Bomba de B-4", "bomba-p2": "Bomba de P-2", "goteo": "Goteo de salmuera",
              "raspado": "Raspado en el metal", "cria-latido": "Pulso de la cría", "respiraciones": "Trece respiraciones", "casco-respiracion": "Respiración en el casco",
              "rover-motor": "Motor del rover", "alarma-lenta": "Alarma lenta", "radar-ping": "Ping de radar", "temblor": "Temblor", "alarma-presion": "Alarma de presión",
              "alarma-co2": "Alarma de CO₂", "siseo": "Fuga de gas", "golpe-metal": "Golpe metálico", "chirrido": "Chirrido de dentículos", "raspado-fuerte": "Raspado cercano",
              "compuerta": "Compuerta hidráulica", "rover-arranque": "Arranque del rover", "soldadura": "Soldadura", "terminal": "Terminal", "radio-estatica": "Estática de radio",
              "radio-serrat": "Radio de Serrat"}
AUD = MOD + "/assets/audio/"
PLAYLISTS = []


def snd(clave, carpeta, nombre, vol, repetir, key):
    return {"_id": fid("snd:%s:%s" % (key, clave)), "name": nombre, "path": AUD + "%s/%s.ogg" % (carpeta, clave), "repeat": repetir, "volume": vol,
            "playing": False, "pausedTime": None, "fade": 1500 if repetir else None, "sort": 0, "description": "", "channel": "music" if carpeta == "musica" else "environment",
            "flags": {"mr-nadir": {"clave": clave}}}


def playlists_base():
    fol = folder("Playlist", "Nádir · Banda sonora", sort=100)
    sounds = [snd(k, "sfx", SFX_NOMBRE[k], 0.8, False, "sfx") for k in SFX_KEYS]
    for s_ in sounds:
        s_["channel"] = "interface"
    PLAYLISTS.append({"_id": fid("pl:sfx"), "name": "Nádir · Efectos (Guardián)", "mode": -1, "playing": False, "fade": None, "sorting": "a", "sounds": sounds,
                      "folder": fol, "sort": 0, "description": "<p>Efectos de disparo manual. Los botones de las escenas y del guion los lanzan para todos.</p>",
                      "channelVolumes": {}, "seed": 0, "ownership": {"default": 0}, "flags": {"mr-nadir": {"rol": "sfx"}}})
    PLAYLISTS.append({"_id": fid("pl:musica"), "name": "Nádir · Música", "mode": -1, "playing": False, "fade": 2000, "sorting": "m",
                      "sounds": [snd(k, "musica", n, 0.5, True, "musica") for k, n in MUSICAS.items()], "folder": fol, "sort": 10, "description": "",
                      "channelVolumes": {}, "seed": 0, "ownership": {"default": 0}, "flags": {"mr-nadir": {"rol": "musica"}}})


def playlist_escena(slug, nombre, musica, ambientes):
    fol = folder("Playlist", "Nádir · Escenas (música + ambiente)", sort=200)
    sounds = [snd(musica, "musica", "Música · " + MUSICAS[musica], 0.45, True, slug)]
    sounds += [snd(a, "sfx", "Ambiente · " + SFX_NOMBRE[a], 0.32, True, slug) for a in ambientes]
    pid = fid("pl:esc:" + slug)
    PLAYLISTS.append({"_id": pid, "name": "Escena · " + nombre, "mode": 2, "playing": False, "fade": 2000, "sorting": "m", "sounds": sounds, "folder": fol,
                      "sort": len(PLAYLISTS) * 10, "description": "", "channelVolumes": {}, "seed": 0, "ownership": {"default": 0},
                      "flags": {"mr-nadir": {"rol": "escena", "slug": slug}}})
    return pid


# ---------------- lecturas por estancia ----------------
LECT_JE = fid("je:lecturas")
LECT_PAGE = {}


def lecturas():
    fol = folder("JournalEntry", "Nádir · Guía del Guardián", sort=100)
    bloques = {}
    for f in ("lectura-superficie-b4.md", "lectura-c7.md"):
        t = open(os.path.join(ROOT, "docs", "v2", f)).read()
        for m in re.finditer(r"^## (\S+) · (.+?)\n(.*?)(?=^## |\Z)", t, re.S | re.M):
            bloques[m.group(1)] = (m.group(2).strip(), m.group(3))
    pages = []
    for i, e in enumerate(ESTANCIAS):
        nombre, md = bloques.get(e["id"], (e["nombre"], ""))
        acc = ['<div class="acciones"><b>Guardián</b>', "@NadirEscena[%s]{Mostrar escena a todos}" % e["id"], "@NadirMapa[%s]{Volver al mapa}" % e["mapa"]]
        acc += ["@NadirSfx[%s]{%s}" % (k, SFX_NOMBRE[k]) for k in e["sfx_manual"]]
        acc += ["@NadirMusica[%s]{Música: %s}" % (e["musica"], MUSICAS[e["musica"]]), "</div>"]
        html = " ".join(acc) + "".join(h for k, h in B.md_blocks(md, {}))
        pg = page("lect:" + e["id"], "%s · %s" % (e["sala"], nombre) if e["mapa"] != "ruta" else nombre, html, (i + 1) * 100)
        pages.append(pg)
        LECT_PAGE[e["id"]] = pg["_id"]
    JOURNALS.append({"_id": LECT_JE, "name": "Lecturas de escena (Guardián)", "pages": pages, "folder": fol, "sort": -50, "ownership": {"default": 0}, "flags": {}})


# ---------------- objetos para arrastrar ----------------
OBJETOS = {
    "cartucho-co2": ("Cartucho de CO₂ HRF C-12", "item", "+1,2 kg de absorción: unas 2 h para los trece de R-3 (10 min de instalación) o unas 13 h de aire para los dos de P-2."),
    "bateria-auxiliar": ("Batería portátil (12 UE)", "item", "Seis horas de bomba en P-2 (2 UE/h). 1 UE de batería = 1 UE de rover."),
    "sellante": ("Sellante, abrazaderas y parches", "item", "Tres parches de traje (estanqueidad con PA 1). Parche de la junta del tramo bajo: 60 min con E-1 abierta y H-4 ≤ 3, H-4 −1 una vez."),
    "cortadora": ("Cortadora industrial", "item", "Corta chapa deformada (portilla de P-2, E-1). Vibra: +1 Atención de la colonia."),
    "soldador": ("Soldador industrial", "item", "Repara juntas y derivaciones. Vibración y calor."),
    "botiquin": ("Botiquín de trauma", "item", "Contiene hemorragias y férulas; imprescindible para sacar heridos por el portillo."),
    "dron": ("Dron de inspección", "item", "Explora tramos sin aire o con costreros sin exponer a nadie."),
    "cable": ("Carrete de cable de 200 m", "item", "Lleva el banco de C-0 hasta la portilla de P-2: 30 min de tendido."),
    "cuerda": ("Cuerda, anclajes y arnés", "item", "Paso alto: 15–30 min para anclar; después, cruces sin tirada. Izar heridos."),
    "herramienta-par": ("Herramienta de par y llaves de válvula", "item", "Cerrar V-12 a mano (45–90 min, gradual), actuadores, pernos del portillo."),
    "recambio-mochila": ("Recambio de mochila", "item", "10 min con ayuda: otra mochila de traje de faena (12 h normales, 4 h en esfuerzo)."),
    "senuelo": ("Señuelo vibratorio", "item", "Martillo neumático pequeño: en un corredor lateral, aparta a los exploradores durante 30 min."),
    "filtro-portatil": ("Filtro portátil", "item", "+0,3 kg de absorción (R-3) o algo más de 3 h de aire para P-2. Cabe por cualquier abertura."),
    "carabina": ("Carabina reglamentaria ACE", "weapon", "Fuego selectivo. Disparar en instalaciones presurizadas puede dañar conductos."),
    "esposas": ("Esposas", "item", "Custodia. Atar a alguien junto al agua tiene consecuencias."),
    "lector-quimico": ("Lector químico portátil", "item", "Analiza costras: revela la estructura orgánica ordenada."),
    "analizador-fugas": ("Analizador de fugas", "item", "Localiza fugas de gas y caídas de presión en juntas."),
}
ITEMS = []
OBJ_ID = {}


def objetos():
    fol = folder("Item", "Nádir · Objetos", sort=100)
    for k, (n, tipo, d) in OBJETOS.items():
        sysd = {"description": "<p>%s</p>" % d, "quantity": 1}
        if tipo == "weapon":
            sysd = {"description": "<p>%s</p>" % d, "damage": "4d10", "ranges": {"short": 20, "medium": 50, "long": 150, "value": ""}, "shots": 3,
                    "ammo": 30, "useAmmo": True, "settings": {"firstEdition": True}}
        iid = fid("obj:" + k)
        OBJ_ID[k] = iid
        ITEMS.append({"_id": iid, "name": n, "type": tipo, "img": "icons/svg/item-bag.svg" if tipo == "item" else "icons/svg/sword.svg", "system": sysd,
                      "folder": fol, "sort": len(ITEMS) * 10, "ownership": {"default": 0}, "flags": {}, "effects": []})


# ---------------- PNJ y pregenerados completos ----------------
def secciones(md_file):
    t = open(os.path.join(ROOT, "docs", "texto", md_file)).read()
    return {m.group(1).split(" — ")[0].strip(): m.group(2) for m in re.finditer(r"^## (.+?)\n(.*?)(?=^## |\Z)", t, re.S | re.M)}


def html_md(md):
    return "".join(h for k, h in B.md_blocks(md, {}))


def enriquecer_actores():
    pnj = secciones("07-pnj.md")
    pj = secciones("10-tripulacion.md")
    cost = open(os.path.join(ROOT, "docs", "texto", "03-costreros.md")).read()
    mcost = re.search(r"^## (?:Cómo describirlos|Conducta).*?(?=^## |\Z)", cost, re.S | re.M)
    for a in ACTORS:
        nombre = a["name"]
        sec = next((v for k, v in {**pnj, **pj}.items() if k.split()[0] in nombre or nombre.split()[0] in k), None)
        if a["type"] == "creature":
            if sec:
                a["system"]["biography"] = '<div class="mr-nadir-j">%s</div>' % html_md(sec) + a["system"]["biography"]
            elif "Costrero" in nombre or "Enjambre" in nombre:
                a["system"]["biography"] = '<div class="mr-nadir-j">%s</div>' % html_md(mcost.group(0) if mcost else "") + a["system"]["biography"]
            a["system"]["description"] = a["system"]["biography"]
            # armas como objetos de la ficha
            pid = a["_pid"]
            for w in ([] if pid in MEC.get("pnj", {}) else CANON["pnj"].get(pid, {}).get("armas", [])):
                dano = re.search(r"\d+d\d+(?:\+\d+)?", w["dano"])
                a["items"].append({"_id": fid("aw:%s:%s" % (pid, w["n"])), "name": w["n"], "type": "weapon", "img": "icons/svg/sword.svg",
                                   "system": {"description": "<p>%s</p>" % w["dano"], "damage": dano.group(0) if dano else "1d10", "settings": {"firstEdition": True}},
                                   "effects": [], "flags": {}, "sort": 0})
            a["prototypeToken"]["sight"] = {"enabled": False}
            a["prototypeToken"]["displayBars"] = 20
        else:
            if sec:
                a["system"]["biography"] = '<div class="mr-nadir-j">%s</div>' % html_md(sec) + a["system"]["biography"]
            a["items"].append({"_id": fid("arm:" + nombre), "name": "Traje de faena", "type": "armor", "img": "icons/svg/shield.svg",
                               "system": {"description": "<p>Traje de faena HRF/ACE (PA 3, Velocidad [−]). Mochila: 12 h normales, 4 h bajo esfuerzo o estrés; con umbilical no se gasta. Perforado, se despresuriza en 1d5 asaltos.</p>",
                                          "armorPoints": 3, "damageReduction": 0, "oxygenMax": 720, "oxygenCurrent": 720, "equipped": True},
                               "effects": [], "flags": {}, "sort": 0})
            a["prototypeToken"]["sight"] = {"enabled": True, "range": 15, "visionMode": "basic", "angle": 360}
            a["prototypeToken"]["light"] = {"bright": 3, "dim": 9, "angle": 80, "color": "#cfe8ff", "alpha": 0.35, "luminosity": 0.5}
            a["prototypeToken"]["displayBars"] = 30
            a["prototypeToken"]["bar2"] = {"attribute": "other.stress"}


RANGO = {"Entrenado": ("Trained", 10), "Experto": ("Expert", 15), "Maestro": ("Master", 20)}


def _arma(clave, w):
    """Arma 1e del sistema mosh a partir de una entrada de mecanica.json."""
    desc = " · ".join(x for x in (w.get("desc", ""), ("Herida: " + w["herida"]) if w.get("herida") else "", w.get("especial", "")) if x)
    rng = {"short": w.get("corto", 0), "medium": w.get("medio", 0), "long": w.get("largo", 0), "value": w.get("alcance", "")}
    sysd = {"description": "<p>%s</p>" % B.esc(desc), "damage": w.get("dano", "1d10"), "ranges": rng, "wound": w.get("herida", ""),
            "woundEffect": w.get("especial", ""), "settings": {"firstEdition": True}}
    if w.get("cargador"):
        sysd.update({"useAmmo": True, "shots": w["cargador"], "curShots": w["cargador"], "ammo": w.get("municion", w["cargador"])})
    return {"_id": fid(clave), "name": w["n"], "type": "weapon", "img": icono("armas", w["n"], icono("equipo", w["n"], "icons/svg/sword.svg")),
            "system": sysd, "effects": [], "flags": {}, "sort": 0}


def _bloque_juego(m):
    """Lo que el Guardián necesita en mesa: qué quiere, cómo reacciona, cómo pelea."""
    filas = "".join("<tr><td>%s</td><td>%s</td></tr>" % (B.inline(r["si"]), B.inline(r["entonces"])) for r in m.get("reacciones", []))
    partes = ['<div class="mr-nadir-j mr-nadir-juego"><h3>En juego</h3>']
    for et, k in (("Quiere", "quiere"), ("Teme", "teme")):
        if m.get(k):
            partes.append("<p><b>%s:</b> %s</p>" % (et, B.inline(m[k])))
    if filas:
        partes.append("<table><thead><tr><th>Si…</th><th>Entonces</th></tr></thead><tbody>%s</tbody></table>" % filas)
    for et, k in (("En combate", "en_combate"), ("Se rinde o huye", "se_rinde")):
        if m.get(k):
            partes.append("<p><b>%s:</b> %s</p>" % (et, B.inline(m[k])))
    if m.get("frase"):
        partes.append("<blockquote>%s</blockquote>" % B.inline(m["frase"]))
    return "".join(partes) + "</div>"


def mecanica():
    """Fichas jugables: habilidades, especiales, ataques y reacciones de los PNJ; armas, traje y equipo de los PJ;
    respuesta al trauma en su campo de la ficha; iconos de todos los objetos."""
    tripu = open(os.path.join(ROOT, "docs", "texto", "10-tripulacion.md")).read()
    trauma_txt = dict(re.findall(r"^Clase \*\*(.+?)\*\* · Estrés \d+ · Respuesta al trauma: (.+)$", tripu, re.M))
    for a in ACTORS:
        pid = a.pop("_pid")
        if a["type"] == "creature":
            m = MEC.get("pnj", {}).get(pid)
            if not m:
                continue
            bicho = pid in ("costrero", "defensor", "enjambre")
            for s in m.get("habilidades", []):
                rank, bonus = RANGO.get(s.get("rango"), ("Trained", 10))
                a["items"].append({"_id": fid("pnj:%s:sk:%s" % (pid, s["n"])), "name": s["n"], "type": "skill", "img": icono("habilidades", s["n"], "icons/svg/book.svg"),
                                   "system": {"description": "", "rank": rank, "bonus": bonus, "prerequisite_ids": []}, "effects": [], "flags": {}, "sort": 0})
            for h in m.get("especiales", []):
                a["items"].append({"_id": fid("pnj:%s:ab:%s" % (pid, h["n"])), "name": h["n"], "type": "ability",
                                   "img": ICON.get("habilidad_criatura" if bicho else "habilidad_pnj", "icons/svg/aura.svg"),
                                   "system": {"description": "<p>%s</p>" % B.inline(h["texto"]), "text": "", "roll": ""}, "effects": [], "flags": {}, "sort": 0})
            # quien no lleva arma pelea con lo que tenga a mano (el ataque del preso genérico)
            for w in m.get("armas") or ([] if bicho else MEC["pnj"]["preso"]["armas"][:1]):
                a["items"].append(_arma("pnj:%s:w:%s" % (pid, w["n"]), w))
            juego = _bloque_juego(m)
            a["system"]["biography"] = juego + a["system"]["biography"]
            a["system"]["description"] = a["system"]["biography"]
        else:
            m = MEC.get("pregenerados", {}).get(pid, {})
            p = CANON["pregenerados"][pid]
            trauma = m.get("trauma") or trauma_txt.get(p["clase"], "")
            a["system"].setdefault("other", {})["stressdesc"] = {"value": trauma[:1].upper() + trauma[1:]}
            if m:   # el equipo estructurado sustituye a los objetos sueltos del canon
                a["items"] = [i for i in a["items"] if i["type"] == "skill"]
                for w in m.get("armas", []):
                    a["items"].append(_arma("pj:%s:w:%s" % (pid, w["n"]), w))
                ar = m.get("armadura")
                if ar:
                    a["items"].append({"_id": fid("arm:" + a["name"]), "name": ar["n"], "type": "armor", "img": ICON.get("traje", "icons/svg/shield.svg"),
                                       "system": {"description": "<p>%s</p>" % B.esc(ar.get("desc", "")), "armorPoints": ar.get("pa", 3), "damageReduction": ar.get("rd", 0),
                                                  "speed": ar.get("velocidad", ""), "oxygenMax": ar.get("oxigeno_h", 12) * 60, "oxygenCurrent": ar.get("oxigeno_h", 12) * 60,
                                                  "equipped": True}, "effects": [], "flags": {}, "sort": 0})
                for o in m.get("objetos", []):
                    a["items"].append({"_id": fid("pj:%s:o:%s" % (pid, o["n"])), "name": o["n"], "type": "item", "img": icono("equipo", o["n"], "icons/svg/item-bag.svg"),
                                       "system": {"description": "<p>%s</p>" % B.esc(o.get("desc", "")), "quantity": o.get("cantidad", 1)}, "effects": [], "flags": {}, "sort": 0})
        for i in a["items"]:   # iconos de lo que venga del canon
            if i["img"] == "icons/svg/book.svg" and i["type"] == "skill":
                i["img"] = icono("habilidades", i["name"], i["img"])
            elif i["img"] in ("icons/svg/item-bag.svg", "icons/svg/sword.svg"):
                i["img"] = icono("equipo", i["name"], icono("armas", i["name"], i["img"]))
            elif i["type"] == "armor" and i["img"] == "icons/svg/shield.svg":
                i["img"] = ICON.get("traje", i["img"])
    for it in ITEMS:
        k = next((k for k, v in OBJ_ID.items() if v == it["_id"]), None)
        if k:
            it["img"] = ICON.get("objetos", {}).get(k, it["img"])


# ---------------- escenas: mapas de fósforo + escenas de imagen ----------------
MAPA_SLUG = {"c7": "Sector C-7", "b4": "Frente B-4", "ruta": "Superficie de Nádir"}
MAPA_MUSICA = {"c7": ("exploracion", ["hum"]), "b4": ("turno", ["hum"]), "ruta": ("superficie", ["casco-respiracion"])}
LUCES = {"1": ("#9fe8ff", 0.5, "torch"), "7": ("#ffb060", 0.35, None), "8": ("#ffd090", 0.35, "flame"), "3": ("#ff4030", 0.3, "pulse"),
         "9": ("#a0d0ff", 0.25, None), "10": ("#a0d0ff", 0.25, None), "X": ("#ffd090", 0.3, None), "2": ("#ffd090", 0.2, None)}
OSCURAS = {"4": 0.95, "5": 0.97, "6": 0.95, "12": 0.9, "11": 0.8}


def rect_shapes(rects):
    return [{"type": "rectangle", "x": x * M.G, "y": y * M.G, "width": w * M.G, "height": h * M.G, "rotation": 0, "hole": False} for (x, y, w, h) in rects]


def region(key, nombre, shapes, behaviors, color="#5dff8a"):
    return {"_id": fid("reg:" + key), "name": nombre, "color": color, "shapes": shapes, "elevation": {"bottom": None, "top": None},
            "behaviors": behaviors, "visibility": 0, "locked": True, "flags": {}}


def comp(key, tipo, system, nombre=""):
    return {"_id": fid("beh:" + key), "name": nombre, "type": tipo, "system": system, "disabled": False, "flags": {}}


def estancia_de(mapa, sala):
    return next((e for e in ESTANCIAS if e["mapa"] == mapa and e["sala"] == sala), None)


def escenas():
    walls = json.load(open(os.path.join(M.OUT, "walls.json")))
    ids = {m: fid("scene:" + m) for m in MAPA_SLUG}
    tele = {}   # puntos de teletransporte: (mapa, clave) -> region id
    for mapa in MAPA_SLUG:
        regions, notes, lights, sounds = [], [], [], []
        if mapa in M.DECKS:
            deck = M.DECKS[mapa]
            for sala, rects in deck["rooms"].items():
                e = estancia_de(mapa, sala)
                if not e:
                    continue
                x, y, w, h = max(rects, key=lambda r: r[2] * r[3])
                cx, cy = (x + w / 2) * M.G, (y + h / 2) * M.G
                notes.append({"_id": fid("note:%s:%s" % (mapa, sala)), "entryId": LECT_JE, "pageId": LECT_PAGE[e["id"]], "x": int(cx), "y": int(cy + 0.9 * M.G),
                              "elevation": 0, "sort": 0, "texture": {"src": "icons/svg/eye.svg", "tint": "#9dffb0"}, "iconSize": 44, "text": e["nombre"],
                              "fontFamily": "Signika", "fontSize": 26, "textAnchor": 1, "textColor": "#c8ffd2", "global": False, "flags": {}})
                beh = [comp("zona:%s:%s" % (mapa, sala), "executeScript", {"events": ["tokenMoveIn"],
                       "source": 'game.modules.get("mr-nadir")?.api?.zona(%s, event.data.token);' % json.dumps(e["id"])}, "Aviso al Guardián")]
                if mapa == "c7" and sala in OSCURAS:
                    beh.append(comp("osc:%s" % sala, "adjustDarknessLevel", {"mode": 0, "modifier": OSCURAS[sala]}, "Zona oscura"))
                regions.append(region("%s:%s" % (mapa, sala), "Zona · " + e["nombre"], rect_shapes(rects), beh))
                lt = LUCES.get(sala) if mapa == "c7" else ("#fff0d0", 0.4, None)
                if lt:
                    col, alpha, anim = lt
                    rad = max(w, h) * 0.75 * 1.5
                    lights.append({"_id": fid("light:%s:%s" % (mapa, sala)), "x": int(cx), "y": int(cy), "rotation": 0, "walls": True, "vision": False,
                                   "config": {"bright": rad * 0.35, "dim": rad, "color": col, "alpha": alpha, "angle": 360, "luminosity": 0.5,
                                              "animation": {"type": anim, "speed": 3, "intensity": 3} if anim else {"type": None}},
                                   "hidden": False, "flags": {}})
                for j, a in enumerate(x for x in e["sfx_auto"] if x != "casco-respiracion"):
                    sounds.append({"_id": fid("as:%s:%s:%s" % (mapa, sala, a)), "x": int(cx), "y": int(cy), "radius": max(w, h) * 1.5 * 0.9, "path": AUD + "sfx/%s.ogg" % a,
                                   "repeat": True, "volume": 0.35, "walls": True, "easing": True, "hidden": False, "elevation": 0,
                                   "darkness": {"min": 0, "max": 1}, "effects": {}, "flags": {}})
            if mapa == "c7":
                tele[("c7", "X")] = fid("reg:c7:X")
            if mapa == "b4":
                tele[("b4", "B7")] = fid("reg:b4:B7")
        else:
            for n, (x, y) in M.RUTA["nodos"].items():
                e = next((e for e in ESTANCIAS if e["mapa"] == "ruta" and e["sala"] == n), None)
                key = "ruta:" + n
                shapes = rect_shapes([(x - 0.8, y - 0.8, 1.6, 1.6)])
                beh = []
                if e:
                    beh.append(comp("zona:" + key, "executeScript", {"events": ["tokenMoveIn"],
                               "source": 'game.modules.get("mr-nadir")?.api?.zona(%s, event.data.token);' % json.dumps(e["id"])}, "Aviso al Guardián"))
                regions.append(region(key, "Nodo · " + n, shapes, beh))
                tele[("ruta", n)] = fid("reg:" + key)
                for e2 in [x2 for x2 in ESTANCIAS if x2["mapa"] == "ruta" and x2["sala"] == n]:
                    notes.append({"_id": fid("note:ruta:" + e2["id"]), "entryId": LECT_JE, "pageId": LECT_PAGE[e2["id"]], "x": int(x * M.G), "y": int((y + 1.3) * M.G),
                                  "elevation": 0, "sort": 0, "texture": {"src": "icons/svg/eye.svg", "tint": "#9dffb0"}, "iconSize": 40, "text": e2["nombre"],
                                  "fontFamily": "Signika", "fontSize": 24, "textAnchor": 1, "textColor": "#c8ffd2", "global": False, "flags": {}})
        musica_k, amb = MAPA_MUSICA[mapa]
        pl = playlist_escena(mapa, MAPA_SLUG[mapa], musica_k, amb)
        ws = walls.get(mapa, [])
        SCENES.append({
            "_id": ids[mapa], "name": "Nádir · Mapa · " + MAPA_SLUG[mapa], "active": False, "navigation": True, "navOrder": len(SCENES), "navName": MAPA_SLUG[mapa],
            "background": {"src": "%s/assets/maps/%s.webp" % (MOD, mapa)}, "thumb": "%s/assets/maps/%s.webp" % (MOD, mapa),
            "width": M.W * M.G, "height": M.H * M.G, "padding": 0, "initial": {"x": 2000, "y": 1300, "scale": 0.45}, "backgroundColor": "#010603",
            "grid": {"type": 1 if mapa != "ruta" else 0, "size": M.G, "style": "solidLines", "thickness": 1, "color": "#3cff70", "alpha": 0.08, "distance": 1.5, "units": "m"},
            "tokenVision": mapa != "ruta", "fog": {"exploration": mapa != "ruta", "colors": {"explored": "#021a08", "unexplored": "#000000"}},
            "environment": {"darknessLevel": {"c7": 0.6, "b4": 0.25, "ruta": 0}[mapa], "globalLight": {"enabled": mapa == "ruta"}},
            "walls": [{"_id": fid("wall:%s:%d" % (mapa, k)), "c": w["c"], "move": 1, "sense": 1, "sound": 1, "light": 1, "door": w["door"], "ds": w["ds"], "dir": 0, "flags": {}} for k, w in enumerate(ws)],
            "notes": notes, "tokens": [], "lights": lights, "sounds": sounds, "tiles": [], "drawings": [], "templates": [], "regions": regions,
            "playlist": pl, "folder": folder("Scene", "Nádir · Mapas", sort=100), "sort": len(SCENES) * 10, "ownership": {"default": 0},
            "flags": {"mr-nadir": {"slug": mapa, "tipo": "mapa", "mapa": mapa, "nombre": MAPA_SLUG[mapa], "relojes": ["r3", "p2", "bomba", "h4"] if mapa == "c7" else [], "acciones": []}}})
    # teletransportes (destino = región en otra escena)
    pares = [(("c7", "X"), ("ruta", "C-7")), (("b4", "B7"), ("ruta", "B-4"))]
    def reg_by(mapa, rid):
        sc = next(s for s in SCENES if s["_id"] == ids[mapa])
        return next(r for r in sc["regions"] if r["_id"] == rid)
    for a, b in pares:
        for src, dst in ((a, b), (b, a)):
            r = reg_by(src[0], tele[src])
            r["behaviors"].append(comp("tele:%s:%s" % src, "teleportToken", {"destination": "Scene.%s.Region.%s" % (ids[dst[0]], tele[dst]), "choice": True}, "Ir a " + MAPA_SLUG[dst[0]]))
    # escenas de imagen
    fol_img = folder("Scene", "Nádir · Escenas de imagen", sort=200)
    for i, e in enumerate(ESTANCIAS):
        img_id = e["reutiliza"] or e["imagen"]
        src = "%s/assets/art/%s.webp" % (MOD, img_id)
        w, h = 1536, 1024
        p = os.path.join(ASSETS, "art", img_id + ".webp")
        if os.path.exists(p):
            w, h = Image.open(p).size
        pl = playlist_escena(e["id"], e["nombre"], e["musica"], e["sfx_auto"])
        SCENES.append({
            "_id": fid("scene:img:" + e["id"]), "name": "Nádir · " + e["nombre"], "active": False, "navigation": False, "navName": e["nombre"],
            "background": {"src": src}, "thumb": src, "width": w, "height": h, "padding": 0, "initial": {"x": w // 2, "y": h // 2, "scale": 1},
            "backgroundColor": "#000000", "grid": {"type": 0, "size": 100, "alpha": 0}, "tokenVision": False, "fog": {"exploration": False},
            "environment": {"darknessLevel": 0, "globalLight": {"enabled": True}}, "walls": [], "notes": [], "tokens": [], "lights": [], "sounds": [],
            "tiles": [], "drawings": [], "templates": [], "regions": [], "journal": LECT_JE, "journalEntryPage": LECT_PAGE[e["id"]], "playlist": pl,
            "folder": fol_img, "sort": i * 10, "ownership": {"default": 0},
            "flags": {"mr-nadir": {"slug": e["id"], "tipo": "imagen", "mapa": e["mapa"], "nombre": e["nombre"], "sfx": [[k, SFX_NOMBRE[k]] for k in e["sfx_manual"]], "relojes": e["relojes"], "acciones": e["acciones"]}}})
    for s_ in SCENES:
        if s_["flags"]["mr-nadir"]["tipo"] == "mapa":
            s_["journal"] = LECT_JE


# ---------------- guion de dirección ----------------
def guion():
    fol = folder("JournalEntry", "Nádir · Guía del Guardián", sort=100)
    t = open(os.path.join(ROOT, "docs", "v2", "guion.md")).read()
    actor_id = {}
    for pid, p in list(CANON["pnj"].items()) + list(CANON["pregenerados"].items()):
        actor_id[pid] = (fid("actor:" + pid), p["nombre"])
    doc_by = {}
    for j in JOURNALS:
        if j.get("flags", {}).get("mr-nadir", {}).get("doc"):
            doc_by.setdefault(j["flags"]["mr-nadir"]["doc"], []).append(j)

    def rep(m):
        k, v = m.group(1), m.group(2)
        if k == "escena":
            return "@NadirEscena[%s]{%s}" % (v, EST[v]["nombre"])
        if k == "mapa":
            return "@NadirMapa[%s]{Mapa: %s}" % (v, MAPA_SLUG[v])
        if k == "sfx":
            return "@NadirSfx[%s]{%s}" % (v, SFX_NOMBRE[v])
        if k == "musica":
            return "@NadirMusica[%s]{Música: %s}" % (v, MUSICAS[v])
        if k == "actor":
            i, n = actor_id[v]
            return "@UUID[Actor.%s]{%s}" % (i, n)
        if k == "objeto":
            return "@UUID[Item.%s]{%s}" % (OBJ_ID[v], OBJETOS[v][0])
        if k == "doc":
            js = doc_by[v]  # KeyError si el guion cita un documento que no existe
            if len(js) == 1:
                return "@UUID[JournalEntry.%s]{%s} @NadirDoc[%s]{Mostrar}" % (js[0]["_id"], js[0]["name"], v)
            # registro por tramos o variantes: un enlace y un botón por parte, para entregar solo las que tocan
            return "%s (%s)" % (v, "; ".join("@UUID[JournalEntry.%s]{%s} @NadirDoc[%s/%d]{Mostrar}" % (
                j["_id"], j["name"].split(" · ", 1)[1], v, j["flags"]["mr-nadir"]["parte"]) for j in js))
        if k == "panel":
            return "@NadirPanel[]{Panel de emergencia}"
        if k == "reloj":
            return "@NadirReloj[%s]{Reloj %s min}" % (v.replace("+", ""), v)
        return m.group(0)
    t = re.sub(r"\{\{(\w+)(?::([^}]*))?\}\}", rep, t)
    pages = []
    for k, (pt, md) in enumerate(split_pages(t, "guion")):
        html = "".join(h for kind, h in B.md_blocks(md, {}))
        if k == 0 and not md.strip():
            continue
        pages.append(page("guion:%d" % k, pt or "Guion de dirección", html, (k + 1) * 100))
    JOURNALS.append({"_id": fid("je:guion"), "name": "★ Guion de dirección", "pages": pages, "folder": fol, "sort": -100, "ownership": {"default": 0}, "flags": {}})
    # guía de uso de las herramientas (la abre el botón «?» de la barra del Guardián)
    ayuda = open(os.path.join(ROOT, "docs", "v2", "herramientas.md")).read()
    pags = [page("ayuda:%d" % k, pt or "Cómo usar las herramientas", "".join(h for kind, h in B.md_blocks(md, {})), (k + 1) * 100)
            for k, (pt, md) in enumerate(split_pages(ayuda, "ayuda")) if md.strip()]
    JOURNALS.append({"_id": fid("je:ayuda"), "name": "★ Cómo usar las herramientas", "pages": pags, "folder": fol, "sort": -90, "ownership": {"default": 0},
                     "flags": {"mr-nadir": {"ayuda": True}}})


if __name__ == "__main__":
    main()
