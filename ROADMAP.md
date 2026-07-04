# 🗺️ Hoja de Ruta: Scrapic (Próximos Pasos)

¡El lanzamiento de la **v1.0.1** fue un éxito! Ya tenemos una base sólida, pero como todo buen framework de OSINT, siempre hay espacio para hacerlo más sigiloso, rápido y letal. 

Aquí tienes la ruta de trabajo sugerida para el futuro, dividida por áreas clave:

### 1. Motor Anti-Bot y Redes (Nivel Ninja 🥷)
- **Rotación de Proxies Dinámica:** Actualmente el soporte SOCKS5 funciona, pero podríamos agregar un modo donde Scrapic lea una lista de proxies (`proxies.txt`) y salte de IP en cada petición automáticamente.
- **Bypass Avanzado:** Integrar `cloudscraper` o `undetected-chromedriver` para evadir los molestos desafíos de Cloudflare que bloquean algunas páginas en el modo *Spider*.

### 2. Spider Crawler (El Ninja Veloz 🕷️)
- **Mapeo Concurrente:** La fase de descarga ya es multi-hilo, pero la *Fase 1 (Mapeo BFS)* es lineal. Si la hacemos asíncrona, el Spider podría escanear cientos de páginas en un par de segundos.
- **Filtros Inteligentes:** Añadir soporte para expresiones regulares (Regex). Por ejemplo, decirle a la araña: *"Baja solo los PDFs que contengan la palabra 'contrato' en el link"*.

### 3. Media Ripper & Dataset Builder 🎧📊
- **Descarga de Playlists completas:** Mejorar el módulo de YouTube/Audio para que acepte links de playlists y baje discos enteros de una vez.
- **Múltiples Motores de Búsqueda:** El dorking usa Yahoo ahora mismo. Podríamos añadir DuckDuckGo o Bing como opciones seleccionables desde la interfaz, por si Yahoo nos bloquea por exceso de consultas.

### 4. Interfaz y Experiencia (Streamlit UI 🎨)
- **Galería Integrada:** Una nueva pestaña en la aplicación web para poder previsualizar las fotos, escuchar los audios o leer los PDFs descargados sin tener que salir de la UI web.
- **Reportes OSINT:** Un botón de "Exportar Reporte". Que Scrapic genere un archivo `.csv` automático con la procedencia de cada archivo bajado (URL original, tamaño, fecha de captura), lo cual es oro puro para los analistas de datos.

### 5. Distribución Global (Nivel Maestro 🌍)
- **Publicación en PyPI (`pip install scrapic`):** Estructurar el código fuente para que se pueda empaquetar y publicar en el repositorio oficial de Python. Así, cualquier persona del mundo podrá instalar y correr Scrapic desde su terminal con un solo comando, e integraremos *GitHub Actions* para que esto suceda automáticamente en cada Release.

---
**💡 Recomendación para cuando quieras retomar:**
Podemos empezar por los **Reportes OSINT (.csv)** o la **Publicación en PyPI**, ya que son las características que más valor comercial le darían a un Framework de este estilo. ¡Guárdalo en tus notas para cuando volvamos a la carga!
