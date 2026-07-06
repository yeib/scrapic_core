import os
import re
import urllib.parse
import logging
import concurrent.futures
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import threading
from typing import List, Tuple

from src.core.network import NetworkManager
from src.core.utils import FileUtils
from src.core.history import HistoryManager
from src.core.report import OSINTReporter

logger = logging.getLogger("scrapic")

class SpiderScraper:
    """Modo Araña (Spider): Extrae todos los archivos de un dominio completo de forma recursiva."""
    def __init__(self, base_dir: str = "downloads/spider"):
        self.base_dir = base_dir
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
        self.history = HistoryManager()
        self.reporter = OSINTReporter()

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

    def _scan_url(self, url: str, base_domain: str, target_extensions: List[str]) -> Tuple[List[str], List[str]]:
        """Wrapper de _get_links para uso como callable en ThreadPoolExecutor."""
        return self._get_links(url, base_domain, target_extensions)

    def crawl_and_download(self, start_url: str, target_extensions: List[str] = ['.pdf'], max_depth: int = 2, max_files: int = 20, regex_pattern: str = None):
        """
        Realiza un mapeo y extracción completa de un sitio web.
        
        Args:
            start_url (str): URL semilla por donde empezará a escanear.
            target_extensions (List[str]): Lista de extensiones a atrapar (ej: ['.pdf', '.csv']).
            max_depth (int): Profundidad máxima de clicks desde la URL original.
            max_files (int): Límite total de archivos a descargar.
            regex_pattern (str): Patrón Regex opcional para filtrar los archivos (ej: 'reporte_202[0-4]').
            
        El proceso se divide en dos fases:
        Fase 1: Escaneo en anchura (BFS) asíncrono para mapear todos los links internos rápidamente.
        Fase 2: Descarga masiva y concurrente usando ThreadPoolExecutor para mayor velocidad.
        """
        logger.info(f"🕸️ Iniciando Spider en: {start_url} (Profundidad Máxima: {max_depth})")
        parsed_start = urllib.parse.urlparse(start_url)
        base_domain = parsed_start.netloc
        
        domain_dir = os.path.join(self.base_dir, base_domain.replace(".", "_"))
        os.makedirs(domain_dir, exist_ok=True)

        # Fase 1: Rastreo Recursivo (BFS Concurrente por niveles)
        logger.info("Fase 1: Mapeo recursivo asíncrono del sitio web...")
        
        compiled_regex = re.compile(regex_pattern, re.IGNORECASE) if regex_pattern else None
        
        visited_pages = set()
        current_level_urls = {start_url}
        found_files = set()

        for depth in range(max_depth + 1):
            if not current_level_urls or len(found_files) >= max_files * 2:
                break
                
            logger.info(f"Escaneando {len(current_level_urls)} páginas en profundidad {depth}...")
            next_level_urls = set()

            with ThreadPoolExecutor(max_workers=15) as executor:
                future_to_url = {executor.submit(self._scan_url, url, base_domain, target_extensions): url for url in current_level_urls}
                
                for future in concurrent.futures.as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        new_pages, new_files = future.result()
                        
                        for f in new_files:
                            if compiled_regex and not compiled_regex.search(f):
                                continue # El link no cumple el filtro Regex
                                
                            if f not in found_files and not self.history.is_downloaded(f):
                                found_files.add(f)
                                
                        for p in new_pages:
                            if p not in visited_pages and p not in current_level_urls:
                                next_level_urls.add(p)
                                
                    except Exception as e:
                        logger.debug(f"Error escaneando url {url}: {e}")
                        
            visited_pages.update(current_level_urls)
            current_level_urls = next_level_urls

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
                        self.reporter.log_download(filepath, url, "Spider")
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
        self.history.flush()

