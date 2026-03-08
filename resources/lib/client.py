import ssl
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .constants import DEFAULT_HEADERS, REQUEST_TIMEOUT


class HttpClient:
    def __init__(self):
        # Kodi on some systems can fail strict TLS validation depending on bundled certs.
        # Keep default verification first, and fallback to unverified context only on TLS errors.
        self._default_ssl_context = ssl.create_default_context()
        self._fallback_ssl_context = ssl._create_unverified_context()

    def get_text(self, url, referer=None):
        headers = dict(DEFAULT_HEADERS)
        if referer:
            headers["Referer"] = referer

        request = Request(url=url, headers=headers, method="GET")
        try:
            return self._read_response(request, self._default_ssl_context)
        except URLError:
            # Retry once with relaxed TLS context for Kodi/device cert edge-cases.
            return self._read_response(request, self._fallback_ssl_context)

    @staticmethod
    def _read_response(request, context):
        try:
            with urlopen(request, timeout=REQUEST_TIMEOUT, context=context) as response:
                content_type = response.headers.get_content_charset() or "utf-8"
                raw = response.read()
                return raw.decode(content_type, errors="replace")
        except HTTPError as exc:
            # Keep message explicit for Kodi log readability.
            raise RuntimeError(f"HTTP {exc.code} while requesting {request.full_url}")
