#!/usr/bin/env python3
"""Valida docs/texto/*.md: bloques ::: balanceados, figuras permitidas y únicas, palabras."""
import glob, json, re, collections
ids = {i["id"] for i in json.load(open("docs/arte/prompts.json"))["imagenes"] if i["id"].startswith(("fig-", "ret-", "lam-"))}
usadas = collections.Counter()
tot = 0
for f in sorted(glob.glob("docs/texto/*.md")):
    t = open(f).read()
    pal = len(re.findall(r"\w+", t)); tot += pal
    abre = len(re.findall(r"^::: ?\w+", t, re.M)); cierra = len(re.findall(r"^:::\s*$", t, re.M))
    figs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", t)
    for g in figs: usadas[g] += 1
    mal = [g for g in figs if g not in ids]
    h1 = len(re.findall(r"^# ", t, re.M))
    print(f"{f.split('/')[-1]:44} {pal:6} pal  bloques {abre}/{cierra} {'OK' if abre==cierra else 'DESCUADRE'}  h1={h1}  figs={len(figs)} {'MAL:'+str(mal) if mal else ''}")
print("TOTAL palabras", tot)
print("Figuras repetidas:", {k: v for k, v in usadas.items() if v > 1})
print("Figuras sin usar:", sorted(ids - set(usadas)))
