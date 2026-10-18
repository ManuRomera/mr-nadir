"""Verifica títulos con contenido y grandes huecos de maquetación."""
from pathlib import Path
import re,json,unicodedata,xml.etree.ElementTree as ET
import fitz
R=Path(__file__).resolve().parents[1];OUT=R.parent/'output/pdf/nadir-edicion-editorial'
s=(OUT/'edicion.html').read_text();body=s.split('<body>',1)[1].rsplit('</body>',1)[0]
body=re.sub(r'<(img|br|hr|meta|link|input)(\b[^>]*?)(?<!/)>',r'<\1\2/>',body)
root=ET.fromstring('<root>'+body+'</root>')
def norm(s):return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',s.lower()))
def text(e):return ''.join(e.itertext())
doc=fitz.open(OUT/'Nadir-Sangre-bajo-el-hielo-edicion-editorial.pdf');pages=[norm(p.get_text()) for p in doc]
checks=[];bad=[]
for e in root.iter():
 cls=e.attrib.get('class','').split();heads=[];target=''
 if 'lead' in cls or 'illustrated' in cls:
  children=list(e)
  heads=[c for c in children if c.tag in ['h2','h3']]
  others=[c for c in children if c.tag not in ['h2','h3']]
  if others:
   node=others[0]
   if node.tag=='figure':target=text(node.find('figcaption'))
   elif node.attrib.get('class','')=='documento':target=text(node.find('h4'))
   elif node.attrib.get('class','')=='ficha':target=text(node.find('./header/h4'))
   else:target=text(node)
 elif 'fulltable' in cls:
  caption=e.find('./table/caption');row=e.find('./table/tbody/tr')
  if caption is not None:heads=list(caption.iter('h2'))+list(caption.iter('h3'))
  if row is not None:target=text(row)
 if not heads or not target:continue
 tn=norm(target)[:48]
 for h in heads:
  hn=norm(text(h));hp=[i+1 for i,p in enumerate(pages) if hn in p];both=[i for i in hp if tn in pages[i-1]]
  item={'titulo':text(h),'paginas':hp,'contenido_en_misma_pagina':both,'primer_bloque':target[:130]}
  checks.append(item)
  if not both:bad.append(item)
result={'titulos_comprobados':len(checks),'titulos_sin_primer_bloque':bad,'comprobaciones':checks}
(OUT/'titulos.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));(R/'docs/revision/titulos-pdf.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print('Títulos comprobados:',len(checks),'pendientes:',len(bad))
if bad:print(json.dumps(bad,ensure_ascii=False,indent=2))
assert not bad
