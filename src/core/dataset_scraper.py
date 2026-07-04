import os
import urllib.parse
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup

from src.core.history import HistoryManager
from src.core.network import NetworkManager
from src.core.utils import FileUtils
from src.core.report import OSINTReporter

logger = logging.getLogger("scrapic")

class DatasetScraper:
    """Scraper especializado en obtener archivos masivos (PDF, CSV, JSON, MD, MP3) desde internet.
    Usa Yahoo Search con dorking de filetype para localizar archivos directamente descargables.
    Para MP3, delega al modo Media Ripper vía yt-dlp + FFmpeg.
    Incluye sistema de filtros inteligentes: tamaño, páginas (PDF) y duración (MP3).
    """
    def __init__(self):
        self.history = HistoryManager()
        self.reporter = OSINTReporter()

    def create_concept_dir(self, concept: str, file_ext: str) -> str:
        """Crea el directorio destino dependiendo del tipo de archivo."""
        base = "downloads/audio" if file_ext == '.mp3' else "downloads/documentos"
        concept_dir = os.path.join(base, concept.replace(" ", "_"))
        if not os.path.exists(concept_dir):
            os.makedirs(concept_dir)
        return concept_dir

    def _download_file(self, idx: int, url: str, save_dir: str, file_ext: str, min_size_mb: float, min_pages: int, successes: list, limit: int, lock: threading.Lock) -> bool:
        """
        Descarga un archivo, lo guarda temporalmente y aplica filtros inteligentes (tamaño, páginas, formato).
        Si falla algún filtro, el archivo es eliminado automáticamente.
        """
        with lock:
            if len(successes) >= limit: return False

        filepath = None
        try:
            # Fase 1: Headers y descarga temprana
            response = NetworkManager.get(url, stream=True, timeout=20)
            if not response: return False

            # Validar tamaño desde headers si está disponible (ahorra ancho de banda)
            content_length = response.headers.get('Content-Length')
            if content_length and min_size_mb > 0:
                if (int(content_length) / (1024 * 1024)) < min_size_mb:
                    return False

            raw_name = url.split('/')[-1].split('?')[0]
            if not raw_name.lower().endswith(file_ext):
                raw_name = f"dataset_{idx:03d}{file_ext}"
            
            clean_name = FileUtils.clean_filename(raw_name)
            filepath = os.path.join(save_dir, f"{idx:03d}_{clean_name}")
            
            # Fase 2: Escritura a disco
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            with lock:
                if len(successes) >= limit:
                    if os.path.exists(filepath): os.remove(filepath)
                    return False
            
            # Fase 3: Validaciones Post-Descarga (Filtros Inteligentes)
            if not FileUtils.validate_size(filepath, min_size_mb):
                os.remove(filepath)
                return False

            if file_ext == '.pdf' and not FileUtils.validate_pdf(filepath, min_pages):
                os.remove(filepath)
                return False

            if file_ext in ['.csv', '.json'] and not FileUtils.validate_dataset(filepath, file_ext):
                os.remove(filepath)
                return False

            # Éxito: Todas las validaciones pasadas
            with lock:
                if len(successes) < limit:
                    successes.append(url)
                    self.history.mark_as_downloaded(url)
                    self.reporter.log_download(filepath, url, f"Dataset ({file_ext})")
                    return True
                else:
                    if os.path.exists(filepath): os.remove(filepath)

        except Exception as e:
            logger.debug(f"Fallo en _download_file para {url}: {e}")
            if filepath and os.path.exists(filepath):
                try: os.remove(filepath)
                except: pass
        return False

    def _scrape_mp3_yt(self, concept: str, concept_dir: str, limit: int, max_duration_mins: int = 15) -> int:
        import shutil
        if shutil.which("ffmpeg") is None:
            logger.error("\n❌ [ERROR CRÍTICO] 'ffmpeg' no está instalado en tu sistema.")
            logger.error("El Media Ripper necesita FFmpeg para convertir los videos a MP3.")
            logger.error("👉 Windows: winget install ffmpeg (o instálalo manual desde ffmpeg.org)")
            logger.error("👉 Mac: brew install ffmpeg")
            logger.error("👉 Linux: sudo apt install ffmpeg\n")
            return 0
            
        import yt_dlp
        logger.info(f"Modo Media Ripper (yt-dlp) activado para: {concept}")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(concept_dir, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': False,
            'no_warnings': True,
            'extract_audio': True,
            'noplaylist': True,
            'keepvideo': False,
        }
        
        if max_duration_mins > 0:
            ydl_opts['match_filter'] = yt_dlp.utils.match_filter_func(f"duration <= {max_duration_mins * 60}")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch{limit * 3}:{concept}", download=False)
                if not info or 'entries' not in info:
                    return 0
                
                successes = 0
                for entry in info['entries']:
                    if not entry: continue
                    url = entry.get('webpage_url', entry.get('url', ''))
                    if not url or self.history.is_downloaded(url):
                        continue
                    
                    try:
                        logger.debug(f"Ripper descargando: {entry.get('title', url)}")
                        ydl.download([url])
                        self.history.mark_as_downloaded(url)
                        
                        # Loggear en reporte
                        title = entry.get('title', 'audio_desconocido')
                        file_guess = os.path.join(concept_dir, f"{title}.mp3")
                        self.reporter.log_download(file_guess, url, "Media Ripper")
                        
                        successes += 1
                    except Exception as e:
                        logger.debug(f"Fallo extrayendo audio de {url}: {e}")
                        
                    if successes >= limit:
                        break
                return successes
        except Exception as e:
            if "ffprobe" in str(e).lower() or "ffmpeg" in str(e).lower():
                logger.error("⚠ CRÍTICO: Necesitas instalar 'ffmpeg' en tu sistema (ej: sudo apt install ffmpeg) para convertir el audio a MP3.")
            else:
                logger.error(f"Error en Media Ripper: {e}")
            return 0

    def scrape_dataset(self, concept: str, file_ext: str = '.pdf', limit: int = 5, min_size_mb: float = 0, min_pages: int = 0, max_duration_mins: int = 15) -> int:
        """
        Busca y descarga archivos masivamente desde internet usando Yahoo Search (OSINT dorking).
        
        Args:
            concept (str): Palabra clave o tema de investigación.
            file_ext (str): Extensión del archivo objetivo (ej: .pdf, .mp3, .csv).
            limit (int): Límite de archivos exitosos a descargar.
            min_size_mb (float): Peso mínimo del archivo (filtro anti-basura).
            min_pages (int): Páginas mínimas, solo válido si es PDF.
            max_duration_mins (int): Duración máxima en minutos, solo válido si es MP3.
            
        Retorna:
            int: Cantidad de archivos descargados que cumplieron todos los filtros.
        """
        logger.info(f"Buscando archivos {file_ext} en la web para: {concept}")
        concept_dir = self.create_concept_dir(concept, file_ext)
        
        if file_ext == '.mp3':
            return self._scrape_mp3_yt(concept, concept_dir, limit, max_duration_mins)
            
        successes = []
        lock = threading.Lock()
        
        try:
            url = "https://search.yahoo.com/search"
            ext_no_dot = file_ext.strip('.')
            query = f"{concept} filetype:{ext_no_dot}"
            
            for page in range(5):
                logger.debug(f"Consultando página {page+1} de resultados en Yahoo...")
                params = {"p": query, "b": (page * 10) + 1}
                res = NetworkManager.get(url, params=params, timeout=15)
                if not res: break
                
                soup = BeautifulSoup(res.text, "html.parser")
                file_links = []
                
                # Buscamos cualquier enlace válido (Yahoo devuelve los links directos)
                for a in soup.find_all("a", href=True):
                    real_url = a['href']
                    # Yahoo a veces mete su propia URL de tracking (r.search.yahoo.com/RV=2/RE=.../RU=https://url_real.pdf)
                    # Tratamos de limpiar eso o tomar solo URLs puras
                    if "RU=" in real_url:
                        try:
                            real_url = urllib.parse.unquote(real_url.split("RU=")[1].split("/RK=")[0])
                        except: pass
                        
                    if real_url.startswith("http") and file_ext in real_url.lower():
                        if "yahoo.com" not in real_url and not self.history.is_downloaded(real_url):
                            file_links.append(real_url)
                
                if file_links:
                    logger.info(f"Página {page+1}: Probando {len(file_links)} enlaces con los filtros...")
                    with ThreadPoolExecutor(max_workers=3) as executor:
                        for idx, file_url in enumerate(file_links):
                            executor.submit(self._download_file, len(successes) + idx + 1, file_url, concept_dir, file_ext, min_size_mb, min_pages, successes, limit, lock)
                
                if len(successes) >= limit:
                    break
                    
                # Si no encontramos suficientes links en la página, probablemente no hay más resultados relevantes
                if len(file_links) == 0:
                    logger.warning("No se encontraron más enlaces en esta página. Finalizando búsqueda.")
                    break
            
            logger.info(f"Proceso terminado. Se lograron descargar {len(successes)} archivos que cumplen los filtros.")
            return len(successes)
                    
        except Exception as e:
            logger.error(f"Error al scrapear datos: {e}")
            return 0
