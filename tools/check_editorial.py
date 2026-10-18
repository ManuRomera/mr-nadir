#!/usr/bin/env python3
"""Comprueba que una revisión editorial no cambia la aventura jugable.
Uso: python3 tools/check_editorial.py referencia.json [_data/aventura.json]
"""
import sys,json,re,subprocess,copy,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
a=json.loads(Path(sys.argv[1]).read_text())[0];b=json.loads(Path(sys.argv[2] if len(sys.argv)>2 else R/'_data/aventura.json').read_text())[0]
fail=[];counts={};edited=[]
def check(ok,msg):
 if not ok:fail.append(msg)
def structure(x):
 x=copy.deepcopy(x)
 for j in x['journal']:
  for p in j['pages']:
   if 'text' in p:p['text'].pop('content',None)
 for actor in x['actors']:
  for k in ['biography','description']:actor.get('system',{}).pop(k,None)
 return json.loads(json.dumps(x,ensure_ascii=False).replace("Mothership 1e","Mothership 1.2"))
check(structure(a)==structure(b),'Hay cambios fuera del contenido de diarios y biografías.')
for key in ['journal','actors','items','scenes','tables','macros','playlists','folders']:
 counts[key]=len(b[key]);check([x['_id'] for x in a[key]]==[x['_id'] for x in b[key]],f'Identificadores u orden cambiados: {key}')
for x,y in zip(a['journal'],b['journal']):
 check([(p['_id'],p['name'].replace('Mothership 1e','Mothership 1.2')) for p in x['pages']]==[(p['_id'],p['name']) for p in y['pages']],f'Páginas diferentes: {x["name"]}')
 for p,q in zip(x['pages'],y['pages']):
  old=p.get('text',{}).get('content','');new=q.get('text',{}).get('content','')
  if old!=new:edited.append([x['name'],p['name']])
  control=lambda t:re.findall(r'@(?:UUID|Nadir\w+)\[[^\]]*\]',t)
  check(control(old)==control(new),f'Botones o referencias cambiados: {x["name"]}/{p["name"]}')
for p in sorted((R/'docs/texto').glob('*.md')):
 if p.name.startswith('_'):continue
 old=subprocess.check_output(['git','show','e3b03a3:'+str(p.relative_to(R))],cwd=R,text=True).replace('Mothership 1e','Mothership 1.2');new=p.read_text()
 for label,pattern in [('secciones',r'^#{1,3} .+$'),('tablas',r'^\|.*(?:\n\|.*)*'),('fichas',r'^::: ficha .*?\n:::\s*$'),('documentos',r'^::: documento .*?\n:::\s*$')]:
  flags=re.M|(re.S if label in ['fichas','documentos'] else 0)
  check(re.findall(pattern,old,flags)==re.findall(pattern,new,flags),f'{label} cambiadas en {p.name}')
 check(len(re.findall(r'^::: \w',new,re.M))==len(re.findall(r'^:::\s*$',new,re.M)),f'Bloques abiertos: {p.name}')
# Cada texto de lectura conserva su identificador de estancia y sus tipos de bloque.
for p in (R/'docs/v2').glob('*.md'):
 old=subprocess.check_output(['git','show','e3b03a3:'+str(p.relative_to(R))],cwd=R,text=True).replace('Mothership 1e','Mothership 1.2');new=p.read_text()
 check(re.findall(r'^#{1,3} .+$',old,re.M)==re.findall(r'^#{1,3} .+$',new,re.M),f'Secciones de Foundry cambiadas: {p.name}')
 check(re.findall(r'\{\{[^}]+\}\}',old)==re.findall(r'\{\{[^}]+\}\}',new),f'Controles del guion cambiados: {p.name}')
result={'resultado':'OK' if not fail else 'ERROR','base':'e3b03a3','documentos':counts,'paginas':sum(len(x['pages']) for x in b['journal']),'paginas_con_texto_revisado':len(edited),'cambios_ajenos_al_texto':structure(a)!=structure(b),'errores':fail,'revisadas':edited}
(R/'docs/revision/compatibilidad-editorial.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='revisadas'},ensure_ascii=False,indent=2));sys.exit(bool(fail))
