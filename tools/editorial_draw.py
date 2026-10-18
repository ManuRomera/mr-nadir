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

