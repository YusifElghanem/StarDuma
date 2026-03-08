import base64
import re
from urllib.parse import parse_qs, unquote, urljoin, urlparse

from .client import HttpClient
from .constants import BASE_URL, TVSHOWS_URL

_SHOW_LINK_RE = re.compile(r'href=["\'](?P<href>/watch/tvshows/(?P<slug>[^"\'/]+)/?)["\']')
_TITLE_RE = re.compile(r'title=["\']([^"\']+)["\']')
_IMG_RE = re.compile(r'(?:data-src|src)=["\']([^"\']+)["\']')
_EP_LINK_RE = re.compile(r'href=["\'](?P<href>/watch/episodes/(?P<slug>[^"\']+)-(?P<season>\d+)-(?P<ep>\d+)/?)["\']')
_IFRAME_RE = re.compile(r'<iframe[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)


class StarDimaScraper:
    def __init__(self):
        self.client = HttpClient()

    def list_shows(self):
        html = self.client.get_text(TVSHOWS_URL, referer=BASE_URL)
        items = []
        seen = set()

        for match in _SHOW_LINK_RE.finditer(html):
            slug = match.group("slug")
            href = urljoin(BASE_URL, match.group("href"))
            if slug in seen:
                continue

            start = max(0, match.start() - 500)
            end = min(len(html), match.end() + 500)
            snippet = html[start:end]

            title_match = _TITLE_RE.search(snippet)
            img_match = _IMG_RE.search(snippet)
            title = title_match.group(1).strip() if title_match else slug.replace("-", " ").title()
            thumb = img_match.group(1).replace("/w500", "/w185") if img_match else ""

            items.append({"title": title, "slug": slug, "url": href, "thumb": thumb})
            seen.add(slug)

        return items

    def list_episodes(self, show_slug):
        show_url = f"{TVSHOWS_URL}{show_slug}/"
        html = self.client.get_text(show_url, referer=TVSHOWS_URL)

        episodes = []
        seen = set()
        for match in _EP_LINK_RE.finditer(html):
            href = urljoin(BASE_URL, match.group("href"))
            season = int(match.group("season"))
            episode = int(match.group("ep"))
            key = (season, episode, href)
            if key in seen:
                continue
            episodes.append(
                {
                    "title": f"S{season:02d}E{episode:02d}",
                    "season": season,
                    "episode": episode,
                    "url": href,
                }
            )
            seen.add(key)

        episodes.sort(key=lambda x: (x["season"], x["episode"]))
        return episodes

    def extract_stream_url(self, episode_url):
        html = self.client.get_text(episode_url, referer=BASE_URL)
        match = _IFRAME_RE.search(html)
        if not match:
            return ""

        iframe_url = unquote(match.group(1))
        return self._resolve_redirect(iframe_url)

    def _resolve_redirect(self, url):
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        redirect_raw = query.get("redirect", [""])[0]
        if not redirect_raw:
            return url

        try:
            padded = redirect_raw + "=" * (-len(redirect_raw) % 4)
            decoded = base64.b64decode(padded).decode("utf-8", errors="ignore").strip()
            return decoded or url
        except Exception:
            return url
