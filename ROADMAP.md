# 🗺️ Hoja de Ruta: Scrapic (Próximos Pasos)

¡El lanzamiento de la **v1.1** ha sido un éxito rotundo! Implementamos reportes OSINT, araña asíncrona con regex y evasión anti-bot. 

Aquí tienes la ruta de trabajo sugerida para el futuro, apuntando a una **v2.0** que rompa todos los esquemas (ideal para coincidir con tu próximo diploma 🎓):

### 1. Distribución Global (Nivel Maestro 🌍) - *[Pendiente para el próximo Diploma]*
- **Publicación en PyPI (`pip install scrapic`):** Empaquetar el proyecto y publicarlo en el repositorio oficial de Python para que cualquiera en el mundo pueda instalarlo con un solo comando.

### 2. Scraping Semántico (Integración con IA 🧠)
- **Extracción con LLMs:** En lugar de solo bajar archivos, hacer que Scrapic lea el texto de las páginas o PDFs y use la API de un modelo de lenguaje (como OpenAI o Gemini) para extraer datos estructurados (ej: resumir el dictamen o extraer nombres clave) automáticamente.

### 3. Renderizado de JavaScript (SPA 🌐)
- **Integración con Playwright:** Actualmente usamos `requests` y `cloudscraper`, lo cual es rapidísimo pero falla si la página está hecha en React o Angular y requiere ejecutar JavaScript para cargar los links. Sumar un "Modo Playwright" (Headless Browser) nos haría invencibles.

### 4. Base de Datos Local y Búsqueda (SQLite 🗄️)
- **Migrar de CSV a SQL:** A medida que bajes miles de archivos, un CSV se vuelve lento. Podríamos hacer que Scrapic guarde toda la metadata y el historial en una base de datos local SQLite, permitiéndote hacer consultas complejas (ej: "muéstrame todos los PDFs de más de 5MB descargados ayer").

### 5. Web Dashboard Pro (Streamlit Avanzado 🎨)
- **Centro de Comando Web:** Ya tenemos una base en `src/web/`. Podríamos mejorarla para incluir gráficos en tiempo real de las descargas, una galería visual integrada y la capacidad de iniciar las misiones con botones directamente desde el navegador (sin usar la consola).

### 6. Tareas Programadas (Cronjobs ⏰)
- **Modo Vigía:** Añadir una función para que Scrapic se quede "durmiendo" y se despierte automáticamente (ej: todos los días a las 3 AM) para escanear un sitio y bajar solo los archivos nuevos que no estaban ayer.

---
*Esta hoja de ruta está viva. ¡Iremos tachando y agregando cosas según los retos que nos ponga la web!*
