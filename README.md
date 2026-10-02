# geo-oil-gas — Demison - Lande

Visor SIG independiente de hidrocarburos argentinos, estático y preparado para GitHub Pages. Las capas se consultan desde el propio proyecto; no se consulta WFS ni el catálogo nacional durante la navegación. Los cinco mapas base Argenmap son servicios remotos del IGN. Leaflet se distribuye localmente bajo licencia BSD-2-Clause.

## Abrir en Windows

1. Extraer el ZIP completo en una carpeta independiente, por ejemplo `D:\Desarrollos\Geo_capas_geograficas\Geo_Oil_Gas`.
2. Con Python instalado, ejecutar `03_VER_LOCAL.bat`. Abrir `http://localhost:8090`. Mantener la consola abierta.
3. Para publicar: instalar Git y GitHub CLI, ejecutar `gh auth login` y después `04_PUBLICAR_GITHUB.bat`. El script utiliza la cuenta autenticada, crea un repositorio público `geo-oil-gas` si no existe y activa Pages en `main`.
4. La publicación no se ha ejecutado desde este entorno: no dispone de acceso autenticado a tu GitHub.

No abrir index.html con doble clic: el navegador impide leer los GeoJSON mediante file://. No requiere base de datos ni servidor de pago.

## Organización

- **Exploración:** cuencas, permisos, sísmica 2D/3D y distribución de fluidos VM de Neuquén.
- **Producción:** padrón de pozos Capítulo IV, yacimientos, concesiones, lotes, trayectorias, venteos y capas provinciales.
- **Transporte:** ductos Res.319, ductos y nodos planillas 20/21, gasoductos ENARGAS y líneas provinciales.
- **Instalaciones:** puntos característicos, baterías, medición, plantas, refinerías, terminales, locaciones y aceite vegetal. Las capas de refinación y aceite vegetal son complementarias al upstream.

Los filtros se aplican a todas las capas activas. Limpiar los filtros al cambiar de temática si se desea volver a ver todos los elementos. Elegir un filtro requiere activar antes una capa con ese atributo. Fuente y división organizan el menú; no desactivan capas ya encendidas. El mapa dibuja hasta 20.000 elementos por capa dentro de la vista actual; acercar el mapa para consultar zonas densas. El contador distingue visibles de coincidentes. No se cuentan como activos los registros de las fuentes: se trata de elementos geométricos y pueden existir coincidencias entre Nación y provincia.

## Datos y clasificación

`datos/catalogo.json` registra fuente, archivo, cantidad, fecha de descarga, recurso y estado. Cada capa disponible tiene copias GeoJSON fragmentadas. Las ventanas de VM provienen de polígonos oficiales: se muestra distribución de fluidos, sin inferir valores de madurez térmica que la fuente no aporta. La paleta del visor es propia.

El padrón nacional usa el CSV completo para conservar `idpozo`, `tipoestado`, `tipopozo`, `tipoextraccion`, `formacion`, `clasificacion` y `subclasificacion`. El filtro «Tipo de extracción» responde al tipo de pozo (petrolífero, gasífero, etc.); el método de extracción permanece en la ficha como `tipoextraccion`. El recurso utiliza SHALE/TIGHT y, cuando no está informado, el tipo de recurso general. La producción mensual disponible y las fracturas se vinculan por idpozo; los registros sin correspondencia se contabilizan en `datos/vinculacion.json`. Los meses informados no constituyen un año completo ni garantizan cierre de declaraciones.

Las clasificaciones de puntos característicos se infieren de campos de tipo/nombre/descripción, con marca de revisión. Si aparecen términos de varias categorías, queda en Otros para revisión. No se borran atributos originales. Los medidores de Res.318/554 no se georreferencian por nombre ni proximidad: los padrones 554 se vinculan con las coordenadas de 318 mediante identificadores comprobados, según el apartado final. Neuquén aporta una capa geográfica de puntos de medición independiente. No se fusionan medidores duplicados sin validar IDs.

Algunas geometrías provinciales inválidas se excluyen y su número figura en `rejected`; deben revisarse contra el original. La copia de visualización usa simplificación de 0,00001 grados y redondeo a seis decimales, sin atribuirle precisión topográfica ni catastral. Los originales se guardan en `archivo_fuentes`, excluido de GitHub. Los SHP mantienen los límites de longitud de campos de DBF; el padrón de pozos evita esa limitación usando CSV.

## Actualizar

Ejecutar `01_INSTALAR.bat` una vez y luego `02_ACTUALIZAR.bat`. El actualizador consulta CKAN por identificadores de recurso y WFS 2.0 con paginación, transforma a WGS84 y conserva la última capa disponible si una descarga falla. Mantiene metadatos y archivo original; cuando existe una versión anterior, la conserva. No actualiza automáticamente al abrir el visor.

La producción y fracturas se vinculan con `scripts/vincular_operacion.py --produccion RUTA_CSV --fracturas RUTA_CSV`. Primero actualizar el padrón, luego vincular operación y publicar. Descargar los CSV oficiales desde las fuentes registradas en el catálogo. El padrón actualizado reemplaza sus fichas: repetir la vinculación después de cada actualización.

Se suministran `scripts/validar.py` y los controles de tamaño de archivo para GitHub. GitHub Pages publica sólo la raíz del proyecto: no cargar archivos masivos originales ni la carpeta virtual de Python. Mantener copias originales fuera de GitHub permite conservar datos aunque cambie el sitio de origen. Los geoservicios Argenmap pueden dejar de responder sin afectar la lectura de capas locales.

## Cobertura pendiente

«Agua y servicios» y «Offshore históricos» se exploran mediante los atributos originales del padrón y la búsqueda textual; no se crean inventarios separados no verificados. Los padrones nacionales 554 se vinculan con las geometrías 318. Quedan registros sin una correspondencia validada, detallados en el informe de cobertura. No se ha completado una deduplicación entre Nación y Neuquén. El visor explicita estas limitaciones en Fuentes.

Fuentes principales: https://datos.energia.gob.ar/ · https://hidrocarburos.energianeuquen.gob.ar/gis · https://www.ign.gob.ar/NuestrasActividades/InformacionGeoespacial/ServiciosOGC

## Colores editables

Cada capa tiene un color inicial diferente. En capas de gas se utilizan amarillos y naranjas, con gasoductos troncales amarillo yema y compresoras naranja más oscuro. Petróleo se representa en verdes. Las capas mixtas reconocen gas y petróleo cuando sus atributos de tipo o fluido lo permiten; los registros sin indicio conservan el color general de la capa. El selector junto a cada nombre aplica un color uniforme a esa capa. Las preferencias se guardan en el navegador y se recuperan al volver a abrir el visor. No modifican los GeoJSON ni la vista de otros usuarios.

VM Distribución de Fluidos conserva una paleta temática basada en las capturas aportadas: gas seco rojo, gas húmedo naranja, gas condensado amarillo claro, petróleo volátil verde lima y petróleo negro gris. Los tonos son aproximados porque las capturas tienen transparencia sobre el mapa base. Su botón Colores abre cinco selectores por categoría y actualiza la leyenda. Restablecer colores recupera toda la paleta inicial. Si el navegador restringe almacenamiento local, los cambios funcionan en la sesión pero no se guardan.

## Inicio y World Imagery

El visor abre en Transporte con siete capas de ductos/líneas de conducción activadas. Producción comienza completamente apagada. El mapa base inicial es Argenmap clásico, consultado en línea. No se creó ningún sitio de teselas.

World Imagery — Esri se selecciona desde Mapa base. Utiliza el servicio público clásico mediante Esri Leaflet, que gestiona la atribución de las imágenes según la vista. Necesita internet; las imágenes no se descargan ni se redistribuyen en el proyecto. La disponibilidad depende del proveedor. Esri Leaflet se distribuye bajo licencia Apache 2.0. No se usa un token ni se configura un servicio pago.

Los dos padrones nacionales de Resolución 554 están disponibles mediante vinculación validada con las geometrías de Resolución 318. Las posiciones de medidores se muestran como referencia de la instalación.

## Corrección de instalaciones y medidores Res.318 / 554

La fuente espacial es instalaciones-hidrocarburos-instalaciones-res-318. Su tabla CKAN DataStore contiene 2.543 registros, de los que 2.540 tienen coordenadas válidas; el SHP publicado contiene 2.027 registros y no se usa en esta vinculación. La capa del padrón 554 utiliza sus atributos administrativos y se une por idinstalacion exacto y único con las coordenadas de 318: 2.369 instalaciones ubicadas y 155 pendientes. No se afirma que los inventarios sean idénticos en cobertura.

Los 3.222 medidores del padrón 554 se vinculan a instalaciones por empresa, provincia e idinstalacion_empresa, exigiendo clave única y corroborando nombre_instalacion. Se ubican 2.961 medidores en 1.809 instalaciones; quedan 261 sin un vínculo validado. La geometría es una referencia de la instalación, no una coordenada individual del medidor. Los medidores de una instalación se agrupan en una sola ficha con su listado, para evitar puntos superpuestos que impidan consultar los registros.

Las cifras anteriores sustituyen el estado pendiente indicado en versiones anteriores. Ambas capas están disponibles en Instalaciones. scripts/vincular_318_554.py utiliza únicamente la biblioteca estándar de Python y actualiza ambos padrones mediante la API pública, evitando las redirecciones del CSV descargable. 02_ACTUALIZAR.bat lo ejecuta después de actualizar las demás capas. El informe de cobertura está en datos/vinculacion_318_554.json.


## Transparencia y publicación final

Cada capa temática y cada mapa base tiene un deslizador de **Transparencia**: 0 % conserva la apariencia original y 100 % oculta visualmente la capa. Los rellenos mantienen su relación de intensidad con los contornos. Se aplica al instante, sin volver a descargar los datos. Los valores se guardan por capa y por mapa base en el navegador. Los colores y filtros siguen funcionando de forma independiente.

Para publicar en Windows:

1. Extraer el ZIP completo en una carpeta, sin trabajar dentro del archivo comprimido.
2. Instalar Python, Git (https://git-scm.com/download/win) y GitHub CLI (https://cli.github.com/). Si Git o GitHub CLI se acaban de instalar, cerrar y abrir la terminal.
3. Ejecutar `00_PREPARAR_GITHUB.bat` y completar el inicio de sesión en el navegador. No crea todavía el repositorio.
4. Revisar el visor con `03_VER_LOCAL.bat`.
5. Ejecutar `04_PUBLICAR_GITHUB.bat`. Valida los datos, crea un repositorio público llamado `geo-oil-gas` en la cuenta autenticada si no existe, envía los archivos y configura GitHub Pages desde `main` y la raíz. Muestra la dirección del sitio. La publicación puede demorar unos minutos.
6. Para enviar cambios posteriores, ejecutar `05_ACTUALIZAR_GITHUB.bat`. Para renovar datos oficiales antes de publicar, ejecutar `01_INSTALAR.bat` (una vez) y `02_ACTUALIZAR.bat`.

El paquete ya incluye los datos locales: no es necesario descargarlos de nuevo para la primera publicación. La publicación se detiene ante errores de validación, una rama diferente de `main`, un remoto de otra cuenta/repositorio o un conflicto al enviar cambios; no fuerza ni reemplaza la historia remota. Las fuentes originales y el entorno Python quedan excluidos del repositorio.
