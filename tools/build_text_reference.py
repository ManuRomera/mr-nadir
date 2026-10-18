"""Firmas de los textos publicados y de la copia editorial anterior, por ID estable."""
from pathlib import Path
import subprocess,json
R=Path(__file__).resolve().parents[1]
def signature(text):
 h=0xcbf29ce484222325
 for b in text.encode():h=((h^b)*0x100000001b3)&0xffffffffffffffff
 return f'{h:016x}'
result={'revision':'2.4.0','paginas':{},'actores':{}}
for ref in ['e3b03a3','232c3ea']:
 a=json.loads(subprocess.check_output(['git','show',ref+':_data/aventura.json'],cwd=R))[0]
 for j in a['journal']:
  for p in j['pages']:
   d=result['paginas'].setdefault(p['_id'],{})
   for k,v in [('text.content',p.get('text',{}).get('content')),('name',p['name'])]:
    if isinstance(v,str):d.setdefault(k,[]).append(signature(v))
 for p in a['actors']:
  d=result['actores'].setdefault(p['_id'],{})
  for k in ['biography','description']:
   v=p.get('system',{}).get(k)
   if isinstance(v,str):d.setdefault('system.'+k,[]).append(signature(v))
for group in ['paginas','actores']:
 for d in result[group].values():
  for k,v in d.items():d[k]=sorted(set(v))
out=R/'assets/editorial/referencia-textos.json';out.parent.mkdir(exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('Referencias:',len(result['paginas']),'páginas y',len(result['actores']),'actores')
