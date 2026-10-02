"""Descarga, preserva y convierte fuentes oficiales. Nunca elimina la última copia válida."""
from pathlib import Path
import argparse, json, re, unicodedata, hashlib, datetime, concurrent.futures, shutil, tempfile, xml.etree.ElementTree as ET
import requests, geopandas as gpd, pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def norm(s):return ''.join(c for c in unicodedata.normalize('NFD',str(s).lower()) if unicodedata.category(c)!='Mn')
def fetch(url,path):
 r=requests.get(url.replace('http://datos.','https://datos.'),timeout=(20,180));r.raise_for_status();path.write_bytes(r.content);return r

def classify(p):
 n={norm(k):v for k,v in p.items()}
 def pick(*keys):
  for k in keys:
   if k in n and n[k] not in (None,''):return str(n[k])
  return ''
 p['estado']=pick('tipoestado','estado','estado_pozo','estadopozo','situacion','estado_del_pozo')
 p['extraccion']=pick('tipopozo','tipoextraccion','tipo_extraccion','tipo_pozo','tipo_de_pozo','tipo')
 p['formacion']=pick('formacion','formacion_productiva','formacionproductiva')
 p['subclasificacion']=pick('subclasificacion','subclasificacion_pozo','clasificacion','clasificaci')
 p['recurso']=pick('sub_tipo_recurso','subtiporecurso','subtipo','tipo_recurso','tiporecurso')
 if norm(p['recurso']) in ['no informado','']:
  p['recurso']=pick('tipo_recurso','tiporecurso')
 text=norm(' '.join(str(n.get(k,'')) for k in ['tipo','tipo_instalacion','tipoinstal','tipo_inst','descpc','tipo_plant','planta','descripcion','nombre','denominacion','instalacion']))
 matches=[]
 for category,pattern in [('Baterías',r'bateria'),('Medición',r'medici|medidor|fiscaliz'),('Plantas',r'planta|refineri|compresor')]:
  if re.search(pattern,text):matches.append(category)
 p['categoria_instalacion']=matches[0] if len(matches)==1 else 'Otros puntos característicos'
 p['clasificacion_revision']='Inferida por texto' if len(matches)==1 else 'Revisar: ambiguo o sin indicio'
 return p

def csvgeo(path):
 df=pd.read_csv(path,sep=None,engine='python',encoding='utf-8-sig',dtype=str);cols={norm(k):k for k in df.columns}
 if 'geojson' in cols:
  geom=df[cols['geojson']].map(lambda v: __import__('shapely.geometry',fromlist=['shape']).shape(json.loads(v)) if pd.notna(v) else None)
  return gpd.GeoDataFrame(df.drop(columns=[cols['geojson']]+([cols['geom']] if 'geom' in cols else [])),geometry=geom,crs=4326)
 lon=next((cols[k] for k in ['longitud','longitude','lon','long','x'] if k in cols),None);lat=next((cols[k] for k in ['latitud','latitude','lat','y'] if k in cols),None)
 if not lon or not lat:raise ValueError('Tabla sin coordenadas reconocidas; conservada como tabla, requiere vinculación por ID')
 x=pd.to_numeric(df[lon].str.replace(',','.'),errors='coerce');y=pd.to_numeric(df[lat].str.replace(',','.'),errors='coerce');ok=x.between(-180,180)&y.between(-90,90)&~((x==0)&(y==0));df=df[ok]
 return gpd.GeoDataFrame(df,geometry=gpd.points_from_xy(x[ok],y[ok]),crs=4326)

def download_layer(c):
 original=dict(c);raw=ROOT/'archivo_fuentes'/c['id'];raw.mkdir(parents=True,exist_ok=True)
 try:
  url=c['url'];fmt=c.get('format','')
  if c.get('dataset'):
   j=requests.get('https://datos.energia.gob.ar/api/3/action/package_show',params={'id':c['dataset']},timeout=90).json()
   if not j.get('success'):raise ValueError('Dataset no disponible')
   (raw/'metadatos.json').write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf8')
   resources=j['result']['resources'];r=next((r for r in resources if r['id']==c.get('resource_id')),None)
   if r is None:raise ValueError('Recurso no encontrado; revisar catálogo')
   url=r['url'];fmt=r['format'];c['license']=j['result'].get('license_title');c['source_modified']=j['result'].get('metadata_modified')
  ext={'SHP':'.zip','CSV':'.csv','GEOJSON':'.geojson'}.get(fmt,'.bin');temp=raw/('descarga_nueva'+ext)
  if c.get('wfs'):
   features=[];start=0;seen=set()
   while True:
    r=requests.get(c['wfs'],params={'service':'WFS','version':'2.0.0','request':'GetFeature','typeNames':c['typeName'],'outputFormat':'application/json','srsName':'EPSG:4326','count':5000,'startIndex':start},timeout=180);r.raise_for_status();page=r.json();fs=page.get('features')
    if fs is None:raise ValueError('WFS no devolvió FeatureCollection')
    if not fs:break
    signature=hashlib.sha256(json.dumps(fs,sort_keys=True).encode()).hexdigest()
    if signature in seen:raise ValueError('WFS repite página; descarga incompleta')
    seen.add(signature);features.extend(fs);start+=len(fs)
    if len(fs)<5000:break
   temp.write_text(json.dumps({'type':'FeatureCollection','features':features}),encoding='utf8');g=gpd.read_file(temp)
  elif c.get('kind')=='raster':
   fetch(url,temp);dest=ROOT/'datos'/c['id'];dest.mkdir(exist_ok=True);out=dest/'imagen.png';temp.replace(out);c.update(file=str(out.relative_to(ROOT)),status='Disponible',count=1,downloaded=datetime.datetime.now(datetime.timezone.utc).isoformat());return c
  else:
   fetch(url,temp)
   g=csvgeo(temp) if fmt=='CSV' else gpd.read_file('zip://'+str(temp) if fmt=='SHP' else temp)
  if g.crs is None:raise ValueError('CRS ausente; se requiere verificación manual')
  g=g.to_crs(4326);g=g.drop(columns=[k for k in g.columns if norm(k) in ['geojson','geom']],errors='ignore');g.geometry=g.geometry.simplify(0.00001,preserve_topology=True);valid=g.geometry.notna()&~g.geometry.is_empty&g.geometry.is_valid;rejected=int((~valid).sum());g=g[valid]
  if len(g)==0:raise ValueError('No contiene geometrías válidas')
  for col in g.columns:
   if col!=g.geometry.name and str(g[col].dtype).startswith('datetime'):g[col]=g[col].astype(str)
  j=json.loads(g.to_json(drop_id=False,na='null'));features=j['features']
  for f in features:
   p=f['properties'];p['fuente']=c['source']
   if c.get('well') or c['division']=='Instalaciones':classify(p)
   if c.get('category'):
    p['categoria_instalacion']=c['category'];p['clasificacion_revision']='Categoría de la capa oficial'
  dest=ROOT/'datos'/c['id'];dest.mkdir(exist_ok=True);parts=[]
  for i in range(0,len(features),5000):
   name=f'parte_{i//5000:03d}.geojson';p=dest/name;p.write_text(json.dumps({'type':'FeatureCollection','features':features[i:i+5000]},ensure_ascii=False,separators=(',',':')),encoding='utf8');parts.append(str(p.relative_to(ROOT)))
  old=raw/('original'+ext)
  if old.exists():shutil.copy2(old,raw/('anterior'+ext))
  temp.replace(old);c.update(parts=parts,file=parts[0],count=len(features),rejected=rejected,sha256=hashlib.sha256(old.read_bytes()).hexdigest(),status='Disponible',downloaded=datetime.datetime.now(datetime.timezone.utc).isoformat(),resource_url=url);c.pop('error',None)
 except Exception as e:
  c=original;c['error']=str(e);c['status']='Copia anterior conservada' if c.get('file') else 'Pendiente: descarga o vinculación';print(c['id'],str(e),flush=True)
 return c

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--solo',help='IDs separados por coma');args=parser.parse_args();path=ROOT/'datos/catalogo.json';j=json.loads(path.read_text(encoding='utf8'));selected=[c for c in j['layers'] if (not args.solo or c['id'] in args.solo.split(',')) and not c.get('manual')]
 results={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
  for c in ex.map(download_layer,selected):results[c['id']]=c;print(c['id'],c['status'],c.get('count',0),flush=True)
 j['layers']=[results.get(c['id'],c) for c in j['layers']];j['updated']=datetime.datetime.now(datetime.timezone.utc).isoformat();tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf8');tmp.replace(path)
if __name__=='__main__':main()
