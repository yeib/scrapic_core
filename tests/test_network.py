import pytest
from unittest.mock import patch, MagicMock
import requests
import socket

from scrapic.core.network import NetworkManager


def _make_mock_response(status_code=200):
    """Helper que crea un mock de requests.Response."""
    mock_resp = MagicMock(spec=requests.Response)
    mock_resp.status_code = status_code
    mock_resp.text = "<html>ok</html>"
    mock_resp.headers = {}
    return mock_resp


class TestNetworkManagerGet:

    def test_get_returns_response_on_success(self):
        """GET exitoso (200) devuelve el objeto Response."""
        mock_resp = _make_mock_response(200)

        with patch("requests.get", return_value=mock_resp):
            # Forzar que no use cloudscraper para el mock
            with patch("scrapic.core.network.HAS_CLOUDSCRAPER", False):
                result = NetworkManager.get("https://ejemplo.com")

        assert result is not None
        assert result.status_code == 200

    @pytest.mark.parametrize(
        "url, resolved_ip",
        [
            ("http://127.0.0.1/", "127.0.0.1"),
            ("http://localhost/", "127.0.0.1"),
            ("http://10.0.0.1/", "10.0.0.1"),
            ("http://169.254.169.254/", "169.254.169.254"),
        ],
    )
    def test_is_safe_url_rejects_private_destinations(self, url, resolved_ip):
        address = (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (resolved_ip, 80))
        with patch("scrapic.core.network.socket.getaddrinfo", return_value=[address]):
            assert NetworkManager.is_safe_url(url) is False

    @pytest.mark.parametrize("url", ["file:///etc/passwd", "ftp://example.org/file"])
    def test_is_safe_url_rejects_non_http_schemes(self, url):
        with patch("scrapic.core.network.socket.getaddrinfo") as resolver:
            assert NetworkManager.is_safe_url(url) is False
        resolver.assert_not_called()

    def test_is_safe_url_accepts_public_destination(self):
        address = (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("8.8.8.8", 443))
        with patch("scrapic.core.network.socket.getaddrinfo", return_value=[address]):
            assert NetworkManager.is_safe_url("https://example.org/") is True

    def test_get_does_not_disable_tls_verification(self):
        mock_resp = _make_mock_response(200)

        with patch("scrapic.core.network.HAS_CLOUDSCRAPER", False):
            with patch("requests.get", return_value=mock_resp) as mock_get:
                NetworkManager.get("https://ejemplo.com")

        assert mock_get.call_args.kwargs.get("verify", True) is True

    def test_get_retries_on_connection_error(self):
        """GET reintenta automáticamente si hay error de conexión."""
        mock_resp = _make_mock_response(200)

        with patch("scrapic.core.network.HAS_CLOUDSCRAPER", False):
            with patch("requests.get", side_effect=[
                requests.exceptions.ConnectionError("Sin conexión"),
                mock_resp,  # 2do intento: éxito
            ]) as mock_get:
                with patch("time.sleep"):  # Evitar esperas reales en tests
                    result = NetworkManager.get("https://ejemplo.com", max_retries=3)

        assert result is not None
        assert mock_get.call_count == 2

    def test_get_returns_none_after_all_retries_exhausted(self):
        """GET devuelve None si todos los reintentos fallan."""
        with patch("scrapic.core.network.HAS_CLOUDSCRAPER", False):
            with patch("requests.get", side_effect=requests.exceptions.ConnectionError("Timeout")):
                with patch("time.sleep"):
                    result = NetworkManager.get("https://ejemplo.com", max_retries=3)

        assert result is None

    def test_get_retries_on_blocked_status(self):
        """GET reintenta si recibe status de bloqueo (429, 403, 503)."""
        mock_blocked = _make_mock_response(429)
        mock_ok = _make_mock_response(200)

        with patch("scrapic.core.network.HAS_CLOUDSCRAPER", False):
            with patch("requests.get", side_effect=[mock_blocked, mock_ok]):
                with patch("time.sleep"):
                    result = NetworkManager.get("https://ejemplo.com", max_retries=3)

        # El 429 dispara excepción internamente y reintenta → devuelve el 200
        assert result is not None

    def test_get_uses_random_user_agent(self):
        """Cada request usa un User-Agent de la lista, no uno fijo."""
        mock_resp = _make_mock_response(200)
        captured_headers = []

        def capture_call(*args, **kwargs):
            captured_headers.append(kwargs.get("headers", {}).get("User-Agent", ""))
            return mock_resp

        with patch("scrapic.core.network.HAS_CLOUDSCRAPER", False):
            with patch("requests.get", side_effect=capture_call):
                NetworkManager.get("https://ejemplo.com")

        assert len(captured_headers) == 1
        assert captured_headers[0] != "", "El User-Agent no debería estar vacío"


class TestNetworkManagerPost:

    def test_post_returns_response_on_success(self):
        """POST exitoso devuelve el objeto Response."""
        mock_resp = _make_mock_response(200)

        with patch("scrapic.core.network.HAS_CLOUDSCRAPER", False):
            with patch("requests.post", return_value=mock_resp):
                result = NetworkManager.post("https://ejemplo.com", data={"key": "value"})

        assert result is not None
        assert result.status_code == 200

    def test_post_does_not_disable_tls_verification(self):
        mock_resp = _make_mock_response(200)

        with patch("scrapic.core.network.HAS_CLOUDSCRAPER", False):
            with patch("requests.post", return_value=mock_resp) as mock_post:
                NetworkManager.post("https://ejemplo.com", data={})

        assert mock_post.call_args.kwargs.get("verify", True) is True

    def test_post_returns_none_on_failure(self):
        """POST devuelve None si todos los reintentos fallan."""
        with patch("scrapic.core.network.HAS_CLOUDSCRAPER", False):
            with patch("requests.post", side_effect=requests.exceptions.Timeout("Timeout")):
                with patch("time.sleep"):
                    result = NetworkManager.post("https://ejemplo.com", data={}, max_retries=2)

        assert result is None


class TestNetworkManagerProxies:

    def test_no_proxy_when_file_missing(self, tmp_path, monkeypatch):
        """Si no existe proxies.txt, _get_random_proxy devuelve None."""
        # Resetear el estado de carga de proxies para este test
        monkeypatch.setattr(NetworkManager, "_proxies_loaded", False)
        monkeypatch.setattr(NetworkManager, "_proxies_list", [])
        monkeypatch.chdir(tmp_path)  # Directorio sin proxies.txt

        proxy = NetworkManager._get_random_proxy()
        assert proxy is None

    def test_proxy_loaded_from_file(self, tmp_path, monkeypatch):
        """Los proxies se cargan correctamente desde proxies.txt."""
        proxy_file = tmp_path / "proxies.txt"
        proxy_file.write_text("192.168.1.1:8080\n10.0.0.1:3128\n# Este es un comentario\n")

        monkeypatch.setattr(NetworkManager, "_proxies_loaded", False)
        monkeypatch.setattr(NetworkManager, "_proxies_list", [])
        monkeypatch.chdir(tmp_path)

        NetworkManager._load_proxies()
        assert len(NetworkManager._proxies_list) == 2
        assert "192.168.1.1:8080" in NetworkManager._proxies_list
