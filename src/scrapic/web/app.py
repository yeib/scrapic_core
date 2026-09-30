import streamlit as st
import os
import glob
from pathlib import Path

from scrapic.core.image_scraper import MultiEngineScraper
from scrapic.core.dataset_scraper import DatasetScraper
from scrapic.core.spider import SpiderScraper
from scrapic.core.network import NetworkManager
from scrapic.core.database import DatabaseManager
from scrapic.core.i18n import t
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
        .block-container { padding-top: 1.5rem !important; }
        [data-testid="stHeaderActionElements"], .stMarkdown a.anchor-link { display: none !important; }
        [data-testid="stSidebarHeader"] {display: none;}
        [data-testid="stSidebarUserContent"] {padding-top: 1rem;}
    </style>
""", unsafe_allow_html=True)

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
        st.header("Scrapic")

    language = st.selectbox(
        t("language"),
        options=["EN", "ES"],
        format_func=lambda code: "🇺🇸 English" if code == "EN" else "🇪🇸 Español",
        key="language",
    )
    modes = {
        "images": "mode_images",
        "dataset": "mode_dataset",
        "spider": "mode_spider",
        "library": "mode_library",
    }
    
    modo = st.selectbox(
        t("mode_label", language),
        options=list(modes),
        format_func=lambda mode: t(modes[mode], language),
        key="mission_mode",
    )
    
    start_btn = False
    
    if modo == "images":
        concepts_input = st.text_input(t("concepts_label", language), placeholder=t("concepts_placeholder", language))
        with st.expander(t("search_engines", language), expanded=False):
            use_bing = st.checkbox("Bing", value=True)
            use_baidu = st.checkbox("Baidu", value=True)
            use_yandex = st.checkbox("Yandex", value=True)
        limit = st.slider(t("image_limit", language), min_value=1, max_value=50, value=10)
        start_btn = st.button(t("start_extraction", language), type="primary", use_container_width=True)
        
    elif modo == "dataset":
        concepts_input = st.text_input(t("research_topics", language), placeholder=t("research_placeholder", language))
        file_ext = st.selectbox(t("format", language), options=[".pdf", ".csv", ".json", ".xlsx", ".md", ".mp3"])
        limit = st.slider(t("files_per_concept", language), min_value=1, max_value=20, value=5)
        st.subheader(t("smart_filters", language))
        min_size_mb = st.number_input(t("minimum_size", language), min_value=0.0, max_value=100.0, value=0.0, step=1.0)
        min_pages = 0
        max_duration_mins = 15
        if file_ext == '.pdf':
            min_pages = st.number_input(t("minimum_pages", language), min_value=0, max_value=1000, value=0, step=10)
        elif file_ext == '.mp3':
            max_duration_mins = st.number_input(t("maximum_duration", language), min_value=0, max_value=600, value=15, step=1)
        start_btn = st.button(t("start_extraction", language), type="primary", use_container_width=True)
            
    elif modo == "spider":
        start_url = st.text_input(t("start_url", language), placeholder=t("start_url_placeholder", language))
        target_exts = st.text_input(t("target_extensions", language), value=".pdf, .csv")
        max_depth = st.slider(t("navigation_depth", language), min_value=0, max_value=5, value=2)
        limit = st.slider(t("total_file_limit", language), min_value=1, max_value=100, value=20)
        start_btn = st.button(t("start_extraction", language), type="primary", use_container_width=True)
    
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

header_logo_b64 = get_base64_image(logo_file)
if header_logo_b64:
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 18px; margin-bottom: 20px;">
            <img src="data:image/webp;base64,{header_logo_b64}" width="68" height="68" style="border-radius: 12px; box-shadow: 0 4px 14px rgba(0,188,212,0.25);" />
            <div>
                <h1 style="margin: 0; padding: 0; font-size: 32px; font-weight: 800; color: #00bcd4; line-height: 1.1;">Scrapic</h1>
                <p style="margin: 0; padding: 0; font-size: 15px; color: #aaa; font-weight: 500;">Ninja Harvester</p>
                <p style="margin: 3px 0 0 0; padding: 0; font-size: 13px; color: #777;">{t("page_description", language)}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.title("Scrapic")
    st.markdown("### Ninja Harvester")
    st.markdown(t("page_description", language))

if start_btn:
    progress_bar = st.progress(0)
    status_text = st.empty()

    if modo == "images":
        concepts = [c.strip() for c in concepts_input.split(",") if c.strip()]
        if not concepts: st.error(t("enter_concept", language))
        else:
            if not any([use_bing, use_baidu, use_yandex]):
                st.error(t("select_search_engine", language))
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
                st.subheader(t("images_for", language).format(concept=concept))
                
                for engine in engines:
                    status_text.info(t("downloading", language).format(concept=concept, engine=engine))
                    if engine == 'bing': scraper.scrape_bing(concept, concept_dir, limit)
                    elif engine == 'baidu': scraper.scrape_baidu(concept, concept_dir, limit)
                    elif engine == 'yandex': scraper.scrape_yandex(concept, concept_dir, limit)
                    
                    tasks_done += 1
                    progress_bar.progress(tasks_done / total_tasks)
                
                images = glob.glob(os.path.join(concept_dir, "*.*"))
                if images:
                    st.success(t("images_downloaded", language).format(count=len(images), concept=concept))
                    cols = st.columns(5)
                    for i, img_path in enumerate(images[:25]): 
                        with cols[i % 5]: st.image(img_path, use_container_width=True)
                else:
                    st.warning(t("no_images_found", language).format(concept=concept))
                    
            status_text.success(t("download_complete", language))
            st.balloons()
            
    elif modo == "dataset":
        concepts = [c.strip() for c in concepts_input.split(",") if c.strip()]
        if not concepts: st.error(t("enter_concept", language))
        else:
            scraper = DatasetScraper()
            total_tasks = len(concepts)
            tasks_done = 0
            
            for concept in concepts:
                concept_dir = scraper.create_concept_dir(concept, file_ext)
                st.subheader(t("files_for", language).format(extension=file_ext, concept=concept))
                status_text.info(t("searching_web", language))
                
                if file_ext == '.mp3':
                    st.warning(t("mp3_notice", language))
                
                count = scraper.scrape_dataset(concept, file_ext=file_ext, limit=limit, min_size_mb=min_size_mb, min_pages=min_pages, max_duration_mins=max_duration_mins)
                
                tasks_done += 1
                progress_bar.progress(tasks_done / total_tasks)
                
                docs = glob.glob(os.path.join(concept_dir, f"*{file_ext}"))
                if docs:
                    st.success(t("files_obtained", language).format(count=len(docs), concept=concept))
                    for doc in docs: st.markdown(f"- 📄 `{os.path.basename(doc)}`")
                else:
                    st.warning(t("nothing_downloaded", language).format(concept=concept))
                    st.info(t("download_tip", language))
                    
            base_folder = "audio" if file_ext == '.mp3' else "documentos"
            status_text.success(t("mission_complete", language).format(folder=base_folder))
            st.balloons()

    elif modo == "spider":
        if not NetworkManager.is_safe_url(start_url):
            st.error(t("unsafe_url", language))
        else:
            exts = [e.strip() if e.strip().startswith('.') else f".{e.strip()}" for e in target_exts.split(",")]
            spider = SpiderScraper()
            
            status_text.info(t("spider_crawling", language).format(url=start_url))
            
            spider.crawl_and_download(start_url, target_extensions=exts, max_depth=max_depth, max_files=limit)
            
            progress_bar.progress(1.0)
            status_text.success(t("spider_complete", language))
            st.balloons()

# --- Vistas persistentes / Explorador de archivos guardados ---

if modo == "images" and not start_btn:
    saved_concepts = get_subdirs("downloads/imagenes")
    if saved_concepts:
        st.markdown("---")
        st.subheader(t("existing_collections", language))
        c1, c2 = st.columns([3, 1])
        with c1:
            sel = st.selectbox(t("select_collection", language), options=saved_concepts)
        
        if sel:
            folder_path = os.path.join("downloads/imagenes", sel)
            imgs = sorted(glob.glob(os.path.join(folder_path, "*.*")))
            st.info(t("images_in_folder", language).format(count=len(imgs), folder=folder_path))
            if imgs:
                cols = st.columns(5)
                for i, img_path in enumerate(imgs):
                    with cols[i % 5]:
                        st.image(img_path, caption=os.path.basename(img_path), use_container_width=True)
            else:
                st.write(t("empty_folder", language))
    else:
        st.info(t("image_download_tip", language))

elif modo == "dataset" and not start_btn:
    doc_dirs = get_subdirs("downloads/documentos")
    audio_dirs = get_subdirs("downloads/audio")
    if doc_dirs or audio_dirs:
        st.markdown("---")
        st.subheader(t("saved_datasets", language))
        tab_doc, tab_aud = st.tabs([t("documents_tab", language), t("audio_tab", language)])
        with tab_doc:
            if doc_dirs:
                sel_doc = st.selectbox(t("select_documents_folder", language), options=doc_dirs)
                if sel_doc:
                    folder = os.path.join("downloads/documentos", sel_doc)
                    files = sorted(glob.glob(os.path.join(folder, "*.*")))
                    st.info(t("files_in_folder", language).format(count=len(files), folder=folder))
                    for f in files:
                        st.markdown(f"- 📄 `{os.path.basename(f)}` ({format_size_mb(f)})")
            else:
                st.write(t("no_documents", language))
        with tab_aud:
            if audio_dirs:
                sel_aud = st.selectbox(t("select_audio_folder", language), options=audio_dirs)
                if sel_aud:
                    folder = os.path.join("downloads/audio", sel_aud)
                    files = sorted(glob.glob(os.path.join(folder, "*.*")))
                    st.info(t("files_in_folder", language).format(count=len(files), folder=folder))
                    for f in files:
                        st.markdown(f"- 🎧 `{os.path.basename(f)}` ({format_size_mb(f)})")
            else:
                st.write(t("no_audio", language))
    else:
        st.info(t("dataset_download_tip", language))

elif modo == "spider" and not start_btn:
    spider_dirs = get_subdirs("downloads/spider")
    if spider_dirs:
        st.markdown("---")
        st.subheader(t("crawled_sites", language))
        sel_site = st.selectbox(t("select_website", language), options=spider_dirs)
        if sel_site:
            folder = os.path.join("downloads/spider", sel_site)
            files = sorted(glob.glob(os.path.join(folder, "*.*")))
            st.info(t("extracted_files", language).format(count=len(files), folder=folder))
            for f in files:
                st.markdown(f"- 📦 `{os.path.basename(f)}` ({format_size_mb(f)})")
    else:
        st.info(t("spider_download_tip", language))

elif modo == "library":
    st.header(t("library_title", language))
    st.markdown(t("library_description", language))
    
    db = DatabaseManager()
    all_downloads = db.get_all_downloads()
    
    img_folders = get_subdirs("downloads/imagenes")
    doc_folders = get_subdirs("downloads/documentos")
    aud_folders = get_subdirs("downloads/audio")
    spider_folders = get_subdirs("downloads/spider")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(t("image_collections_metric", language), len(img_folders))
    m2.metric(t("document_datasets_metric", language), len(doc_folders))
    m3.metric(t("spider_sites_metric", language), len(spider_folders))
    m4.metric(t("history_records_metric", language), len(all_downloads))
    
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        t("image_gallery_tab", language),
        t("datasets_documents_tab", language),
        t("spider_files_tab", language),
        t("osint_history_tab", language)
    ])
    
    with tab1:
        if img_folders:
            c1, _ = st.columns([3, 1])
            with c1:
                sel_gal = st.selectbox(t("image_collection", language), options=img_folders, key="bib_img")
            if sel_gal:
                fpath = os.path.join("downloads/imagenes", sel_gal)
                imgs = sorted(glob.glob(os.path.join(fpath, "*.*")))
                st.caption(t("image_count", language).format(count=len(imgs), folder=fpath))
                cols = st.columns(5)
                for i, img_path in enumerate(imgs):
                    with cols[i % 5]:
                        st.image(img_path, caption=os.path.basename(img_path), use_container_width=True)
        else:
            st.info(t("no_image_collections", language))
            
    with tab2:
        all_ds_folders = [
            (t("documents_category", language), "downloads/documentos", d) for d in doc_folders
        ] + [
            (t("audio_category", language), "downloads/audio", a) for a in aud_folders
        ]
        if all_ds_folders:
            folder_labels = [f"[{cat}] {name}" for cat, _, name in all_ds_folders]
            sel_idx = st.selectbox(t("select_dataset", language), range(len(folder_labels)), format_func=lambda i: folder_labels[i], key="bib_ds")
            cat, base, name = all_ds_folders[sel_idx]
            target_path = os.path.join(base, name)
            files = sorted(glob.glob(os.path.join(target_path, "*.*")))
            st.caption(t("showing_files", language).format(count=len(files), folder=target_path))
            for f in files:
                st.markdown(f"- `{os.path.basename(f)}` — **{format_size_mb(f)}**")
        else:
            st.info(t("no_datasets", language))
            
    with tab3:
        if spider_folders:
            sel_sp = st.selectbox(t("crawled_domain", language), options=spider_folders, key="bib_sp")
            if sel_sp:
                target_path = os.path.join("downloads/spider", sel_sp)
                files = sorted(glob.glob(os.path.join(target_path, "*.*")))
                st.caption(t("spider_file_count", language).format(count=len(files), folder=target_path))
                for f in files:
                    st.markdown(f"- 📦 `{os.path.basename(f)}` — **{format_size_mb(f)}**")
        else:
            st.info(t("no_spider_downloads", language))
            
    with tab4:
        if all_downloads:
            st.markdown(t("history_count", language).format(count=len(all_downloads)))
            st.dataframe(all_downloads, use_container_width=True)
        else:
            st.info(t("no_download_history", language))
