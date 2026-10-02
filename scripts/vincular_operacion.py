"""Vincula producción y fracturas por idpozo. Conserva períodos y atributos de fuente."""
from pathlib import Path
import json,datetime,argparse
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--produccion',required=True);parser.add_argument('--fracturas',required=True);args=parser.parse_args()
 prod=pd.read_csv(args.produccion,dtype={'idpozo':str},low_memory=False);fract=pd.read_csv(args.fracturas,dtype={'idpozo':str},low_memory=False)
 fields=['prod_pet','prod_gas','prod_agua','iny_agua','iny_gas'];group=prod.groupby(['idpozo','anio','mes'],dropna=False)[fields].sum(min_count=1).reset_index();series={}
 for idpozo,df in group.groupby('idpozo'):
  series[idpozo]=json.loads(df.drop(columns=['idpozo']).sort_values(['anio','mes']).to_json(orient='records'))
 fractures={idpozo:json.loads(df.to_json(orient='records')) for idpozo,df in fract.groupby('idpozo')}
 catpath=ROOT/'datos/catalogo.json';cat=json.loads(catpath.read_text());c=next(c for c in cat['layers'] if c['id']=='pozos');matched=0;fm=0
 for part in c['parts']:
  p=ROOT/part;j=json.loads(p.read_text())
  for f in j['features']:
   props=f['properties'];key=str(props.get('idpozo',''))
   if key in series:props['produccion_mensual']=series[key];matched+=1
   if key in fractures:props['fracturas']=fractures[key];fm+=1
  p.write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')))
 c['operation_updated']=datetime.datetime.now(datetime.timezone.utc).isoformat();catpath.write_text(json.dumps(cat,ensure_ascii=False,indent=2))
 report={'pozos_con_produccion':matched,'pozos_con_fracturas':fm,'ids_produccion_sin_padron':len(set(series))-matched,'ids_fracturas_sin_padron':len(set(fractures))-fm,'unidades':'Campos prod_pet/prod_gas/prod_agua según diccionario Capítulo IV; no se convierten unidades','periodos':sorted(set(str(int(a))+'-'+str(int(m)).zfill(2) for a,m in zip(group.anio,group.mes)))}
 (ROOT/'datos/vinculacion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(report)
if __name__=='__main__':main()
