from pathlib import Path
import json,sys,math
root=Path(__file__).resolve().parents[1];j=json.loads((root/'datos/catalogo.json').read_text(encoding='utf8'));errors=[];ids=set();available=0
for c in j['layers']:
 if c['id'] in ids:errors.append('ID repetido: '+c['id'])
 ids.add(c['id'])
 if c.get('file'):
  available+=1;total=0
  for part in c.get('parts',[c['file']]):
   p=root/part
   if not p.is_file():errors.append('Falta '+part);continue
   if p.stat().st_size>95*1024**2:errors.append('Archivo demasiado grande para GitHub: '+part)
   if c.get('kind')=='raster':continue
   d=json.loads(p.read_text(encoding='utf8'))
   if d.get('type')!='FeatureCollection':errors.append('GeoJSON inválido '+part)
   for f in d.get('features',[]):
    if not f.get('geometry'):errors.append('Geometría vacía '+part)
   total+=len(d.get('features',[]))
  if c.get('kind')!='raster' and total!=c.get('count'):errors.append('Conteo incorrecto '+c['id'])
if available==0:errors.append('No hay capas descargadas')
size=sum(p.stat().st_size for p in (root/'datos').rglob('*') if p.is_file())
if size>900*1024**2:errors.append('Datos demasiado grandes para el presupuesto de GitHub Pages')
print(f'{available}/{len(ids)} capas disponibles; datos {size/1024**2:.1f} MiB')
for e in errors:print('ERROR:',e)
sys.exit(bool(errors))
