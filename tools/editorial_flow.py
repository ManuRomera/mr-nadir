"""Flujo de revista: las figuras y tablas anchas salen de las columnas.
Cada título viaja con el primer bloque de su sección.
"""
from html.parser import HTMLParser
import re
class TopBlocks(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=False);self.depth=0;self.current=[];self.blocks=[]
 def add(self,s):
  if self.depth:self.current.append(s)
 def handle_starttag(self,t,a):
  raw=self.get_starttag_text()
  if self.depth==0:self.current=[]
  self.current.append(raw)
  if t not in {'img','br','hr','meta','link','input','wbr','source'}:self.depth+=1
  elif self.depth==0:self.blocks.append(''.join(self.current));self.current=[]
 def handle_startendtag(self,t,a):self.add(self.get_starttag_text())
 def handle_endtag(self,t):
  self.current.append('</'+t+'>');self.depth-=1
  if self.depth==0:self.blocks.append(''.join(self.current));self.current=[]
 def handle_data(self,s):self.add(s)
 def handle_entityref(self,s):self.add('&'+s+';')
 def handle_charref(self,s):self.add('&#'+s+';')
def blocks(s):
 p=TopBlocks();p.feed(s);assert p.depth==0,p.current[:1];return p.blocks

def heading(s):return bool(re.match(r'<h[23]\b',s))
def text(s):return re.sub('<[^>]+>','',s)
def columns(nodes):
 out=[];i=0
 while i<len(nodes):
  n=nodes[i]
  if heading(n):
   group=[n];i+=1
   while i<len(nodes) and heading(nodes[i]):group.append(nodes[i]);i+=1
   if i<len(nodes):group.append(nodes[i]);i+=1
   out.append('<div class="lead">'+''.join(group)+'</div>')
  else:out.append(n);i+=1
 return '<section class="cols">'+''.join(out)+'</section>' if out else ''

def flow(raw):
 nodes=blocks(raw);out=[];pending=[];i=0
 while i<len(nodes):
  n=nodes[i]
  wide=bool(re.match(r'<(?:figure|table)\b[^>]*class="[^"]*\bwide\b',n))
  # Los principios extensos se leen mejor a todo el ancho.
  wide=wide or (n.startswith('<aside class="caja"') and len(text(n))>1350)
  if not wide:pending.append(n);i+=1;continue
  intro=[]
  # Mantener el epígrafe y una introducción corta con la tabla/figura.
  for k in range(len(pending)-1,max(-1,len(pending)-4),-1):
   if heading(pending[k]) and sum(len(text(x)) for x in pending[k+1:])<650:
    intro=pending[k:];pending=pending[:k];break
  while pending and heading(pending[-1]):intro.insert(0,pending.pop())
  out.append(columns(pending));pending=[]
  n=n.replace('class="wide','class="spread')
  if n.startswith('<figure'):
   i+=1
   if i<len(nodes) and nodes[i].startswith('<blockquote'):n+=nodes[i];i+=1
   out.append('<section class="illustrated">'+''.join(intro)+n+'</section>')
  elif n.startswith('<table'):
   # Un caption pertenece a la tabla y no se separa de sus primeras filas.
   if intro:n=re.sub(r'(<table\b[^>]*>)',lambda m:m[1]+'<caption>'+''.join(intro)+'</caption>',n,count=1)
   cls='fulltable keep-table' if n.count('<tr')<=9 or 's-cronolog-a-inmutable' in n else 'fulltable'
   out.append('<section class="'+cls+'">'+n+'</section>');i+=1
  else:out.append('<section class="lead fullbox">'+''.join(intro)+n+'</section>');i+=1
 out.append(columns(pending));return ''.join(out)

def install(B):
 def chapter(nombre,num):
  source=open(B.ROOT+'/docs/texto/'+nombre+'.md').read();ctx={};segs=B.md_blocks(source,ctx)
  res=ctx.get('resumen','');m=re.search(r'Palabras clave:\s*(.*)',res);kw=m[1] if m else '';res=re.sub(r'Palabras clave:.*','',res).strip()
  cid='cap-%d'%num;title=ctx.get('titulo','')
  op=('<section class="opener" id="%s"><div class="kicker">%s · N.º %02d</div><h1>%s</h1><div class="abstract"><b>Resumen</b><p>%s</p><p class="kw"><b>Palabras clave:</b> %s</p></div></section>')%(cid,B.esc(B.SECCION[nombre]),num,B.inline(title),B.inline(res),B.esc(kw))
  body=''.join(flow(h) if k=='flow' else h for k,h in segs)
  return cid,title,'<article class="article">'+op+body+'</article>'
 B.capitulo=chapter
 B.CSS+='''
.article { break-before:page; }
.article .opener { break-before:auto; }
.cols { column-fill:balance; column-gap:7mm; margin:0; }
.cols table { column-span:none; }
.lead { break-inside:avoid; }
.illustrated { break-inside:avoid; margin:3mm 0; }
.illustrated h2 { margin-top:3mm; }
.illustrated figure { margin-top:2mm; }
.fulltable { margin:3mm 0; }
.fulltable table { column-span:none; }
.fulltable caption { text-align:left; caption-side:top; break-inside:avoid; break-after:avoid; }
.fulltable caption p { font:9pt/1.42 'Iowan Old Style'; margin:0 0 3mm; }
.fulltable caption h2 { margin-top:3mm; }
thead { display:table-header-group; break-after:avoid; }
.keep-table { break-inside:avoid; }
tbody tr:first-child { break-before:avoid; }
.fullbox { margin:3mm 0; }
figure.spread img { width:100%; height:66mm; object-fit:cover; }
figure.spread.specimen img { height:95mm; object-fit:contain; }
.ficha header { display:block; }
.ficha header span { display:block; margin-top:1mm; white-space:normal; overflow-wrap:normal; }
figure.ret { float:none; width:100%; margin:2mm 0; }
figure.ret img { width:100%; height:42mm; object-fit:cover; object-position:center 30%; }
figure.ret figcaption { font-size:6.8pt; }
'''
