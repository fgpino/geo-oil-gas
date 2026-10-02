'use strict';
const $=id=>document.getElementById(id),esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const vmDefaults={'GAS SECO':'#ff4144','GAS HÚMEDO':'#f7bf45','GAS CONDENSADO':'#f5f397','PETRÓLEO VOLATIL':'#b0e044','PETRÓLEO NEGRO':'#a1a1a1'};
const colorStorageKey='geo-oil-gas.colors.v1';
let colorPreferences={layers:{},vm:{}};
const validColor=v=>typeof v==='string'&&/^#[0-9a-f]{6}$/i.test(v);
try{const saved=JSON.parse(localStorage.getItem(colorStorageKey)||'{}');for(const group of ['layers','vm']){for(const[key,value]of Object.entries(saved[group]||{})){if(validColor(value))colorPreferences[group][key]=value}}}catch(e){}
let vmColors={...vmDefaults,...colorPreferences.vm};
const layerColor=c=>colorPreferences.layers[c.id]||c.color;
function featureColor(f,c){
 if(c.id==='nqn-vm_distribucion_fluidos')return vmColors[f.properties.Nombre]||layerColor(c);
 if(colorPreferences.layers[c.id])return colorPreferences.layers[c.id];
 if(c.mixedFluidColors){const p=f.properties||{};const value=Object.entries(p).filter(([k])=>/^(tipo|tipo_ducto|tipopozo|tipo_pozo|fluido|tipo_inst|tipo_instalacion)$/i.test(k)).map(([,v])=>String(v)).join(' ').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toUpperCase();const gas=/GAS|GASODUCT|COMPRESOR/.test(value),oil=/PETROL|OLEODUCT/.test(value);if(gas&&!oil)return c.gasColor;if(oil&&!gas)return c.oilColor;}
 return layerColor(c);
}
function saveColors(){try{localStorage.setItem(colorStorageKey,JSON.stringify(colorPreferences))}catch(e){$('status').textContent='Color aplicado. El navegador no permite guardar preferencias.'}}
function applyColors(c){const layer=drawn.get(c.id);if(layer?.setStyle)layer.setStyle(f=>({color:featureColor(f,c),fillColor:featureColor(f,c)}));}
const transparencyKey='geo-oil-gas.transparency.v1';
let transparency={layers:{},bases:{}};
try{const saved=JSON.parse(localStorage.getItem(transparencyKey)||'{}');for(const group of ['layers','bases'])for(const [key,value] of Object.entries(saved[group]||{}))if(Number.isFinite(value)&&value>=0&&value<=100)transparency[group][key]=value}catch(e){}
const alpha=(group,id)=>1-(transparency[group][id]||0)/100;
function saveTransparency(){try{localStorage.setItem(transparencyKey,JSON.stringify(transparency))}catch(e){$('status').textContent='Transparencia aplicada. El navegador no permite guardar preferencias.'}}
function vectorStyle(f,c){const a=alpha('layers',c.id);const point=/Point$/.test(f.geometry?.type||'');return {color:featureColor(f,c),fillColor:featureColor(f,c),opacity:a,fillOpacity:(point?.8:c.id==='nqn-vm_distribucion_fluidos'?.4:.12)*a,weight:point?1:2}}
function applyTransparency(c){const l=drawn.get(c.id);if(c.kind==='raster')l?.setOpacity?.(.6*alpha('layers',c.id));else l?.setStyle?.(f=>vectorStyle(f,c))}
function transparencyControl(group,id,name,onChange){const label=document.createElement('label');label.className='transparency-control';const caption=document.createElement('span');const input=document.createElement('input');input.type='range';input.min='0';input.max='100';input.step='1';input.value=transparency[group][id]||0;input.setAttribute('aria-label','Transparencia de '+name);const update=()=>caption.textContent='Transparencia: '+input.value+' %';update();input.oninput=()=>{transparency[group][id]=Number(input.value);update();saveTransparency();onChange()};label.append(caption,input);return label}
function renderBaseTransparency(){const id=$('base').value;$('base-transparency').replaceChildren(transparencyControl('bases',id,$('base').selectedOptions[0].textContent,()=>base.setOpacity(alpha('bases',id))))}
function renderLegend(){
 $('legend').replaceChildren();if($('division').value!=='Exploración'&&!active.has('nqn-vm_distribucion_fluidos'))return;
 const heading=document.createElement('h2');heading.textContent='VM · Distribución de fluidos';$('legend').append(heading);
 const note=document.createElement('p');note.className='note';note.textContent='Paleta de referencia de Neuquén. Podés editar cada categoría.';$('legend').append(note);
 for(const[key,color]of Object.entries(vmColors)){
  const row=document.createElement('label');row.className='vm-color-row';const text=document.createElement('span');text.textContent=key;
  const input=document.createElement('input');input.type='color';input.value=color;input.setAttribute('aria-label','Color VM: '+key);
  input.oninput=()=>{vmColors[key]=input.value;colorPreferences.vm[key]=input.value;saveColors();const c=catalog.find(c=>c.id==='nqn-vm_distribucion_fluidos');if(c)applyColors(c)};
  row.append(text,input);$('legend').append(row);
 }
}

const map=L.map('map',{preferCanvas:true}).setView([-39,-65],4),canvas=L.canvas({padding:.3});L.control.scale({imperial:false}).addTo(map);
let base, catalog=[], cache=new Map(),active=new Set(), drawn=new Map(),generation=0;
const filterKeys=['recurso','estado','extraccion','formacion','subclasificacion','categoria_instalacion'];const labels={recurso:'Recurso',estado:'Estado',extraccion:'Tipo de extracción',formacion:'Formación',subclasificacion:'Subclasificación',categoria_instalacion:'Instalación'};
for(const k of filterKeys){const l=document.createElement('label');l.textContent=labels[k];const s=document.createElement('select');s.id='f_'+k;s.innerHTML='<option value="">Todos</option>';s.onchange=redraw;l.append(s);$('filters').append(l)}
function setBase(){
 if(base)map.removeLayer(base);
 const value=$('base').value;
 if(value==='osm'){
  base=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'}).addTo(map);
 }else if(value==='esri-imagery'){
  base=L.esri.basemapLayer('Imagery',{maxZoom:23}).addTo(map);
 }else{
  base=L.tileLayer('https://wms.ign.gob.ar/geoserver/gwc/service/tms/1.0.0/'+value+'@EPSG%3A3857@png/{z}/{x}/{y}.png',{tms:true,maxZoom:18,attribution:'© Instituto Geográfico Nacional · Argenmap'}).addTo(map);
 }
 base.setOpacity(alpha('bases',value));renderBaseTransparency();
 const currentBase=base,baseName=$('base').selectedOptions[0].textContent;
 $('base-status').textContent='';
 currentBase.on('tileerror',()=>{if(base!==currentBase)return;$('base-status').textContent='No se pudo cargar una tesela de '+baseName+'. Probá otro mapa base.'});
}setBase();$('base').onchange=setBase;
$('country').onclick=()=>map.setView([-39,-65],4);$('neuquen').onclick=()=>map.fitBounds([[-41.1,-71.9],[-36.1,-68]]);$('menu').onclick=()=>$('panel').classList.toggle('hidden');if(innerWidth<800)$('panel').classList.add('hidden');
map.on('moveend',()=>{if(catalog.length)redraw()});
function list(){const items=catalog.filter(c=>c.division===$('division').value&&(!$('source').value||c.source===$('source').value));$('layers').replaceChildren();for(const c of items){const row=document.createElement('div');row.className='layer';const check=document.createElement('input');check.type='checkbox';check.id='c_'+c.id;check.checked=active.has(c.id);check.disabled=!c.file;check.onchange=async()=>{check.checked?active.add(c.id):active.delete(c.id);await redraw()};const label=document.createElement('label');label.htmlFor=check.id;label.innerHTML=`<span class="dot" style="background:${esc(layerColor(c))}"></span>${esc(c.name)}<small>${esc(c.source)} · ${c.file?Number(c.count).toLocaleString('es-AR')+' elementos':esc(c.status||'Pendiente')}</small>`;if(!c.file&&c.error){const reason=document.createElement('small');reason.className='layer-reason';reason.textContent=c.error;label.append(reason)}row.append(check,label);
if(c.id!=='nqn-vm_distribucion_fluidos'){
 const input=document.createElement('input');input.type='color';input.className='layer-color';input.value=layerColor(c);input.title='Cambiar color de '+c.name;input.setAttribute('aria-label',input.title);
 input.oninput=()=>{colorPreferences.layers[c.id]=input.value;saveColors();label.querySelector('.dot').style.background=input.value;const hint=label.querySelector('.fluid-color-hint');if(hint)hint.textContent='Color uniforme personalizado';applyColors(c)};
 row.append(input);if(c.mixedFluidColors&&!colorPreferences.layers[c.id]){const hint=document.createElement('small');hint.className='fluid-color-hint';hint.textContent='Gas amarillo · petróleo verde';label.append(hint)}
}else{const b=document.createElement('button');b.textContent='Colores';b.onclick=()=>{renderLegend();$('legend').scrollIntoView({block:'nearest'})};row.append(b)}
if(c.file){const b=document.createElement('button');b.textContent='Ver';b.onclick=async()=>{active.add(c.id);check.checked=true;await redraw();const d=drawn.get(c.id);if(d&&d.getBounds().isValid())map.fitBounds(d.getBounds(),{maxZoom:13})};row.append(b)}row.append(transparencyControl('layers',c.id,c.name,()=>applyTransparency(c)));$('layers').append(row)}if(!items.length)$('layers').textContent='No hay capas en esta selección.'}
async function load(c){if(cache.has(c.id))return cache.get(c.id);if(c.kind==='raster')return {};const pages=await Promise.all((c.parts||[c.file]).map(async path=>{const r=await fetch(path);if(!r.ok)throw Error('No se pudo leer '+c.name);return r.json()}));const j={type:'FeatureCollection',features:pages.flatMap(p=>p.features)};cache.set(c.id,j);return j}
function pass(f){const p=f.properties||{},q=$('search').value.trim().toLocaleLowerCase('es');if(q&&!Object.values(p).some(v=>String(v??'').toLocaleLowerCase('es').includes(q)))return false;for(const k of filterKeys){const v=k==='categoria_instalacion'&&$('installation-category').value?$('installation-category').value:$('f_'+k).value;if(v&&p[k]!==v)return false}return true}
function valueHTML(v){if(Array.isArray(v)&&v.length&&typeof v[0]==='object'){const keys=[...new Set(v.flatMap(x=>Object.keys(x)))];return '<table><tr>'+keys.map(k=>'<th>'+esc(k)+'</th>').join('')+'</tr>'+v.map(x=>'<tr>'+keys.map(k=>'<td>'+esc(x[k])+'</td>').join('')+'</tr>').join('')+'</table>'}return esc(typeof v==='object'?JSON.stringify(v):v)}
function popup(f,c){const p=f.properties||{},name=p.nombre||p.sigla||p.pozo||p.NOMBRE||p.Nombre||p.NPC||p.NOMBRE_DE_||p.AREAYACIMI||c.name;return `<h3>${esc(name)}</h3><p>${esc(c.source)} · Copia ${esc(c.downloaded?.slice(0,10)||'')}</p><table>${Object.entries(p).filter(([,v])=>v!=null&&v!=='').map(([k,v])=>`<tr><td>${esc(k)}</td><td>${valueHTML(v)}</td></tr>`).join('')}</table>`}
async function redraw(){const token=++generation;$('status').textContent='Cargando capas locales…';let total=0,rendered=0;const errors=[];const selected=catalog.filter(c=>active.has(c.id)&&c.file);const all=await Promise.all(selected.map(async c=>{try{return [c,await load(c)]}catch(e){errors.push(e.message);return[c,null]}}));if(token!==generation)return;for(const l of drawn.values())map.removeLayer(l);drawn.clear();for(const[c,data]of all){if(!data)continue;if(c.kind==='raster'){const l=L.imageOverlay(c.file,c.bounds,{opacity:.6*alpha('layers',c.id)}).addTo(map);drawn.set(c.id,l);continue}const matched=data.features.filter(pass);total+=matched.length;const bounds=map.getBounds();const filtered=matched.filter(f=>{if(!f._box){const coords=[];const visit=x=>{if(typeof x[0]==='number'){coords.push(x);return}for(const y of x)visit(y)};visit(f.geometry.coordinates);f._box=[Infinity,Infinity,-Infinity,-Infinity];for(const x of coords){f._box[0]=Math.min(f._box[0],x[0]);f._box[1]=Math.min(f._box[1],x[1]);f._box[2]=Math.max(f._box[2],x[0]);f._box[3]=Math.max(f._box[3],x[1])}}const b=f._box;return b[2]>=bounds.getWest()&&b[0]<=bounds.getEast()&&b[3]>=bounds.getSouth()&&b[1]<=bounds.getNorth()});const shown=filtered.slice(0,20000);rendered+=shown.length;const l=L.geoJSON({...data,features:shown},{renderer:canvas,style:f=>vectorStyle(f,c),pointToLayer:(f,ll)=>L.circleMarker(ll,{renderer:canvas,radius:4,...vectorStyle(f,c)}),onEachFeature:(f,l)=>l.bindPopup(()=>popup(f,c))}).addTo(map);drawn.set(c.id,l)}$('status').textContent=errors.length?errors.join(' · '):`${rendered.toLocaleString('es-AR')} visibles / ${total.toLocaleString('es-AR')} coincidentes · ${selected.length} capas${selected.some(c=>(cache.get(c.id)?.features?.length||0)>20000)?' · Máximo 20.000 por capa: acercá el mapa':''}`;for(const k of filterKeys){const s=$('f_'+k),v=s.value;const vals=new Set();for(const[,d]of all)if(d?.features)for(const f of d.features)if(f.properties?.[k])vals.add(f.properties[k]);s.innerHTML='<option value="">Todos</option>'+[...vals].sort().map(x=>`<option value="${esc(x)}">${esc(x)}</option>`).join('');if(vals.has(v))s.value=v}list();renderLegend()}
$('installation-category').onchange=()=>{$('f_categoria_instalacion').value=$('installation-category').value;redraw()};$('division').onchange=()=>{$('installation-group').hidden=$('division').value!=='Instalaciones';list();renderLegend()};$('source').onchange=list;let timer;$('search').oninput=()=>{clearTimeout(timer);timer=setTimeout(redraw,300)};$('reset').onclick=()=>{$('search').value='';$('installation-category').value='';for(const k of filterKeys)$('f_'+k).value='';redraw()};$('reset-colors').onclick=()=>{colorPreferences={layers:{},vm:{}};vmColors={...vmDefaults};saveColors();for(const c of catalog)applyColors(c);list();renderLegend()};$('sources').onclick=()=>$('dialog').showModal();$('close').onclick=()=>$('dialog').close();
fetch('datos/catalogo.json').then(r=>{if(!r.ok)throw Error('Catálogo no disponible');return r.json()}).then(async j=>{catalog=j.layers;$('sourcelist').innerHTML=catalog.map(c=>`<article><b>${esc(c.name)}</b> · ${esc(c.source)}<br>${esc(c.status)} · Descarga: ${esc(c.downloaded||'pendiente')}<br>${c.file?`<a href="${esc(c.file)}" download>Descargar copia local</a> · `:''}<a href="${esc(c.url)}" target="_blank" rel="noopener">Fuente oficial</a>${c.error?'<p>'+esc(c.error)+'</p>':''}</article>`).join('');for(const c of catalog){if(c.file&&c.division==='Transporte'&&/ductos|conducción/i.test(c.name))active.add(c.id);}list();await redraw()}).catch(e=>$('status').textContent=e.message);
