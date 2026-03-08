import requests

from .constants import DEFAULT_HEADERS, REQUEST_TIMEOUT


class HttpClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def get_text(self, url, referer=None):
        headers = {}
        if referer:
            headers["Referer"] = referer
        response = self.session.get(url, timeout=REQUEST_TIMEOUT, headers=headers)
        response.raise_for_status()
        return response.text
