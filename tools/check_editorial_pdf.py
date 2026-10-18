#!/usr/bin/env python3
"""Comprueba contenido, navegación e ilustraciones del PDF editorial generado."""
from pathlib import Path
import fitz,collections,unicodedata,re,json
from html.parser import HTMLParser
R=Path(__file__).resolve().parents[1]
out=R.parent/'output/pdf/nadir-edicion-editorial'
d=fitz.open(out/'Nadir-Sangre-bajo-el-hielo-edicion-editorial.pdf')
class Blocks(HTMLParser):
 def __init__(self):super().__init__();self.s=[];self.b=[]
 def handle_starttag(self,t,a):
  if t in ['p','li','th','td','h1','h2','h3','h4','figcaption']:self.s.append([t,[]])
 def handle_data(self,v):
  for x in self.s:x[1].append(v)
 def handle_endtag(self,t):
  for i in range(len(self.s)-1,-1,-1):
   if self.s[i][0]==t:self.b.append(''.join(self.s[i][1]));del self.s[i:];break
h=Blocks();h.feed((out/'edicion.html').read_text())
def norm(s):return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',s.lower()))
n=norm(''.join(''.join(b[4] for b in p.get_text('blocks') if b[1]>45 and b[3]<792) for p in d))
missing=[];reordered=[]
for b in h.b:
 s=norm(b)
 if len(s)<20:continue
 for i in range(0,len(s)-20,34):
  f=s[i:i+34]
  if f in n:continue
  # Un párrafo puede cruzar página mientras un recuadro flota en la otra columna.
  # Exigir ambas partes (al menos diez caracteres) evita confundirlo con texto perdido.
  splits=[k for k in range(10,len(f)-9) if f[:k] in n and f[k:] in n]
  if splits:reordered.append({'parrafo':b[:80],'fragmento':f,'corte_verificado':splits[0]})
  else:missing.append({'texto':b[:100],'fragmento':f})
images=collections.defaultdict(set)
for i,p in enumerate(d):
 for im in p.get_image_info(hashes=True):
  r=fitz.Rect(im['bbox'])&p.rect
  # Excluir marca, máscaras de degradado y sombras rasterizadas del navegador.
  if max(im['width'],im['height'])>=1024 and r.width>80 and r.height>70:images[im['digest'].hex()].add(i+1)
reps=[sorted(v) for v in images.values() if len(v)>1]
check={'paginas_libro':len(d),'paginas_material':len(fitz.open(out/'Nadir-Material-de-juego-edicion-editorial.pdf')),'marcadores':len(d.get_toc()),'enlaces_indice':len(d[1].get_links()),'ilustraciones_repetidas':reps,'texto_no_localizado':missing,'fragmentos_comprobados_a_ambos_lados_de_un_salto':reordered,'figuras_editoriales':json.loads((out/'figuras-editoriales.json').read_text())}
(out/'preflight.json').write_text(json.dumps(check,ensure_ascii=False,indent=2));(R/'docs/revision/preflight-pdf.json').write_text(json.dumps(check,ensure_ascii=False,indent=2))
assert not missing,missing
assert not reps,reps
assert len(d[1].get_links())==14
print('Preflight OK:',len(d),'páginas,',len(d.get_toc()),'marcadores; ilustraciones únicas y contenido localizado.')
