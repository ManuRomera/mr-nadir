#!/usr/bin/env python3
"""Edición de lectura: misma tipografía de revista, figuras únicas y atlas único.
No altera los generadores ni los documentos del módulo. python3 tools/build_editorial.py
"""
from pathlib import Path
import sys,re,json
import build_pdf as B
R=Path(B.ROOT)
OUT=R.parent/'output/pdf/nadir-edicion-editorial'
OUT.mkdir(parents=True,exist_ok=True)
B.MAPAS={}
# Las láminas se integran con el texto; el artículo y su resumen comparten página.
B.is_portrait=lambda iid:False
_original_table=B.parse_table

def parse_table(lines):
    headers=[c.strip() for c in lines[0].strip().strip("|").split("|")]
    if headers==["Fuerza","Velocidad","Intelecto","Combate","Cordura","Miedo","Cuerpo","Salud","Heridas"] and len(lines)==3:
        values=[c.strip() for c in lines[2].strip().strip("|").split("|")]
        return '<div class="statgrid">'+"".join('<div><em>'+B.esc(h)+'</em><strong>'+B.esc(v)+'</strong></div>' for h,v in zip(headers,values))+'</div>'
    return _original_table(lines)
B.parse_table=parse_table
_original_figure=B.figure

def figure(iid,cap,mode):
    h=_original_figure(iid,cap,mode)
    return h.replace('<figure class="wide">','<figure class="wide specimen">') if iid.startswith('lam-') else h
B.figure=figure
B.CSS+='''
.opener { page:auto; padding-top:3mm; }
.opener h1 { font-size:34pt; margin:3mm 0 4mm; }
.abstract { padding:3mm 4mm; margin-bottom:4mm; font-size:8.5pt; }
.abstract .kw { font-size:7pt; }
.cols { column-fill:balance; }
figure.ret { float:right; width:37mm; margin:2mm 0 3mm 4mm; }
figure.ret img { height:43mm; aspect-ratio:auto; object-fit:cover; }
figure.ret figcaption { font-size:6.3pt; }
figure.wide img { max-height:75mm; object-fit:cover; }
figure.specimen img { height:100mm; max-height:100mm; object-fit:contain; background:#fbf9f4; }
.atlas { break-before:page; }
.atlas h1 { font:700 29pt 'Avenir Next Condensed'; color:var(--teal); margin:0 0 4mm; }
.atlas img { width:100%; height:205mm; object-fit:contain; }
.atlas figcaption { margin-top:3mm; }
.statgrid { display:grid; grid-template-columns:repeat(5,1fr); gap:1px; margin:3mm 0; break-inside:avoid; background:#d2d8d6; border:.3mm solid #0f3a40; }
.statgrid div { background:#f4f2eb; text-align:center; padding:1.5mm .5mm; }
.statgrid em { display:block; font:600 5.5pt "Avenir Next Condensed"; color:#0f3a40; }
.statgrid strong { font:700 13pt "Avenir Next Condensed"; }
td:first-child,th:first-child { min-width:12mm; overflow-wrap:normal; hyphens:none; }
.toc a { color:inherit; text-decoration:none; }
.toc li { font-size:10pt; padding:2.1mm 0; }
'''
# La contraportada usa una imagen distinta de la ilustración de los finales.
contra=B.contraportada
B.contraportada=lambda:contra().replace(B.img_path('fig-final'),B.img_path('fig-rover'))

def atlas():
    out=[]
    for ident,title,file,caption in [
      ('atlas-b4','Atlas · Frente B-4','b4-paper.png','Punto de partida de la cuadrilla M-4. Taller, laboratorio, soporte vital y salida del rover.'),
      ('atlas-ruta','Atlas · Superficie','ruta-paper.png','Ruta por R-12 y atajo hasta C-7. Las distancias y el terreno determinan tiempo y energía.'),
      ('atlas-c7','Atlas · Sector C-7','c7-operativo-v.svg','Plano operativo: accesos, atmósferas, inundación y equipos. Los números corresponden a las localizaciones del Acto III.')]:
      out.append(f'<section class="atlas" id="{ident}"><div class="kicker">ANEXO CARTOGRÁFICO</div><h1>{title}</h1><figure><img src="file://{B.MAPS}/{file}"><figcaption>{caption}</figcaption></figure></section>')
    return ''.join(out)

def construir(pages):
    B.fig_n[0]=0;B.usadas.clear();items=[];body=[]
    for i,n in enumerate(B.ORDEN):
      cid,title,h=B.capitulo(n,i);items.append((cid,B.SECCION[n],title));body.append(h)
    items.append(('atlas-b4','Atlas','Planos de B-4, superficie y C-7'))
    toc=B.indice(items,pages).replace('Los planos están en cada cubierta y en el apéndice.','Los tres planos aparecen una sola vez en el atlas final. Las hojas de personaje y las copias recortables están en el volumen de material de juego.')
    for cid,_,title in items:
      toc=toc.replace('<span>'+B.inline(title)+'</span>','<span><a href="#'+cid+'">'+B.inline(title)+'</a></span>')
    return '<!doctype html><html lang="es"><meta charset="utf-8"><title>Nádir · Edición editorial</title><style>'+B.CSS.replace('BRANDDIR','file://'+str(R/'brand'))+'</style><body>'+B.portada()+toc+''.join(body)+atlas()+B.contraportada()+'</body></html>',items

hp=OUT/'edicion.html';pdf=OUT/'Nadir-Sangre-bajo-el-hielo-edicion-editorial.pdf'
for run in range(2):
    html,items=construir({} if run==0 else pages);hp.write_text(html);B.pdf(str(hp),str(pdf))
    pages=B.paginas_de(str(pdf),items)
    import fitz
    doc=fitz.open(pdf)
    for i,p in enumerate(doc):
      if 'Atlas · Frente B-4' in p.get_text():pages['atlas-b4']=str(i+1)
# Material de mesa separado: sin repetir documentos, fichas o mapas dentro del libro principal.
material=OUT/'Nadir-Material-de-juego-edicion-editorial.pdf';mh=OUT/'material.html'
B.fig_n[0]=0;B.usadas.clear()
_,_,tools=B.capitulo('08b-herramientas',B.ORDEN.index('08b-herramientas'))
# En el volumen de herramientas basta el atlas completo de esta edición.
mh.write_text('<!doctype html><html lang="es"><meta charset="utf-8"><style>'+B.CSS.replace('BRANDDIR','file://'+str(R/'brand'))+'</style><body>'+tools+B.imprimibles()+B.hojas()[B.hojas().index('<section class="hoja"'):]+atlas()+'</body></html>')
B.pdf(str(mh),str(material))
print(json.dumps({'libro':str(pdf),'paginas':len(fitz.open(pdf)),'material':str(material),'paginas_material':len(fitz.open(material)),'indice':pages},ensure_ascii=False,indent=2))

# Las láminas y esquemas se añaden después de estabilizar índice y paginación.
import subprocess
(OUT/'figuras-editoriales.json').unlink(missing_ok=True)
subprocess.run([sys.executable,str(R/'tools/finish_editorial_pdf.py')],check=True)

# Las releases del módulo publican estos nombres estables desde docs/.
import shutil
shutil.copy2(pdf,R/'docs/Nadir-Sangre-bajo-el-hielo.pdf')
shutil.copy2(material,R/'docs/Nadir-Material-de-juego.pdf')
