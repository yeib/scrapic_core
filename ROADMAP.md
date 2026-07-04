# 🗺️ Hoja de Ruta: Scrapic (Próximos Pasos)

¡El lanzamiento de la **v1.1** ha sido un éxito rotundo! Implementamos reportes OSINT, araña asíncrona con regex y evasión anti-bot. 

Aquí tienes la ruta de trabajo sugerida para el futuro, apuntando a una **v2.0** que rompa todos los esquemas (ideal para coincidir con tu próximo diploma 🎓):

### 1. Renderizado de JavaScript (SPA 🌐)
- **Integración con Playwright:** Actualmente usamos `requests` y `cloudscraper`, lo cual es rapidísimo pero falla si la página está hecha en React o Angular y requiere ejecutar JavaScript para cargar los links. Sumar un "Modo Playwright" (Headless Browser) nos hará invencibles contra sitios web modernos.

### 2. Base de Datos Local y Búsqueda (SQLite 🗄️)
- **Migrar de CSV a SQL:** A medida que bajes miles de archivos, un CSV se vuelve lento de consultar. Podríamos hacer que Scrapic guarde toda la metadata y el historial en una base de datos local SQLite, permitiéndote hacer búsquedas complejas (ej: "muéstrame todos los PDFs de más de 5MB descargados ayer").

### 3. Web Dashboard Pro (Streamlit Avanzado 🎨)
- **Centro de Comando Web:** Ya tenemos una base gráfica en `src/web/`. Podríamos mejorarla para incluir gráficos en tiempo real de las descargas y la capacidad de iniciar y monitorear las misiones (Araña, Dataset, Imágenes) haciendo clics directamente desde el navegador, sin necesidad de la consola.

### 4. Tareas Programadas (Cronjobs ⏰)
- **Modo Vigía:** Añadir una función para que Scrapic se quede "durmiendo" y se despierte automáticamente (ej: todos los días a las 3 AM) para escanear un sitio y bajar solo los archivos nuevos que no estaban ayer. Automatización total.

### 5. Distribución Global (Nivel Maestro 🌍) - *[Pendiente para el próximo Diploma]*
- **Publicación en PyPI (`pip install scrapic`):** Empaquetar el proyecto y publicarlo en el repositorio oficial de Python para que cualquiera en el mundo pueda instalar tu herramienta con un solo comando. El broche de oro.

---
*Esta hoja de ruta está viva. ¡Iremos tachando y agregando cosas según los retos que nos ponga la web!*
