import streamlit as st
import os
import sys
import glob

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.core.image_scraper import MultiEngineScraper
from src.core.dataset_scraper import DatasetScraper
from src.core.spider import SpiderScraper

st.set_page_config(page_title="Scrapic", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
        .stDeployButton {display:none;}
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.title("🤖 Scrapic - Ninja Harvester")
st.markdown("Herramienta multipropósito para recolección de datos masiva desde fuentes abiertas.")

with st.sidebar:
    st.header("⚙️ Configuración")
    
    modo = st.radio("Modo de Misión", options=["🖼️ Imágenes", "📊 Dataset Builder", "🕸️ Spider Crawler"])
    
    if modo == "🖼️ Imágenes":
        concepts_input = st.text_input("Conceptos (separados por coma)", placeholder="ej: Cyberpunk")
        st.subheader("Motores de búsqueda")
        use_bing = st.checkbox("Bing", value=True)
        use_baidu = st.checkbox("Baidu", value=True)
        use_yandex = st.checkbox("Yandex", value=True)
        limit = st.slider("Cantidad de imágenes por motor", min_value=1, max_value=50, value=10)
        
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
            
    elif modo == "🕸️ Spider Crawler":
        start_url = st.text_input("URL Inicial del sitio web", placeholder="https://ejemplo.com/archivos")
        target_exts = st.text_input("Extensiones a extraer (ej: .pdf, .mp3, .zip, .csv)", value=".pdf,.csv")
        max_depth = st.slider("Profundidad de navegación (Clicks)", min_value=0, max_value=5, value=2)
        limit = st.slider("Límite total de archivos a extraer", min_value=1, max_value=100, value=20)
    
    start_btn = st.button("🚀 Iniciar Extracción", type="primary", width="stretch")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="text-align: center; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.1);">
            <a href="https://yeib.cl" target="_blank" style="font-family: 'Caveat', 'Brush Script MT', 'Comic Sans MS', cursive; font-size: 22px; color: teal; text-decoration: none; font-weight: bold; letter-spacing: 1px;">
                ✨ by Yeib ✨
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
                    for i, img_path in enumerate(images[:15]): 
                        with cols[i % 5]: st.image(img_path, width="stretch")
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
        if not start_url.startswith("http"):
            st.error("La URL debe empezar con http:// o https://")
        else:
            exts = [e.strip() if e.strip().startswith('.') else f".{e.strip()}" for e in target_exts.split(",")]
            spider = SpiderScraper()
            
            status_text.info(f"🕸️ Rastreando red recursivamente en {start_url} ...")
            
            spider.crawl_and_download(start_url, target_extensions=exts, max_depth=max_depth, max_files=limit)
            
            progress_bar.progress(1.0)
            status_text.success("🎉 ¡Spider terminó de mapear y descargar! Revisa tu carpeta 'downloads/spider'.")
            st.balloons()
