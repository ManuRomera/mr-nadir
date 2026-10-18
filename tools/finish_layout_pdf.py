"""Audita espacios de todas las páginas y añade figuras únicas en zonas libres.
Los mapas y las hojas para escribir conservan sus espacios funcionales.
"""
from pathlib import Path
import fitz,re,json,io,hashlib
from PIL import Image
import editorial_draw as D
import build_pdf as B
R=Path(__file__).resolve().parents[1];OUT=R.parent/'output/pdf/nadir-edicion-editorial'
PATH=OUT/'Nadir-Sangre-bajo-el-hielo-edicion-editorial.pdf'
ART=R/'docs/arte/revision'

def content(p):
 rects=[fitz.Rect(b[:4]) for b in p.get_text('blocks') if b[1]>45 and b[3]<792]
 for im in p.get_image_info():
  r=fitz.Rect(im['bbox'])&p.rect
  if max(im['width'],im['height'])>=1024 and r.width>45 and r.height>35:rects.append(r)
 return rects

def picture(p,r,file,label,caption):
 r=fitz.Rect(r);im=Image.open(ART/file);w,h=im.size;ratio=r.width/r.height
 if w/h>ratio:dw=h*ratio;im=im.crop(((w-dw)/2,0,(w+dw)/2,h))
 else:dh=w/ratio;at=(h-dh)*.46;im=im.crop((0,at,w,at+dh))
 b=io.BytesIO();im.save(b,format='JPEG',quality=93);p.insert_image(r,stream=b.getvalue())
 yy=r.y1+8;p.draw_line((r.x0,yy),(r.x1,yy),color=D.AMBER,width=.7)
 D.text(p,r.x0,yy+11,label,7,'Demi',D.TEAL)
 D.para(p,r.x0,yy+23,caption,r.width,7,color=D.GREY)

def clocks(p,y):
 D.panel(p,y,'Tres cuentas que necesitan soluciones distintas')
 yy=y+115
 for a,b in [((198,yy+27),(222,yy+27)),((373,yy+27),(397,yy+27))]:D.arrow(p,[a,b])
 D.box(p,(56,yy,198,yy+76),'P-2 · Bomba','Energía y atención; con automatismo puede trabajar sola.')
 D.box(p,(222,yy,373,yy+76),'H-4 · Inundación','La bomba contiene el nivel. V-12 corta el caudal entrante.')
 D.box(p,(397,yy,540,yy+76),'R-3 · Sello','El nivel alto amenaza la barrera inferior del refugio.')
 D.box(p,(100,y+47,500,y+99),'El aire tiene su propia cuenta','Los filtros protegen a las personas. Cerrar V-12 no repone la depuración.')
 D.para(p,60,yy+108,'Comprueba aire, agua y energía al terminar cada tarea. Estabilizar una de estas cuentas no detiene las otras.',470,9)
 D.cap(p,'Esquema 1.','Relaciones del soporte vital y el drenaje. Los valores exactos están en las tablas.')

def ledge(p,y):
 # Figura de principio, sin modificar las dimensiones o rutas del plano.
 p.draw_rect((43,y,553,744),fill=D.PAPER,color=None);D.text(p,55,y+19,'Paso alto · preparar antes de cruzar',10,'Condensed',D.TEAL)
 mid=y+65
 p.draw_line((76,mid+20),(520,mid+20),color=(.6,.62,.6),width=6)
 p.draw_line((90,mid-3),(505,mid-3),color=D.AMBER,width=1.5)
 for x in [90,505]:
  p.draw_circle((x,mid-3),4,color=D.TEAL,fill=(1,1,1));p.draw_line((x,mid+1),(x,mid+18),color=D.TEAL,width=1)
 p.draw_line((298,mid-3),(298,mid+17),color=D.TEAL,width=1)
 D.text(p,65,mid-15,'Anclaje',7);D.text(p,464,mid-15,'Anclaje',7);D.text(p,238,mid-15,'Línea asegurada',7)
 D.para(p,62,mid+45,'Asegurar la línea permite cruzar sin tirada. Los heridos necesitan ayuda y arnés; una camilla rígida no pasa.',472,8)
 D.cap(p,'Esquema 2.','Principio de aseguramiento. Los tiempos y riesgos se consultan en la ficha del paso alto.')

def valve(p,y):
 p.draw_rect((43,y,553,744),fill=D.PAPER,color=None);D.text(p,55,y+19,'V-12 · cortar la entrada, dejar drenar',10,'Condensed',D.TEAL)
 yy=y+40
 D.arrow(p,[(187,yy+30),(220,yy+30)]);D.arrow(p,[(363,yy+30),(397,yy+30)])
 D.box(p,(56,yy,187,yy+67),'Caudal entrante','El cierre gradual reduce la entrada de salmuera.')
 D.box(p,(220,yy,363,yy+67),'Tramo bajo','El agua acumulada todavía debe evacuarse.')
 D.box(p,(397,yy,540,yy+67),'H-4','El nivel desciende después del cierre.')
 D.cap(p,'Esquema 3.','La válvula permite prescindir de la bomba; los filtros de R-3 y P-2 siguen siendo necesarios.')

# Selección por el contenido real de la página, nunca por una cifra de página fija.
choices=[
 ('LOS TRES RELOJES EN UNA',None,'',clocks),
 ('LA CUADRILLA PROTAGONISTA','p110.jpg','La superficie conserva el rastro de una ruta. Los registros permiten comprobar quién llegó a recorrerla.',None),
 ('LAS FILAS','p008.jpg','Instrumentos de campo: presión, consumo y tiempo se comprueban antes de iniciar otra maniobra.',None),
 ('RELOJ A','p088.jpg','Cartucho absorbente: disponer de oxígeno no elimina el CO₂ acumulado.',None),
 ('EL CANTO DEL CASCO','p023.jpg','Interfaz húmeda: depósitos minerales y actividad biológica se confunden a primera vista.',None),
 ('La radio de Serrat','p040.jpg','Un vehículo inmovilizado y un repetidor caído consumen el mismo margen que necesita C-7.',None),
 ('EL FILTRO ABANDONADO','p017.jpg','Una fractura comunica la superficie con cavidades donde persisten salmuera y gas.',None),
 ('C-7 DESDE FUERA','p032.jpg','Instalaciones bajo el hielo: el casco industrial y el macizo forman fronteras distintas.',None),
 ('La puesta y el material','p052.jpg','La colonia conserva su puesta en el ambiente húmedo de las cavidades.',None),
 ('PASO ALTO',None,'',ledge),
 ('VÁLVULA V-12',None,'',valve),
 ('PORTILLO SUPERIOR','p047.jpg','Un acceso técnico exige herramientas, un sello estable y espacio para trabajar.',None),
 ('Milena Tey (o Inés','p082.jpg','El cuerpo y su equipo quedan incorporados al depósito que cierra la fuga.',None),
 ('CONFLICTO 6','p016.jpg','En Bastión, las decisiones del rescate llegan por radio a quienes controlan material y custodia.',None),
 ('SEMILLAS DE CAMPAÑA','p095.jpg','Después del rescate quedan registros, muestras y un informe que firmar.',None),
 ('CUANDO LOS JUGADORES HACEN','p096.jpg','El material de protección permite intentar otra ruta; su autonomía sigue corriendo.',None),
 ('VERDAD','p089.jpg','Fotografías, muestras y registros permiten contrastar lo ocurrido en C-7.',None),
 ('CIERRE DEL EXPEDIENTE','p103.jpg','Archivo de la concesión: permisos, partes y una búsqueda que solo existió sobre el papel.',None),
]
# Reservas contextualizadas para cierres de página del capítulo de sistemas.
fallback={
 'Sistemas': [('p083.jpg','El diagnóstico reúne lecturas de presión, caudal y alimentación.'),('p031.jpg','Filtrado y bombeo son tareas distintas sobre el mismo circuito.'),('p062.jpg','La espera consume autonomía: también cuenta el equipo que permanece fuera.')],
 'Artículo': [('p089.jpg','El examen de campo contrasta la estructura de los depósitos.'),('p052.jpg','El ambiente húmedo permite la reproducción y el trabajo de la colonia.')],
 'Acto III': [('p041.jpg','Un acceso profundo conecta el trabajo humano con la roca expuesta.'),('p009.jpg','El casco industrial separa los espacios habitables de las galerías dañadas.')],
 'Personas': [('p071.jpg','Barracón de turno: el recuento de personal cambia con cada evacuación.'),('p009.jpg','La circulación entre módulos depende de accesos y permisos.')],
 'Métodos': [('p071.jpg','Un espacio de trabajo puede convertirse en espera de evacuación.')],
 'Herramientas': [('p096.jpg','El inventario de trajes debe seguir a quienes los usan.'),('p071.jpg','El refugio temporal necesita aire, energía y un recuento actualizado.')],
}

doc=fitz.open(PATH);before=[p.get_text() for p in doc];used=set();used_drawers=set();records=[];section=''
for i,p in enumerate(doc):
 t=p.get_text();nt=re.sub(r'\s+',' ',t);compact=re.sub(r'\s+','',t).upper()
 for k,n in enumerate(B.ORDEN):
  if re.sub(r'\s+','',B.SECCION[n]+'·N.º%02d'%k).upper() in compact:section=B.SECCION[n]
 if i<2 or i==len(doc)-1 or p.rect.width>p.rect.height or 'Atlas ·' in t:continue
 for k,b in D.FB.items():p.insert_font(fontname=k,fontbuffer=b)
 rects=content(p);end=max((r.y1 for r in rects),default=57)
 # Dos bloques laterales pueden dejar un hueco aunque el final de página esté lleno.
 for key,file,caption in [('CÓMO LEER UNA FICHA','p041.jpg','Galería de servicio bajo el casco industrial.'),('REGLAS DE MESA','p031.jpg','Equipo de presión y filtrado.')]:
  if key not in nt.upper() or file in used:continue
  spans=sorted((max(57,r.y0),min(780,r.y1)) for r in rects if r.x0<551 and r.x1>310)
  merged=[]
  for a,b in spans:
   if merged and a<merged[-1][1]+12:merged[-1][1]=max(b,merged[-1][1])
   else:merged.append([a,b])
  for a,b in zip(merged,merged[1:]):
   if b[0]-a[1]>165:
    picture(p,(308,a[1]+12,553,b[0]-40),file,'Detalle de campo.',caption);used.add(file);records.append({'pagina':i+1,'tipo':'ilustración lateral','archivo':file});break
 if end>=630:continue
 y=end+17;selection=None
 for key,file,caption,drawer in choices:
  if key.upper() in nt.upper() and (file is None or file not in used) and drawer not in used_drawers:
   if drawer==clocks and y>420:continue
   if drawer==ledge and 744-y<140:continue
   if drawer==valve and 744-y<125:continue
   selection=(file,caption,drawer);break
 if not selection:
  for file,caption in fallback.get(section,[]):
   if file not in used:selection=(file,caption,None);break
 if not selection:continue
 file,caption,drawer=selection
 if drawer:drawer(p,y);used_drawers.add(drawer);records.append({'pagina':i+1,'tipo':'esquema','clave':drawer.__name__})
 else:
  picture(p,(43,y,553,738),file,f'Lámina de campo {len([r for r in records if r["tipo"]=="ilustración"])+1}.',caption);used.add(file);records.append({'pagina':i+1,'tipo':'ilustración','archivo':file})
# La extracción completa conserva los caracteres previos como subsecuencia.
for i,p in enumerate(doc):
 old=re.sub(r'\s+','',before[i]);new=re.sub(r'\s+','',p.get_text());it=iter(new)
 assert all(any(x==c for x in it) for c in old),f'Texto perdido en página {i+1}'
toc=[]
for k,n in enumerate(B.ORDEN):
 title=re.search(r'^# (.+)$',(R/'docs/texto'/(n+'.md')).read_text(),re.M)[1].replace('*','');needle=re.sub(r'\s+','',B.SECCION[n]+'·N.º%02d'%k).upper()
 for i,p in enumerate(doc):
  if needle in re.sub(r'\s+','',p.get_text()).upper():toc.append([1,title,i+1]);break
for i,p in enumerate(doc):
 if 'Atlas ·' in p.get_text():toc.append([1,next(s for s in p.get_text().splitlines() if s.startswith('Atlas ·')),i+1])
doc.set_toc(toc);tmp=OUT/'maquetacion-final.tmp.pdf';doc.save(tmp,garbage=4,deflate=True);doc.close();tmp.replace(PATH)
(OUT/'figuras-editoriales.json').write_text(json.dumps(records,ensure_ascii=False,indent=2));print('Huecos completados:',len(records),records)
