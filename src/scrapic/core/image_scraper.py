import os
import re
import time
import shutil
import urllib.parse
import logging
from typing import List
from concurrent.futures import ThreadPoolExecutor

from icrawler.builtin import BingImageCrawler, BaiduImageCrawler
from icrawler.downloader import ImageDownloader
from scrapic.core.history import HistoryManager
from scrapic.core.network import NetworkManager
from scrapic.core.report import OSINTReporter
from scrapic.core.utils import FileUtils, MAX_DOWNLOAD_BYTES

logger = logging.getLogger("scrapic")


class BoundedImageDownloader(ImageDownloader):
    """icrawler downloader that buffers image data only up to a fixed byte limit."""

    def __init__(self, thread_num, signal, session, storage, max_bytes=MAX_DOWNLOAD_BYTES):
        super().__init__(thread_num, signal, session, storage)
        if max_bytes <= 0:
            raise ValueError("max_bytes debe ser mayor que cero.")
        self.max_bytes = max_bytes
        self.download_records = []

    def download(self, task, default_ext, timeout=5, max_retry=3, overwrite=False, **kwargs):
        file_url = task["file_url"]
        task["success"] = False
        task["filename"] = None
        retry = max_retry

        if not overwrite:
            with self.lock:
                self.fetched_num += 1
                filename = self.get_filename(task, default_ext)
                if self.storage.exists(filename):
                    return
                self.fetched_num -= 1

        while retry > 0 and not self.signal.get("reach_max_num"):
            response = None
            try:
                response = self.session.get(file_url, timeout=timeout, stream=True)
                if response.status_code != 200:
                    break
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > self.max_bytes:
                    break

                content = bytearray()
                oversized = False
                for chunk in response.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    if len(content) + len(chunk) > self.max_bytes:
                        oversized = True
                        break
                    content.extend(chunk)
                if oversized:
                    break

                response._content = bytes(content)
                response._content_consumed = True
                if self.reach_max_num():
                    self.signal.set(reach_max_num=True)
                    break
                if not self.keep_file(task, response, **kwargs):
                    break
                with self.lock:
                    self.fetched_num += 1
                    filename = self.get_filename(task, default_ext)
                self.storage.write(filename, response.content)
                with self.lock:
                    self.download_records.append((filename, file_url))
                task["success"] = True
                task["filename"] = filename
                break
            except (OSError, ValueError) as exc:
                self.logger.debug("Failed bounded image download from %s: %s", file_url, exc)
                break
            except Exception as exc:
                self.logger.error("Exception downloading image %s: %s", file_url, exc)
            finally:
                if response is not None:
                    response.close()
                retry -= 1


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

    def _move_and_prefix(self, source_dir: str, dest_dir: str, prefix: str, download_records=None):
        if not os.path.exists(source_dir):
            return
        source_urls = dict(download_records or [])
        files = os.listdir(source_dir)
        for f in files:
            src_path = os.path.join(source_dir, f)
            dest_path = os.path.join(dest_dir, f"{prefix}_{f}")
            if os.path.isfile(src_path):
                if os.path.exists(dest_path):
                    name, ext = os.path.splitext(f)
                    dest_path = os.path.join(dest_dir, f"{prefix}_{name}_{int(time.time())}{ext}")
                shutil.move(src_path, dest_path)
                source_url = source_urls.get(f)
                if source_url:
                    report_saved = self.reporter.log_download(
                        dest_path, source_url, f"Image Scraper ({prefix})"
                    )
                    if report_saved:
                        if not self.history.mark_as_downloaded(source_url):
                            logger.error("El archivo %s se movió, pero no se pudo guardar su historial.", dest_path)
                    else:
                        logger.error("El archivo %s se movió, pero no se pudo guardar su reporte.", dest_path)
                else:
                    logger.warning("No hay URL de origen para el archivo de imagen %s.", f)
        shutil.rmtree(source_dir)

    def _download_image(self, idx: int, url: str, save_dir: str, prefix: str, max_bytes: int = MAX_DOWNLOAD_BYTES) -> bool:
        try:
            response = NetworkManager.get(url, stream=True, timeout=10)
            if not response:
                return False
            if not response.ok:
                response.close()
                return False

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
            FileUtils.save_response(response, filepath, max_bytes=max_bytes)
            if not self.reporter.log_download(filepath, url, f"Image Scraper ({prefix})"):
                return False
            if not self.history.mark_as_downloaded(url):
                return False
            return True
        except Exception as e:
            logger.debug(f"Error descargando imagen desde {url}: {e}")
        return False

    def scrape_bing(self, concept: str, concept_dir: str, limit: int = 15, max_bytes: int = MAX_DOWNLOAD_BYTES):
        """Descarga imágenes usando el motor de Bing."""
        logger.info(f"Scraping Bing: {concept}")
        temp_dir = os.path.join(concept_dir, "temp_bing")
        crawler = BingImageCrawler(
            storage={'root_dir': temp_dir},
            log_level=60,
            downloader_cls=BoundedImageDownloader,
            extra_downloader_args={"max_bytes": max_bytes},
        )
        crawler.crawl(keyword=concept, max_num=limit)
        self._move_and_prefix(temp_dir, concept_dir, "bing", crawler.downloader.download_records)
        self.history.flush()

    def scrape_baidu(self, concept: str, concept_dir: str, limit: int = 15, max_bytes: int = MAX_DOWNLOAD_BYTES):
        """Descarga imágenes usando el motor de Baidu."""
        logger.info(f"Scraping Baidu: {concept}")
        temp_dir = os.path.join(concept_dir, "temp_baidu")
        crawler = BaiduImageCrawler(
            storage={'root_dir': temp_dir},
            log_level=60,
            downloader_cls=BoundedImageDownloader,
            extra_downloader_args={"max_bytes": max_bytes},
        )
        crawler.crawl(keyword=concept, max_num=limit)
        self._move_and_prefix(temp_dir, concept_dir, "baidu", crawler.downloader.download_records)
        self.history.flush()

    def scrape_yandex(self, concept: str, concept_dir: str, limit: int = 15, max_bytes: int = MAX_DOWNLOAD_BYTES):
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
                    executor.submit(self._download_image, i + 1, img_url, concept_dir, "yandex", max_bytes)
        except Exception as e:
            logger.error(f"Error en Yandex: {e}")
