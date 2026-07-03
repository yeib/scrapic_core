import os
import urllib.parse
import logging
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import threading
from typing import List, Tuple

from src.core.network import NetworkManager
from src.core.utils import FileUtils
from src.core.history import HistoryManager

logger = logging.getLogger("scrapic")

class SpiderScraper:
    """Modo Araña (Spider): Extrae todos los archivos de un dominio completo de forma recursiva."""
    def __init__(self, base_dir: str = "downloads/spider"):
        self.base_dir = base_dir
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
        self.history = HistoryManager()

    def _get_links(self, url: str, base_domain: str, target_extensions: List[str]) -> Tuple[List[str], List[str]]:
        """Retorna (páginas_internas, archivos_objetivo)"""
        pages = []
        files = []
        res = NetworkManager.get(url, timeout=10)
        if not res:
            return pages, files
        
        soup = BeautifulSoup(res.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = urllib.parse.urljoin(url, a['href'])
            parsed = urllib.parse.urlparse(href)
            
            if not href.startswith("http"): continue
            
            ext = os.path.splitext(parsed.path)[1].lower()
            if ext in target_extensions:
                files.append(href)
            elif parsed.netloc == base_domain:
                if ext in ['', '.html', '.php', '.asp', '.htm']:
                    # Eliminar fragmentos para no visitar la misma página por anchors
                    clean_page = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, parsed.query, ''))
                    pages.append(clean_page)
                    
        return pages, files

    def crawl_and_download(self, start_url: str, target_extensions: List[str] = ['.pdf'], max_depth: int = 2, max_files: int = 20):
        """
        Realiza un mapeo y extracción completa de un sitio web.
        
        Args:
            start_url (str): URL semilla por donde empezará a escanear.
            target_extensions (List[str]): Lista de extensiones a atrapar (ej: ['.pdf', '.csv']).
            max_depth (int): Profundidad máxima de clicks desde la URL original.
            max_files (int): Límite total de archivos a descargar.
            
        El proceso se divide en dos fases:
        Fase 1: Escaneo en anchura (BFS) para mapear todos los links internos sin descargar nada.
        Fase 2: Descarga masiva y concurrente usando ThreadPoolExecutor para mayor velocidad.
        """
        logger.info(f"🕸️ Iniciando Spider en: {start_url} (Profundidad Máxima: {max_depth})")
        parsed_start = urllib.parse.urlparse(start_url)
        base_domain = parsed_start.netloc
        
        domain_dir = os.path.join(self.base_dir, base_domain.replace(".", "_"))
        if not os.path.exists(domain_dir):
            os.makedirs(domain_dir)

        visited_pages = set()
        queue = [(start_url, 0)]
        found_files = set()

        # Fase 1: Rastreo Recursivo (BFS)
        logger.info("Fase 1: Mapeo recursivo del sitio web...")
        while queue:
            current_url, depth = queue.pop(0)
            if current_url in visited_pages or depth > max_depth:
                continue
            
            logger.debug(f"Spider analizando: {current_url} (Profundidad {depth})")
            visited_pages.add(current_url)
            
            new_pages, new_files = self._get_links(current_url, base_domain, target_extensions)
            
            for f in new_files:
                if f not in found_files and not self.history.is_downloaded(f):
                    found_files.add(f)
                    
            if len(found_files) >= max_files * 2: 
                break
                
            for p in new_pages:
                if p not in visited_pages:
                    queue.append((p, depth + 1))

        if not found_files:
            logger.warning(f"No se encontraron archivos {target_extensions} en {start_url}")
            return
            
        logger.info(f"🕷️ Spider encontró {len(found_files)} archivos. Iniciando Fase 2 (Descarga Agresiva)...")
        
        # Fase 2: Descarga
        successes = []
        lock = threading.Lock()
        
        def download_worker(idx, url):
            with lock:
                if len(successes) >= max_files: return False
                
            res = NetworkManager.get(url, stream=True)
            if not res: return False
            
            raw_name = url.split('/')[-1].split('?')[0]
            clean_name = FileUtils.clean_filename(raw_name)
            filepath = os.path.join(domain_dir, f"{idx:03d}_{clean_name}")
            
            try:
                with open(filepath, "wb") as f:
                    for chunk in res.iter_content(8192):
                        f.write(chunk)
                        
                with lock:
                    if len(successes) < max_files:
                        successes.append(url)
                        self.history.mark_as_downloaded(url)
                        return True
                    else:
                        if os.path.exists(filepath): os.remove(filepath)
            except Exception as e:
                logger.debug(f"Error guardando de Spider: {e}")
            return False
                
        with ThreadPoolExecutor(max_workers=4) as executor:
            for i, file_url in enumerate(list(found_files)[:max_files*2]):
                executor.submit(download_worker, i+1, file_url)
                
        logger.info(f"🕸️ Spider finalizó: {len(successes)} archivos extraídos de {base_domain}.")
