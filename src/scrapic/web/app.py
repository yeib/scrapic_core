import streamlit as st
import os
import glob
from pathlib import Path

from scrapic.core.image_scraper import MultiEngineScraper
from scrapic.core.dataset_scraper import DatasetScraper
from scrapic.core.spider import SpiderScraper
from scrapic.core.network import NetworkManager
from scrapic.core.database import DatabaseManager
from scrapic.core.utils import setup_logging

setup_logging()

import base64

logo_file = "docs/logo.webp"
st.set_page_config(page_title="Scrapic", page_icon=logo_file if os.path.exists(logo_file) else "🤖", layout="wide")

st.markdown("""
    <style>
        .stDeployButton {display:none;}
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        [data-testid="stSidebarHeader"] {display: none;}
        [data-testid="stSidebarUserContent"] {padding-top: 1rem;}
    </style>
""", unsafe_allow_html=True)

st.title("🤖 Scrapic - Ninja Harvester")
st.markdown("Herramienta multipropósito para recolección de datos masiva desde fuentes abiertas.")

def get_base64_image(image_path: str):
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def get_subdirs(base_path: str):
    if not os.path.exists(base_path):
        return []
    return sorted([d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))])

def format_size_mb(filepath: str) -> str:
    try:
        size = os.path.getsize(filepath)
        if size >= 1024 * 1024:
            return f"{size / (1024 * 1024):.2f} MB"
        return f"{size / 1024:.1f} KB"
    except OSError:
        return "N/A"

with st.sidebar:
    logo_b64 = get_base64_image(logo_file)
    if logo_b64:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.08);">
                <img src="data:image/webp;base64,{logo_b64}" width="42" height="42" style="border-radius: 8px; flex-shrink: 0;" />
                <div>
                    <h3 style="margin: 0; padding: 0; font-size: 20px; font-weight: 800; color: #00bcd4; line-height: 1.1;">Scrapic</h3>
                    <span style="font-size: 11px; color: #888; letter-spacing: 0.5px; text-transform: uppercase;">Ninja Harvester</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.header("🤖 Scrapic")
    
    modo = st.selectbox("🎯 Modo de Misión", options=["🖼️ Imágenes", "📊 Dataset Builder", "🕸️ Spider Crawler", "📂 Biblioteca & Descargas"])
    
    start_btn = False
    
    if modo == "🖼️ Imágenes":
        concepts_input = st.text_input("Conceptos (separados por coma)", placeholder="ej: Cyberpunk")
        with st.expander("🔍 Motores de búsqueda (3 activos)", expanded=False):
            use_bing = st.checkbox("Bing", value=True)
            use_baidu = st.checkbox("Baidu", value=True)
            use_yandex = st.checkbox("Yandex", value=True)
        limit = st.slider("Cantidad de imágenes por motor", min_value=1, max_value=50, value=10)
        start_btn = st.button("🚀 Iniciar Extracción", type="primary", use_container_width=True)
        
    elif modo == "📊 Dataset Builder":
        concepts_input = st.text_input("Temas de investigación", placeholder="ej: Machine Learning")
        file_ext = st.selectbox("Formato", options=[".pdf", ".csv", ".json", ".xlsx", ".md", ".mp3"])
        limit = st.slider("Archivos por concepto", min_value=1, max_value=20, value=5)
        st.subheader("Filtros Inteligentes (Anti-Basura)")
        min_size_mb = st.number_input("Tamaño mínimo (MB)", min_value=0.0, max_value=100.0, value=0.0, step=1.0)
        min_pages = 0
        max_duration_mins = 15
        if file_ext == '.pdf':
            min_pages = st.number_input("Páginas mínimas (Solo PDF)", min_value=0, max_value=1000, value=0, step=10)
        elif file_ext == '.mp3':
            max_duration_mins = st.number_input("Duración máxima en minutos (0 para sin límite)", min_value=0, max_value=600, value=15, step=1)
        start_btn = st.button("🚀 Iniciar Extracción", type="primary", use_container_width=True)
            
    elif modo == "🕸️ Spider Crawler":
        start_url = st.text_input("URL Inicial del sitio web", placeholder="https://ejemplo.com/archivos")
        target_exts = st.text_input("Extensiones a extraer (ej: .pdf, .mp3, .zip, .csv)", value=".pdf, .csv")
        max_depth = st.slider("Profundidad de navegación (Clicks)", min_value=0, max_value=5, value=2)
        limit = st.slider("Límite total de archivos a extraer", min_value=1, max_value=100, value=20)
        start_btn = st.button("🚀 Iniciar Extracción", type="primary", use_container_width=True)
    
    st.markdown(
        """
        <div style="text-align: center; margin-top: 15px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1);">
            <a href="https://yeib.cl" target="_blank" style="font-family: 'Caveat', 'Brush Script MT', 'Comic Sans MS', cursive; font-size: 20px; color: teal; text-decoration: none; font-weight: bold; letter-spacing: 1px;">
                by Yeib
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

if start_btn:
    progress_bar = st.progress(0)
    status_text = st.empty()

    if modo == "🖼️ Imágenes":
        concepts = [c.strip() for c in concepts_input.split(",") if c.strip()]
        if not concepts: st.error("Ingresa al menos un concepto.")
        else:
            if not any([use_bing, use_baidu, use_yandex]):
                st.error("Selecciona al menos un buscador.")
                st.stop()
                
            scraper = MultiEngineScraper()
            engines = []
            if use_bing: engines.append('bing')
            if use_baidu: engines.append('baidu')
            if use_yandex: engines.append('yandex')
            
            total_tasks = len(concepts) * len(engines)
            tasks_done = 0
            
            for concept in concepts:
                concept_dir = scraper.create_concept_dir(concept)
                st.subheader(f"🖼️ Imágenes para: {concept}")
                
                for engine in engines:
                    status_text.info(f"⏳ Descargando '{concept}' usando {engine}...")
                    if engine == 'bing': scraper.scrape_bing(concept, concept_dir, limit)
                    elif engine == 'baidu': scraper.scrape_baidu(concept, concept_dir, limit)
                    elif engine == 'yandex': scraper.scrape_yandex(concept, concept_dir, limit)
                    
                    tasks_done += 1
                    progress_bar.progress(tasks_done / total_tasks)
                
                images = glob.glob(os.path.join(concept_dir, "*.*"))
                if images:
                    st.success(f"✅ Se descargaron {len(images)} imágenes para '{concept}'")
                    cols = st.columns(5)
                    for i, img_path in enumerate(images[:25]): 
                        with cols[i % 5]: st.image(img_path, use_container_width=True)
                else:
                    st.warning(f"No se encontraron imágenes para '{concept}'")
                    
            status_text.success("🎉 ¡Descarga completada!")
            st.balloons()
            
    elif modo == "📊 Dataset Builder":
        concepts = [c.strip() for c in concepts_input.split(",") if c.strip()]
        if not concepts: st.error("Ingresa al menos un concepto.")
        else:
            scraper = DatasetScraper()
            total_tasks = len(concepts)
            tasks_done = 0
            
            for concept in concepts:
                concept_dir = scraper.create_concept_dir(concept, file_ext)
                st.subheader(f"📄 Archivos {file_ext} para: {concept}")
                status_text.info(f"⏳ Buscando en la web (Anti-Bot habilitado)...")
                
                if file_ext == '.mp3':
                    st.warning("🎧 Modo MP3 activado. Esto puede tardar varios minutos mientras se extrae el audio. ¡Revisa la terminal de ejecución para ver el progreso real!")
                
                count = scraper.scrape_dataset(concept, file_ext=file_ext, limit=limit, min_size_mb=min_size_mb, min_pages=min_pages, max_duration_mins=max_duration_mins)
                
                tasks_done += 1
                progress_bar.progress(tasks_done / total_tasks)
                
                docs = glob.glob(os.path.join(concept_dir, f"*{file_ext}"))
                if docs:
                    st.success(f"✅ Se obtuvieron {len(docs)} archivos para '{concept}'")
                    for doc in docs: st.markdown(f"- 📄 `{os.path.basename(doc)}`")
                else:
                    st.warning(f"No se pudo descargar nada para '{concept}'.")
                    st.info("💡 Sugerencia: Intenta bajar el tamaño mínimo (MB), usar menos páginas o probar un término más genérico.")
                    
            base_folder = "audio" if file_ext == '.mp3' else "documentos"
            status_text.success(f"🎉 ¡Misión completada! Revisa tu carpeta 'downloads/{base_folder}'.")
            st.balloons()

    elif modo == "🕸️ Spider Crawler":
        if not NetworkManager.is_safe_url(start_url):
            st.error("La URL debe ser HTTP(S) y resolver únicamente a direcciones IP públicas.")
        else:
            exts = [e.strip() if e.strip().startswith('.') else f".{e.strip()}" for e in target_exts.split(",")]
            spider = SpiderScraper()
            
            status_text.info(f"🕸️ Rastreando red recursivamente en {start_url} ...")
            
            spider.crawl_and_download(start_url, target_extensions=exts, max_depth=max_depth, max_files=limit)
            
            progress_bar.progress(1.0)
            status_text.success("🎉 ¡Spider terminó de mapear y descargar! Revisa tu carpeta 'downloads/spider'.")
            st.balloons()

# --- Vistas persistentes / Explorador de archivos guardados ---

if modo == "🖼️ Imágenes" and not start_btn:
    saved_concepts = get_subdirs("downloads/imagenes")
    if saved_concepts:
        st.markdown("---")
        st.subheader("📁 Colecciones existentes en disco")
        c1, c2 = st.columns([3, 1])
        with c1:
            sel = st.selectbox("Selecciona una colección para visualizar:", options=saved_concepts)
        
        if sel:
            folder_path = os.path.join("downloads/imagenes", sel)
            imgs = sorted(glob.glob(os.path.join(folder_path, "*.*")))
            st.info(f"📸 Mostrando {len(imgs)} imágenes en `{folder_path}`")
            if imgs:
                cols = st.columns(5)
                for i, img_path in enumerate(imgs):
                    with cols[i % 5]:
                        st.image(img_path, caption=os.path.basename(img_path), use_container_width=True)
            else:
                st.write("Esta carpeta está vacía.")
    else:
        st.info("💡 Ingresa conceptos y haz clic en 'Iniciar Extracción' para descargar tus primeras imágenes.")

elif modo == "📊 Dataset Builder" and not start_btn:
    doc_dirs = get_subdirs("downloads/documentos")
    audio_dirs = get_subdirs("downloads/audio")
    if doc_dirs or audio_dirs:
        st.markdown("---")
        st.subheader("📁 Datasets guardados en disco")
        tab_doc, tab_aud = st.tabs(["📄 Documentos", "🎧 Audio"])
        with tab_doc:
            if doc_dirs:
                sel_doc = st.selectbox("Selecciona una carpeta de documentos:", options=doc_dirs)
                if sel_doc:
                    folder = os.path.join("downloads/documentos", sel_doc)
                    files = sorted(glob.glob(os.path.join(folder, "*.*")))
                    st.info(f"Mostrando {len(files)} archivos en `{folder}`")
                    for f in files:
                        st.markdown(f"- 📄 `{os.path.basename(f)}` ({format_size_mb(f)})")
            else:
                st.write("No hay documentos guardados aún.")
        with tab_aud:
            if audio_dirs:
                sel_aud = st.selectbox("Selecciona una carpeta de audio:", options=audio_dirs)
                if sel_aud:
                    folder = os.path.join("downloads/audio", sel_aud)
                    files = sorted(glob.glob(os.path.join(folder, "*.*")))
                    st.info(f"Mostrando {len(files)} archivos en `{folder}`")
                    for f in files:
                        st.markdown(f"- 🎧 `{os.path.basename(f)}` ({format_size_mb(f)})")
            else:
                st.write("No hay audios guardados aún.")
    else:
        st.info("💡 Ingresa un tema de investigación para descargar datasets automáticamente.")

elif modo == "🕸️ Spider Crawler" and not start_btn:
    spider_dirs = get_subdirs("downloads/spider")
    if spider_dirs:
        st.markdown("---")
        st.subheader("🕸️ Sitios web rastreados en disco")
        sel_site = st.selectbox("Selecciona un sitio web:", options=spider_dirs)
        if sel_site:
            folder = os.path.join("downloads/spider", sel_site)
            files = sorted(glob.glob(os.path.join(folder, "*.*")))
            st.info(f"Mostrando {len(files)} archivos extraídos de `{folder}`")
            for f in files:
                st.markdown(f"- 📦 `{os.path.basename(f)}` ({format_size_mb(f)})")
    else:
        st.info("💡 Ingresa una URL y haz clic en 'Iniciar Extracción' para rastrear un sitio.")

elif modo == "📂 Biblioteca & Descargas":
    st.header("📂 Biblioteca y Centro de Descargas")
    st.markdown("Explora todas las colecciones, datasets, archivos y el historial registrado por Scrapic.")
    
    db = DatabaseManager()
    all_downloads = db.get_all_downloads()
    
    img_folders = get_subdirs("downloads/imagenes")
    doc_folders = get_subdirs("downloads/documentos")
    aud_folders = get_subdirs("downloads/audio")
    spider_folders = get_subdirs("downloads/spider")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Colecciones Imágenes", len(img_folders))
    m2.metric("Datasets Documentos", len(doc_folders))
    m3.metric("Sitios Spider", len(spider_folders))
    m4.metric("Registros Historial DB", len(all_downloads))
    
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "🖼️ Galería de Imágenes",
        "📄 Datasets y Documentos",
        "🕸️ Archivos Spider",
        "📜 Historial OSINT (SQLite)"
    ])
    
    with tab1:
        if img_folders:
            c1, _ = st.columns([3, 1])
            with c1:
                sel_gal = st.selectbox("Colección de imágenes:", options=img_folders, key="bib_img")
            if sel_gal:
                fpath = os.path.join("downloads/imagenes", sel_gal)
                imgs = sorted(glob.glob(os.path.join(fpath, "*.*")))
                st.caption(f"📸 {len(imgs)} imágenes en `{fpath}`")
                cols = st.columns(5)
                for i, img_path in enumerate(imgs):
                    with cols[i % 5]:
                        st.image(img_path, caption=os.path.basename(img_path), use_container_width=True)
        else:
            st.info("No hay colecciones de imágenes descargadas.")
            
    with tab2:
        all_ds_folders = [("Documentos", "downloads/documentos", d) for d in doc_folders] + [("Audio", "downloads/audio", a) for a in aud_folders]
        if all_ds_folders:
            folder_labels = [f"[{cat}] {name}" for cat, _, name in all_ds_folders]
            sel_idx = st.selectbox("Selecciona un dataset:", range(len(folder_labels)), format_func=lambda i: folder_labels[i], key="bib_ds")
            cat, base, name = all_ds_folders[sel_idx]
            target_path = os.path.join(base, name)
            files = sorted(glob.glob(os.path.join(target_path, "*.*")))
            st.caption(f"📂 Mostrando {len(files)} archivos en `{target_path}`")
            for f in files:
                st.markdown(f"- `{os.path.basename(f)}` — **{format_size_mb(f)}**")
        else:
            st.info("No hay datasets descargados.")
            
    with tab3:
        if spider_folders:
            sel_sp = st.selectbox("Dominio rastreado:", options=spider_folders, key="bib_sp")
            if sel_sp:
                target_path = os.path.join("downloads/spider", sel_sp)
                files = sorted(glob.glob(os.path.join(target_path, "*.*")))
                st.caption(f"🕸️ {len(files)} archivos extraídos en `{target_path}`")
                for f in files:
                    st.markdown(f"- 📦 `{os.path.basename(f)}` — **{format_size_mb(f)}**")
        else:
            st.info("No hay rastreos de Spider guardados.")
            
    with tab4:
        if all_downloads:
            st.markdown(f"**Total de eventos registrados en base de datos:** {len(all_downloads)}")
            st.dataframe(all_downloads, use_container_width=True)
        else:
            st.info("La base de datos SQLite aún no tiene registros de descargas.")
