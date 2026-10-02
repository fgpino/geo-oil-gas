"""Vinculación oficial por IDs: Res.318 (geometrías) y padrones Res.554."""
from pathlib import Path
from collections import defaultdict,Counter
import urllib.request,json,math,datetime,hashlib,concurrent.futures,unicodedata
ROOT=Path(__file__).resolve().parents[1]
RESOURCES={'318':'f80f01ac-1e50-49d9-974c-8b89b7de8b43','554':'7ec67ff3-d0e3-46d0-98c4-24499975b596','medidores':'f7c9b119-4320-4ab2-94ba-ca611ea695ce'}
def norm(v):return ' '.join(unicodedata.normalize('NFKC',str(v or '')).upper().split())
def records(key):
 rows=[];seen=set();expected=None
 while True:
  url='https://datos.energia.gob.ar/api/3/action/datastore_search?resource_id='+RESOURCES[key]+'&limit=5000&offset='+str(len(rows))
  j=json.load(urllib.request.urlopen(url,timeout=90))
  if not j.get('success'):raise ValueError('API no disponible para '+key)
  result=j['result'];total=int(result['total']);page=result['records']
  if expected is not None and total!=expected:raise ValueError('El padrón cambió durante la descarga')
  expected=total
  if not page:break
  signature=hashlib.sha256(json.dumps(page,sort_keys=True).encode()).hexdigest()
  if signature in seen:raise ValueError('Página repetida en '+key)
  seen.add(signature);rows.extend(page)
  if len(rows)>=total:break
 if len(rows)!=expected:raise ValueError('Descarga incompleta de '+key)
 return key,rows

def build(allrows):
 a,b,m=(allrows[k] for k in ['318','554','medidores']);idcounts=Counter(str(x.get('idinstalacion')) for x in a);geoms={}
 for x in a:
  lon,lat=x.get('lng'),x.get('lat');ident=str(x.get('idinstalacion'))
  if idcounts[ident]==1 and isinstance(lon,(int,float)) and isinstance(lat,(int,float)) and math.isfinite(lon) and math.isfinite(lat) and -180<=lon<=180 and -90<=lat<=90 and (lon!=0 or lat!=0):geoms[ident]={'type':'Point','coordinates':[lon,lat]}
 by_id=Counter(str(x.get('idinstalacion')) for x in b);by_key=defaultdict(list);features=[]
 for x in b:
  key=(norm(x.get('empresa')),norm(x.get('provincia')),norm(x.get('idinstalacion_empresa')))
  if all(key):by_key[key].append(x)
  ident=str(x.get('idinstalacion'))
  if ident not in geoms or by_id[ident]!=1:continue
  p=dict(x);p['fuente']='Secretaría de Energía';p['fuente_geometria']='Instalaciones Res.318';p['vinculacion']='idinstalacion exacto y único';p['categoria_instalacion']=category(x);p['clasificacion_revision']='Clasificada por atributos del padrón';features.append({'type':'Feature','id':ident,'geometry':geoms[ident],'properties':p})
 medgroups=defaultdict(list);unmatched=[]
 for x in m:
  key=(norm(x.get('empresa')),norm(x.get('provincia')),norm(x.get('idinstalacion_empresa')));candidates=by_key.get(key,[])
  if len(candidates)!=1:unmatched.append(x);continue
  target=candidates[0];ident=str(target.get('idinstalacion'))
  if ident not in geoms or by_id[ident]!=1 or norm(target.get('nombre_instalacion'))!=norm(x.get('nombre_instalacion')):unmatched.append(x);continue
  medgroups[ident].append(x)
 medfeatures=[]
 for ident,items in medgroups.items():
  p={k:items[0].get(k) for k in ['empresa','provincia','nombre_instalacion','idinstalacion_empresa']};p.update(idinstalacion=ident,numero_medidores=len(items),medidores=items,categoria_instalacion='Medición',fuente='Secretaría de Energía',fuente_geometria='Instalaciones Res.318',precision_espacial='Referencia de la instalación; no es la posición individual de cada medidor',vinculacion='empresa + provincia + idinstalacion_empresa únicos; nombre corroborado; idinstalacion hacia Res.318');medfeatures.append({'type':'Feature','id':ident,'geometry':geoms[ident],'properties':p})
 report={'registros_geograficos_318':len(a),'geometrias_validas_318':len(geoms),'instalaciones_padron_554':len(b),'instalaciones_554_cartografiadas':len(features),'instalaciones_554_sin_ubicacion':len(b)-len(features),'medidores_padron_554':len(m),'medidores_vinculados':sum(len(x) for x in medgroups.values()),'medidores_sin_vinculo_validado':len(unmatched),'instalaciones_con_medidores':len(medfeatures),'ids_geograficos_repetidos':sum(v>1 for v in idcounts.values())}
 return features,medfeatures,report

def category(x):
 text=norm(' '.join(str(x.get(k,'')) for k in ['tipo_instalacion','nombre_instalacion','descrip_instalacion']))
 if 'BATER' in text:return 'Baterías'
 if any(k in text for k in ['MEDIC','MEDIDOR','LACT','FISCAL']):return 'Medición'
 if any(k in text for k in ['PLANTA','PTC','COMPRESOR']):return 'Plantas'
 return 'Otros puntos característicos'

def save(allrows):
 features,medfeatures,report=build(allrows);catfile=ROOT/'datos/catalogo.json';cat=json.loads(catfile.read_text(encoding='utf8'));now=datetime.datetime.now(datetime.timezone.utc).isoformat()
 for layerid,fs in [('medicion-7ec6',features),('medicion-f7c9',medfeatures)]:
  if not fs:raise ValueError('La vinculación no produjo geometrías para '+layerid)
  c=next(c for c in cat['layers'] if c['id']==layerid);dest=ROOT/'datos'/layerid;dest.mkdir(exist_ok=True);file=dest/'vinculadas.geojson';tmp=file.with_suffix('.tmp');tmp.write_text(json.dumps({'type':'FeatureCollection','features':fs},ensure_ascii=False,separators=(',',':')),encoding='utf8');tmp.replace(file)
  c.update(file=str(file.relative_to(ROOT)),parts=[str(file.relative_to(ROOT))],count=len(fs),status='Disponible: vinculación validada',downloaded=now,manual=True,refresh_script='scripts/vincular_318_554.py',geometry_source_url='https://datos.energia.gob.ar/dataset/instalaciones-hidrocarburos-instalaciones-res-318');c.pop('error',None);c.pop('category',None)
  if layerid=='medicion-7ec6':c['name']='Instalaciones empadronadas · Res.554 / geometría Res.318'
  else:c['name']='Medidores Res.554 · referencia de instalación';c['records_located']=report['medidores_vinculados']
 cat['updated']=now;tmp=catfile.with_suffix('.tmp');tmp.write_text(json.dumps(cat,ensure_ascii=False,indent=2),encoding='utf8');tmp.replace(catfile);report['downloaded']=now;(ROOT/'datos/vinculacion_318_554.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 raw=ROOT/'archivo_fuentes/res318_554';raw.mkdir(parents=True,exist_ok=True)
 for key,rows in allrows.items():(raw/(key+'.json')).write_text(json.dumps(rows,ensure_ascii=False),encoding='utf8')
 print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:allrows=dict(ex.map(records,RESOURCES))
 save(allrows)
