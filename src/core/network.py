import random
import time
import requests
import os
import logging
from typing import Optional

logger = logging.getLogger("scrapic")

try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
]

class NetworkManager:
    """Motor Anti-Bot: Maneja rotación de User-Agents, Proxies dinámicos, Cloudscraper y Exponential Backoff."""
    
    _proxies_list = []
    _proxies_loaded = False
    
    @classmethod
    def _load_proxies(cls):
        if cls._proxies_loaded: return
        cls._proxies_loaded = True
        
        proxy_file = "proxies.txt"
        if os.path.exists(proxy_file):
            try:
                with open(proxy_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    cls._proxies_list = [p.strip() for p in lines if p.strip() and not p.startswith("#")]
                logger.info(f"🥷 Anti-Bot: Cargados {len(cls._proxies_list)} proxies desde {proxy_file}")
            except Exception as e:
                logger.warning(f"Error cargando proxies.txt: {e}")
                
    @classmethod
    def _get_random_proxy(cls) -> Optional[dict]:
        cls._load_proxies()
        if not cls._proxies_list: return None
        
        p = random.choice(cls._proxies_list)
        if not p.startswith("http"):
            p = f"http://{p}"
        return {"http": p, "https": p}

    @staticmethod
    def get(url: str, params: dict = None, stream: bool = False, timeout: int = 15, max_retries: int = 3) -> Optional[requests.Response]:
        for attempt in range(max_retries):
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            proxy = NetworkManager._get_random_proxy()
            
            try:
                if HAS_CLOUDSCRAPER:
                    scraper = cloudscraper.create_scraper()
                    res = scraper.get(url, params=params, headers=headers, stream=stream, timeout=timeout, proxies=proxy)
                else:
                    res = requests.get(url, params=params, headers=headers, stream=stream, timeout=timeout, proxies=proxy, verify=False)
                    
                if res.status_code in [429, 403, 503, 401]:
                    raise requests.exceptions.RequestException(f"Bloqueo (Status {res.status_code})")
                return res
            except requests.exceptions.RequestException as e:
                wait_time = 2 ** attempt
                logger.debug(f"Red/Anti-Bot detectó fallo en {url} ({e}). Reintento táctico en {wait_time}s... ({attempt+1}/{max_retries})")
                time.sleep(wait_time)
        return None

    @staticmethod
    def post(url: str, data: dict, timeout: int = 15, max_retries: int = 3) -> Optional[requests.Response]:
        for attempt in range(max_retries):
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            proxy = NetworkManager._get_random_proxy()
            
            try:
                if HAS_CLOUDSCRAPER:
                    scraper = cloudscraper.create_scraper()
                    res = scraper.post(url, data=data, headers=headers, timeout=timeout, proxies=proxy)
                else:
                    res = requests.post(url, data=data, headers=headers, timeout=timeout, proxies=proxy, verify=False)
                    
                if res.status_code in [429, 403, 503, 401]:
                    raise requests.exceptions.RequestException(f"Bloqueo (Status {res.status_code})")
                return res
            except requests.exceptions.RequestException as e:
                wait_time = 2 ** attempt
                logger.debug(f"Red/Anti-Bot detectó fallo POST en {url} ({e}). Reintento táctico en {wait_time}s... ({attempt+1}/{max_retries})")
                time.sleep(wait_time)
        return None
