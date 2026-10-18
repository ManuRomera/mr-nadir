#!/usr/bin/env python3
"""Figuras editoriales únicas: esquemas funcionales y láminas sobre páginas de cierre.
Conserva el texto y los enlaces; nunca añade páginas al índice.
"""
from pathlib import Path
import fitz,re,struct,json,io,hashlib,collections
from PIL import Image,ImageFont
R=Path(__file__).resolve().parents[1]
OUT=R.parent/'output/pdf/nadir-edicion-editorial'
PATH=OUT/'Nadir-Sangre-bajo-el-hielo-edicion-editorial.pdf'
PAPER=(.984,.976,.957);TEAL=(.059,.227,.251);AMBER=(.784,.475,.11);GREY=(.424,.455,.463);INK=(.114,.133,.141)

def face(path,style):
 data=Path(path).read_bytes();n=struct.unpack_from('>I',data,8)[0]
 for i in range(n):
  if ImageFont.truetype(path,12,index=i).getname()[1]==style:break
 else:raise ValueError(style)
 off=struct.unpack_from('>I',data,12+4*i)[0];count=struct.unpack_from('>H',data,off+4)[0];records=[];payload=bytearray();base=12+16*count
 for j in range(count):
  tag,check,at,size=struct.unpack_from('>4sIII',data,off+12+16*j);records.append(struct.pack('>4sIII',tag,check,base+len(payload),size));payload.extend(data[at:at+size]);payload.extend(b'\0'*(-len(payload)%4))
 return data[off:off+12]+b''.join(records)+payload
FB={k:face('/System/Library/Fonts/'+f+'.ttc',s) for k,f,s in [('Regular','Avenir Next','Regular'),('Demi','Avenir Next','Demi Bold'),('Condensed','Avenir Next Condensed','Demi Bold')]}
FM={k:fitz.Font(fontbuffer=v) for k,v in FB.items()}
def text(p,x,y,s,size=9,font='Regular',color=INK):p.insert_text((x,y),s,fontsize=size,fontname=font,color=color)
def para(p,x,y,s,w,size=8,font='Regular',color=INK):
 line=''
 for word in s.split():
  new=(line+' '+word).strip()
  if line and FM[font].text_length(new,fontsize=size)>w:text(p,x,y,line,size,font,color);y+=size*1.45;line=word
  else:line=new
 if line:text(p,x,y,line,size,font,color)
def box(p,r,title,body):
 r=fitz.Rect(r);p.draw_rect(r,fill=(1,1,1),color=(.76,.81,.8),width=.6);text(p,r.x0+10,r.y0+18,title,10,'Condensed',TEAL);para(p,r.x0+10,r.y0+35,body,r.width-20,7.7)
def arrow(p,points):
 import math
 for a,b in zip(points,points[1:]):p.draw_line(a,b,color=AMBER,width=1.1)
 a,b=points[-2:];angle=math.atan2(b[1]-a[1],b[0]-a[0])
 for s in [-.45,.45]:p.draw_line(b,(b[0]-6*math.cos(angle+s),b[1]-6*math.sin(angle+s)),color=AMBER,width=1.1)
def panel(p,y,title):
 p.draw_rect((43,y,553,747),fill=PAPER,color=None);p.draw_line((43,y),(553,y),color=TEAL,width=1);text(p,56,y+25,title,12,'Condensed',TEAL)
def cap(p,prefix,s):
 p.draw_line((43,755),(553,755),color=AMBER,width=.8);text(p,43,767,prefix,7,'Demi',TEAL);para(p,43,779,s,510,7,color=GREY)
def photo(p,top,file,prefix,s):
 im=Image.open(R/'docs/arte/revision'/file);w,h=im.size;ratio=510/(740-top)
 if w/h>ratio:dw=h*ratio;im=im.crop(((w-dw)/2,0,(w+dw)/2,h))
 else:dh=w/ratio;im=im.crop((0,max(0,(h-dh)*.52),w,max(0,(h-dh)*.52)+dh))
 b=io.BytesIO();im.save(b,format='JPEG',quality=94);p.insert_image((43,top,553,740),stream=b.getvalue());cap(p,prefix,s)
def full(p,end,file,prefix,s):
 # Solo se acorta el fondo blanco del cuerpo. El flujo de texto original sigue intacto.
 xref=p.get_contents()[0];stream=p.parent.xref_stream(xref)
 pattern=rb'(1 1 1 RG 1 1 1 rg\n/G\d+ gs\n0 0 680 )964( re\nf\n)'
 height=max(0,(end+20-57)/.74996556)
 stream,count=re.subn(pattern,lambda m:m[1]+f'{height:.3f}'.encode()+m[2],stream,count=1)
 if count!=1:raise ValueError('Fondo de página inesperado')
 p.parent.update_stream(xref,stream)
 p.draw_rect((0,0,p.rect.width,end+20),fill=(1,1,1),color=None,overlay=False)
 p.draw_rect((0,745,p.rect.width,p.rect.height),fill=(1,1,1),color=None,overlay=False)
 im=Image.open(R/'docs/arte/revision'/file);w,h=im.size;ratio=p.rect.width/p.rect.height
 if w/h>ratio:dw=h*ratio;im=im.crop(((w-dw)/2,0,(w+dw)/2,h))
 else:dh=w/ratio;im=im.crop((0,(h-dh)*.5,w,(h+dh)*.5))
 b=io.BytesIO();im.save(b,format='JPEG',quality=95);p.insert_image(p.rect,stream=b.getvalue(),overlay=False);cap(p,prefix,s)

doc=fitz.open(PATH);before=[p.get_text() for p in doc];add=[]
for p in doc:
 for k,b in FB.items():p.insert_font(fontname=k,fontbuffer=b)
 t=p.get_text();body=[b for b in p.get_text('blocks') if b[1]>45 and b[3]<792];end=max([b[3] for b in body]+[0]);y=end+26
 if '§ LA CUADRILLA PROTAGONISTA' in t and end<400:
  photo(p,y,'rastro-sobre-hielo.jpg','Lámina E9.','La superficie conserva el rastro de una ruta. Los registros de Bastión permiten comprobar quién llegó a recorrerla.');add.append((p.number+1,'E9'))
 elif 'LOS TRES RELOJES EN UNA' in t and end<450:
  panel(p,y,'Tres problemas, conexiones distintas')
  yy=y+105
  arrow(p,[(198,yy+35),(222,yy+35)]);arrow(p,[(373,yy+35),(397,yy+35)])
  box(p,(56,yy,198,yy+86),'P-2 · Bomba','Energía y atención humana; con automatismo puede trabajar sola.')
  box(p,(222,yy,373,yy+86),'H-4 · Inundación','La bomba contiene el nivel. V-12 permite cortar el caudal entrante.')
  box(p,(397,yy,540,yy+86),'R-3 · Sello','La salmuera alta termina por vencer la barrera del refugio.')
  box(p,(222,y+45,540,y+97),'El aire lleva su propia cuenta','Los cartuchos protegen a las personas; el cierre de V-12 no repone filtros.')
  para(p,60,yy+116,'Un rescate puede mejorar un sistema mientras otro sigue agotándose. Comprueba aire, energía y agua al cerrar cada tarea.',470,9)
  cap(p,'Esquema E1.','Relaciones entre soporte vital, bombeo e inundación. Lectura funcional de los relojes.');add.append((p.number+1,'E1'))
 elif 'Quien prefiera no hacer cuentas' in t and end<450:
  panel(p,y,'Distribución del banco de C-0')
  yy=y+90;p.draw_line((297,y+93),(297,yy+75),color=AMBER,width=1.1);p.draw_line((132,yy+75),(464,yy+75),color=AMBER,width=1.1)
  for xx in [132,298,464]:arrow(p,[(xx,yy+75),(xx,yy+98)])
  box(p,(170,y+43,425,y+93),'Banco de emergencia','Una reserva compartida para el refugio y las maniobras.')
  for x,title,body in [(56,'C-0 habitable','Luz, ventilación y espera.'),(222,'Maniobras','V-12 y la igualación de E-1.'),(388,'Equipos','Rover, bomba o depurador.')]:box(p,(x,yy+98,x+152,yy+174),title,body)
  para(p,60,yy+200,'Cada consumo sale de la misma reserva. El equipo de rescate decide qué alimentar y cuánto tiempo puede esperar el siguiente viaje.',470,8.5)
  cap(p,'Esquema E2.','Distribución conceptual de energía. Los consumos exactos se consultan en las tablas del capítulo.');add.append((p.number+1,'E2'))
 elif '§ DISCUSIÓN' in t and end<250:
  full(p,end,'colonia-humeda.jpg','Lámina E3.','Cavidad húmeda: la colonia concentra puesta y sellado donde conserva agua y gas.');add.append((p.number+1,'E3'))
 elif 'LAVERDADDEJ-17' in re.sub(r'\s+','',t) and end<300:
  full(p,end,'casco-mineralizado.jpg','Lámina E4.','El equipo queda atrapado bajo el depósito vivo. La humedad y el gas de un cuerpo prolongan el sellado.');add.append((p.number+1,'E4'))
 elif 'La memoria del androide.' in t and 'La pareja del alguacil.' in t and end<300:
  photo(p,y,'mesa-del-informe.jpg','Lámina E5.','Después del rescate quedan muestras, registros y decisiones que alguien deberá firmar.');add.append((p.number+1,'E5'))
 elif 'Actualiza la tabla al intervenir' in t and end<350:
  panel(p,y,'Red de comunicaciones de la operación')
  a=y+60;b=y+170;c=y+285
  arrow(p,[(170,a+26),(225,a+26)]);arrow(p,[(370,a+26),(425,a+26)]);arrow(p,[(479,a+60),(479,b+30),(340,b+30)]);arrow(p,[(255,b+60),(255,c)]);arrow(p,[(340,b+30),(480,b+30),(480,c)])
  box(p,(56,a,170,a+60),'Bastión','Vidal y Oria')
  box(p,(225,a,370,a+60),'R-12','Enlace exterior')
  box(p,(425,a,540,a+60),'C-7','Radio local')
  box(p,(170,b,340,b+60),'Control C-0','Telemetría y comunicaciones')
  box(p,(170,c,340,c+58),'R-3','Mara y los demás')
  box(p,(395,c,540,c+58),'P-2','Quiroga e Ivo')
  cap(p,'Esquema E6.','R-12 enlaza con Bastión. La radio local permite trabajar entre Control, refugio y estación de bombeo.');add.append((p.number+1,'E6'))
 elif '§ CIERRE DEL EXPEDIENTE' in t and end<250:
  full(p,end,'archivo-abierto.jpg','Lámina E7.','Archivo de la concesión: permisos, partes y una búsqueda que solo dejó constancia sobre el papel.');add.append((p.number+1,'E7'))
 elif '§ VÍNCULOS DE LA CUADRILLA' in t and end<380:
  panel(p,y,'Al otro lado del hielo hay alguien conocido')
  rows=[('Gael','Mara','Un vínculo anterior al accidente'),('Vera','Nora','Muestras y cartas'),('Darío','Ivo','Trabajo compartido y una deuda'),('Elia','Milena / Inés','Una amistad en C-7'),('Limen','ACE','Registros y responsabilidad')]
  for k,(left,right,label) in enumerate(rows):
   yy=y+49+58*k;arrow(p,[(168,yy+20),(375,yy+20)]);box(p,(56,yy,168,yy+42),left,'');box(p,(375,yy,540,yy+42),right,'');text(p,181,yy+13,label,7.2,color=GREY)
  cap(p,'Esquema E8.','Contactos y lealtades que cada perfil aporta. La mesa puede reformular los vínculos antes de jugar.');add.append((p.number+1,'E8'))
# Texto previo preservado, carácter por carácter, como subsecuencia del texto final de cada página.
for i,p in enumerate(doc):
 base=re.sub(r'\s+','',before[i]);new=re.sub(r'\s+','',p.get_text());it=iter(new)
 if not all(any(x==c for x in it) for c in base):raise AssertionError(f'Texto perdido en página {i+1}')
import build_pdf as B
toc=[]
for k,n in enumerate(B.ORDEN):
 title=re.search(r'^# (.+)$',(R/'docs/texto'/(n+'.md')).read_text(),re.M)[1].replace('*','')
 needle=re.sub(r'\s+','',B.SECCION[n]+'·N.º%02d'%k).upper()
 for i,p in enumerate(doc):
  if needle in re.sub(r'\s+','',p.get_text()).upper():toc.append([1,title,i+1]);break
for i,p in enumerate(doc):
 if 'Atlas · ' in p.get_text():
  heading=next((x for x in p.get_text().splitlines() if x.startswith('Atlas · ')),None)
  if heading:toc.append([1,heading,i+1])
doc.set_toc(toc)
tmp=OUT/'edicion-final.tmp.pdf';doc.save(tmp,garbage=4,deflate=True);doc.close();tmp.replace(PATH)
record=OUT/'figuras-editoriales.json';previous=json.loads(record.read_text()) if record.exists() else [];record.write_text(json.dumps(sorted({(a,b) for a,b in previous+add}),ensure_ascii=False,indent=2));print('Figuras añadidas:',add)
