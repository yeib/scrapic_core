import random
import time
import requests
import os
import logging
import threading
import socket
import ipaddress
import urllib.parse
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
    _thread_local = threading.local()  # Sesión de cloudscraper reutilizable por hilo

    @staticmethod
    def is_safe_url(url: str) -> bool:
        """Reject URLs whose resolved addresses are not public HTTP(S) destinations."""
        try:
            parsed = urllib.parse.urlsplit(url)
            if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
                return False
            if parsed.username is not None or parsed.password is not None:
                return False
            port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
            addresses = socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM)
            if not addresses:
                return False

            for address in addresses:
                ip = ipaddress.ip_address(address[4][0].split("%", 1)[0])
                if (
                    ip.is_private
                    or ip.is_loopback
                    or ip.is_link_local
                    or ip.is_reserved
                    or ip.is_multicast
                    or ip.is_unspecified
                    or not ip.is_global
                ):
                    return False
            return True
        except (ValueError, OSError, socket.gaierror):
            return False
    
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

    @classmethod
    def _get_cloudscraper(cls):
        """Devuelve la sesión de cloudscraper del hilo actual, creándola si no existe."""
        if not hasattr(cls._thread_local, 'scraper'):
            cls._thread_local.scraper = cloudscraper.create_scraper()
        return cls._thread_local.scraper

    @staticmethod
    def get(url: str, params: dict = None, stream: bool = False, timeout: int = 15, max_retries: int = 3, allow_redirects: bool = True) -> Optional[requests.Response]:
        for attempt in range(max_retries):
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            proxy = NetworkManager._get_random_proxy()
            
            try:
                if HAS_CLOUDSCRAPER:
                    scraper = NetworkManager._get_cloudscraper()
                    res = scraper.get(url, params=params, headers=headers, stream=stream, timeout=timeout, proxies=proxy, allow_redirects=allow_redirects)
                else:
                    res = requests.get(url, params=params, headers=headers, stream=stream, timeout=timeout, proxies=proxy, allow_redirects=allow_redirects)
                    
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
                    scraper = NetworkManager._get_cloudscraper()
                    res = scraper.post(url, data=data, headers=headers, timeout=timeout, proxies=proxy)
                else:
                    res = requests.post(url, data=data, headers=headers, timeout=timeout, proxies=proxy)
                    
                if res.status_code in [429, 403, 503, 401]:
                    raise requests.exceptions.RequestException(f"Bloqueo (Status {res.status_code})")
                return res
            except requests.exceptions.RequestException as e:
                wait_time = 2 ** attempt
                logger.debug(f"Red/Anti-Bot detectó fallo POST en {url} ({e}). Reintento táctico en {wait_time}s... ({attempt+1}/{max_retries})")
                time.sleep(wait_time)
        return None
