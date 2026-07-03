import random
import time
import requests
import logging
from typing import Optional

logger = logging.getLogger("scrapic")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
]

class NetworkManager:
    """Motor Anti-Bot: Maneja rotación de User-Agents y Exponential Backoff (reintentos espaciados)."""
    @staticmethod
    def get(url: str, params: dict = None, stream: bool = False, timeout: int = 15, max_retries: int = 3) -> Optional[requests.Response]:
        for attempt in range(max_retries):
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            try:
                res = requests.get(url, params=params, headers=headers, stream=stream, timeout=timeout, verify=False)
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
            try:
                res = requests.post(url, data=data, headers=headers, timeout=timeout, verify=False)
                if res.status_code in [429, 403, 503, 401]:
                    raise requests.exceptions.RequestException(f"Bloqueo (Status {res.status_code})")
                return res
            except requests.exceptions.RequestException as e:
                wait_time = 2 ** attempt
                logger.debug(f"Red/Anti-Bot detectó fallo POST en {url} ({e}). Reintento táctico en {wait_time}s... ({attempt+1}/{max_retries})")
                time.sleep(wait_time)
        return None
