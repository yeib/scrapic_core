import os
import re
import time
import shutil
import urllib.parse
import logging
from typing import List
from concurrent.futures import ThreadPoolExecutor

from icrawler.builtin import BingImageCrawler, BaiduImageCrawler
from src.core.history import HistoryManager
from src.core.network import NetworkManager
from src.core.report import OSINTReporter

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger("scrapic")

class MultiEngineScraper:
    """Scraper multi-motor para descarga masiva de imágenes.
    Soporta Bing (via icrawler), Baidu (via icrawler) y Yandex (via scraping directo).
    Usa rotación de User-Agent y HistoryManager para evitar duplicados.
    """
    def __init__(self, base_dir: str = "downloads/imagenes"):
        self.base_dir = base_dir
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }
        self.history = HistoryManager()
        self.reporter = OSINTReporter()

    def create_concept_dir(self, concept: str) -> str:
        """Crea el directorio destino para las imágenes de un concepto."""
        return FileUtils.make_concept_dir(self.base_dir, concept)

    def _move_and_prefix(self, source_dir: str, dest_dir: str, prefix: str):
        if not os.path.exists(source_dir):
            return
        files = os.listdir(source_dir)
        for f in files:
            src_path = os.path.join(source_dir, f)
            dest_path = os.path.join(dest_dir, f"{prefix}_{f}")
            if os.path.isfile(src_path):
                if os.path.exists(dest_path):
                    name, ext = os.path.splitext(f)
                    dest_path = os.path.join(dest_dir, f"{prefix}_{name}_{int(time.time())}{ext}")
                shutil.move(src_path, dest_path)
        shutil.rmtree(source_dir)

    def _download_image(self, idx: int, url: str, save_dir: str, prefix: str) -> bool:
        try:
            response = NetworkManager.get(url, timeout=10)
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '').lower()
                if 'image/jpeg' in content_type: ext = 'jpg'
                elif 'image/png' in content_type: ext = 'png'
                elif 'image/gif' in content_type: ext = 'gif'
                elif 'image/webp' in content_type: ext = 'webp'
                else:
                    ext = url.split('.')[-1].split('?')[0].lower()
                    if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                        ext = "jpg"
                
                filename = f"{prefix}_{idx:06d}.{ext}"
                filepath = os.path.join(save_dir, filename)
                with open(filepath, "wb") as f:
                    f.write(response.content)
                self.history.mark_as_downloaded(url)
                self.reporter.log_download(filepath, url, f"Image Scraper ({prefix})")
                return True
        except Exception:
            pass
        return False

    def scrape_bing(self, concept: str, concept_dir: str, limit: int = 15):
        """Descarga imágenes usando el motor de Bing."""
        logger.info(f"Scraping Bing: {concept}")
        temp_dir = os.path.join(concept_dir, "temp_bing")
        crawler = BingImageCrawler(storage={'root_dir': temp_dir}, log_level=60)
        crawler.crawl(keyword=concept, max_num=limit)
        self._move_and_prefix(temp_dir, concept_dir, "bing")
        self.history.flush()

    def scrape_baidu(self, concept: str, concept_dir: str, limit: int = 15):
        """Descarga imágenes usando el motor de Baidu."""
        logger.info(f"Scraping Baidu: {concept}")
        temp_dir = os.path.join(concept_dir, "temp_baidu")
        crawler = BaiduImageCrawler(storage={'root_dir': temp_dir}, log_level=60)
        crawler.crawl(keyword=concept, max_num=limit)
        self._move_and_prefix(temp_dir, concept_dir, "baidu")
        self.history.flush()

    def scrape_yandex(self, concept: str, concept_dir: str, limit: int = 15):
        """Descarga imágenes desde Yandex haciendo scraping directo del HTML de búsqueda."""
        logger.info(f"Scraping Yandex: {concept}")
        try:
            query = urllib.parse.quote(concept)
            url = f"https://yandex.com/images/search?text={query}&family=no"
            res = NetworkManager.get(url, timeout=10)  # Usa anti-bot completo: retry, proxies, backoff
            if not res:
                logger.warning(f"No se pudo conectar a Yandex para '{concept}'.")
                return
            
            encoded_urls = re.findall(r"img_url=([^&]+)", res.text)
            
            image_urls = []
            for u in encoded_urls:
                decoded = urllib.parse.unquote(u)
                if decoded.startswith('http') and not self.history.is_downloaded(decoded):
                    image_urls.append(decoded)
                if len(image_urls) >= limit:
                    break
            
            if not image_urls:
                logger.warning(f"No se encontraron imágenes nuevas en Yandex para {concept}.")
                return

            with ThreadPoolExecutor(max_workers=5) as executor:
                for i, img_url in enumerate(image_urls):
                    executor.submit(self._download_image, i + 1, img_url, concept_dir, "yandex")
        except Exception as e:
            logger.error(f"Error en Yandex: {e}")

