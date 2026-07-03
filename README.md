# 🤖 Scrapic

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup-4.x-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Stable-success?style=for-the-badge)

**Scrapic** no es un simple script, es un **Framework de Scraping** diseñado específicamente para la recolección masiva de datos en investigaciones de OSINT, análisis de datasets y creación de corpus para entrenar modelos de Machine Learning (ML).

A diferencia de un scraper tradicional, su arquitectura modular está diseñada para ser ultra-resiliente: evade bloqueos dinámicamente, rastrea dominios de forma recursiva (Spider) y realiza validaciones inteligentes en memoria para descartar archivos "basura" antes de guardarlos.

---

## 📸 Showcase

> 💡 Agrega capturas de pantalla a la carpeta `docs/` y descomenta las líneas de abajo para mostrarlas aquí.

<!-- ![CLI Showcase](docs/cli_showcase.png) -->
<!-- ![Web Showcase](docs/web_showcase.png) -->

---

## 🚀 Arquitectura y Features Clave

El motor de Scrapic está dividido en módulos independientes (`core`, `cli`, `web`), implementando **Separation of Concerns** y principios de diseño escalable.

- 🥷 **Motor Anti-Bot (Resiliencia de Red)**:
  - Rotación dinámica de `User-Agents` en cada petición web.
  - *Exponential Backoff*: Sistema de reintentos espaciados automáticamente si el servidor destino se protege con bloqueos `429 Too Many Requests` o `403 Forbidden`.
- 🕸️ **Spider Crawler (Rastreo Recursivo)**:
  - Algoritmo de mapeo en árbol (BFS - *Breadth-First Search*) para recorrer un dominio completo.
  - Navega automáticamente de página en página (respetando un límite de profundidad) "aspirando" y descargando todos los archivos objetivo (`.pdf`, `.zip`, etc.) de un sitio web.
- 📊 **Dataset Builder & Smart Validator**:
  - Busca datasets crudos en internet (`.csv`, `.json`, `.xlsx`, `.md`) saltando entre motores de búsqueda y dorking paginado.
  - **Filtro Inteligente**: Abre los archivos extraídos en la memoria RAM y valida su estructura interna (por ejemplo, exige que un CSV tenga un mínimo de columnas y filas reales). Destruye silenciosamente PDFs sin hojas o datasets vacíos.
- 🧹 **History Manager & Sanitizer**:
  - Control de estados: Evita descargas duplicadas guardando un registro de cada URL obtenida (`.scrapic_history.json`).
  - Sanitizador de OS: Limpia y formatea nombres de archivos obtenidos en la web, removiendo caracteres ilegales y encriptaciones de URL (ej: `%20`).

---

## 📦 Instalación

Requiere **Python 3.8 o superior**. Para extraer audio a `.mp3`, requiere tener **FFmpeg** instalado en el sistema.

```bash
# 1. Instalar FFmpeg (Requerido solo para el Media Ripper / MP3)
# Windows: winget install ffmpeg
# Mac: brew install ffmpeg
# Linux/Ubuntu: sudo apt install ffmpeg

# 2. Clonar el repositorio
git clone https://github.com/tu-usuario/scrapic_core.git
cd scrapic_core

# 3. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Linux/Mac
# venv\Scripts\activate   # En Windows

# 4. Instalar dependencias de Python
pip install -e .
```

---

## 🎮 Modos de Uso

Scrapic expone su motor a través de dos interfaces limpias: un **CLI (Command Line Interface)** de alto rendimiento y una **Web App** interactiva.

### 1. Interfaz de Consola (CLI)
Diseñado para la terminal. Muestra feedback técnico detallado y logs en tiempo real usando barras de progreso fluidas.

```bash
python src/cli/main.py
```
> El menú interactivo te permitirá iniciar Misiones: **Buscador de Imágenes**, **Dataset Builder**, o soltar la **Araña (Spider)** en un dominio.

### 2. Interfaz Gráfica (Web App)
Ideal para visualizar galerías de imágenes extraídas al instante o configurar los filtros del dataset con controles deslizables.

```bash
streamlit run src/web/app.py
```
> Abrirá automáticamente una interfaz en tu navegador web (por defecto en `http://localhost:8501`).

---

## 🛠️ Stack Tecnológico

- **Núcleo de Scraping**: `requests`, `beautifulsoup4`, `icrawler`
- **Búsqueda OSINT**: `Yahoo Search` (dorking `filetype:` paginado)
- **Media Ripper (MP3)**: `yt-dlp` + `FFmpeg`
- **Análisis y Validación de Datos**: `PyPDF2`, librerías nativas (`csv`, `json`)
- **Presentación Visual**: `rich` (CLI), `streamlit` (Web)

---

## ⚖️ Disclaimer (Aviso Legal)

Esta herramienta está desarrollada **estrictamente con fines educativos y de investigación (OSINT)**. 
- Scrapic interactúa con la web pública (Surface Web) usando técnicas estándar de scraping y dorking.
- El uso de la función **Media Ripper (yt-dlp)** y la descarga de archivos debe hacerse respetando los derechos de autor (Copyright) y los Términos de Servicio de las plataformas involucradas.
- **El autor no se hace responsable** del mal uso de esta herramienta, recolección de datos privados expuestos por error de terceros, ni de la infracción de leyes de propiedad intelectual. Úsalo bajo tu propia responsabilidad.

*Desarrollado con pasión como demostración de ingeniería de software, arquitectura limpia y automatización de redes.*
