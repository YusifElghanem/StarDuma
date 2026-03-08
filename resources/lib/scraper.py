import base64
import re
from html import unescape
from urllib.parse import parse_qs, unquote, urljoin, urlparse

from .client import HttpClient
from .constants import SITE_ROOT

_TVSHOW_LINK_RE = re.compile(
    r'href=["\'](?P<href>(?:https?://[^"\']+)?/(?:(?:watch/)?tvshows|tvshow)/(?P<slug>[^"\'/\?#]+)/?[^"\']*)["\']',
    re.IGNORECASE,
)
_TITLE_ATTR_RE = re.compile(r'title=["\']([^"\']+)["\']', re.IGNORECASE)
_IMG_RE = re.compile(r'(?:data-src|src)=["\']([^"\']+)["\']', re.IGNORECASE)
_PLAY_LINK_RE = re.compile(
    r'href=["\'](?P<href>(?:https?://[^"\']+)?/(?:watch/episodes/[^"\']+|tvshow/[^"\']*/play/\d+|play/\d+))/?["\']',
    re.IGNORECASE,
)
_EPISODE_LINK_RE = re.compile(
    r'href=["\'](?P<href>(?:https?://[^"\']+)?/(?:(?:watch/episodes/(?P<newslug>[^"\']+)-(?P<season>\d+)-(?P<epnum>\d+))|(?:tvshow/(?P<oldslug>[^"\']*)/play/(?P<epid>\d+))|(?:play/(?P<epid2>\d+))))/?["\']',
    re.IGNORECASE,
)
_IFRAME_RE = re.compile(r'<iframe[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)
_TEXT_RE = re.compile(r">([^<]+)<")


class StarDimaScraper:
    def __init__(self):
        self.client = HttpClient()

    def list_shows(self):
        html = self.client.get_text(SITE_ROOT + "/", referer=SITE_ROOT + "/")
        items = []
        seen = set()

        for match in _TVSHOW_LINK_RE.finditer(html):
            slug = (match.group("slug") or "").strip(" /")
            if not slug or slug in seen or slug.lower() == "undefined":
                continue

            href = urljoin(SITE_ROOT + "/", match.group("href"))
            snippet = self._anchor_snippet(html, match.start(), match.end())

            title = self._extract_title(snippet, fallback=slug.replace("-", " "))
            thumb = self._extract_thumb(snippet)

            items.append({"title": title, "slug": slug, "url": href, "thumb": thumb})
            seen.add(slug)

        return items

    def list_episodes(self, slug):
        show_url = self._show_url(slug)
        show_html = self.client.get_text(show_url, referer=SITE_ROOT + "/")

        play_url = self._extract_first_play_link(show_html, show_url)
        html_candidates = [show_html]
        if play_url:
            try:
                html_candidates.insert(0, self.client.get_text(play_url, referer=show_url))
            except Exception:
                pass

        episodes = []
        seen = set()
        for html in html_candidates:
            for match in _EPISODE_LINK_RE.finditer(html):
                href = self._normalize_episode_url(match, slug)
                if not href or href in seen:
                    continue

                title = self._extract_episode_title(html, match.start(), match.end(), href)
                season = self._safe_int(match.group("season"), default=1)
                epnum = self._safe_int(match.group("epnum"), default=len(episodes) + 1)

                episodes.append(
                    {
                        "title": title,
                        "season": season,
                        "episode": epnum,
                        "url": href,
                    }
                )
                seen.add(href)

        episodes.sort(key=lambda x: (x["season"], x["episode"], x["title"]))
        return episodes

    def extract_stream_url(self, episode_url):
        html = self.client.get_text(episode_url, referer=SITE_ROOT + "/")
        match = _IFRAME_RE.search(html)
        if not match:
            return ""

        iframe_url = unquote(match.group(1))
        return self._resolve_redirect(iframe_url)

    def _extract_first_play_link(self, html, referer_url):
        match = _PLAY_LINK_RE.search(html)
        if not match:
            return ""
        return urljoin(referer_url, match.group("href"))

    def _normalize_episode_url(self, match, fallback_slug):
        href = match.group("href")
        if not href:
            return ""

        normalized = urljoin(SITE_ROOT + "/", href)
        if "/tvshow/undefined/play/" in normalized:
            episode_id = match.group("epid") or match.group("epid2")
            if not episode_id:
                return ""
            return f"{SITE_ROOT}/tvshow/{fallback_slug}/play/{episode_id}"

        if normalized.endswith("/play/"):
            return ""

        return normalized


    @staticmethod
    def _anchor_snippet(html, start, end):
        a_start = html.rfind("<a", 0, start)
        a_end = html.find("</a>", end)
        if a_start == -1 or a_end == -1:
            a_start = max(0, start - 350)
            a_end = min(len(html), end + 350)
        else:
            a_end += 4
        return html[a_start:a_end]

    @staticmethod
    def _extract_title(snippet, fallback):
        title_match = _TITLE_ATTR_RE.search(snippet)
        if title_match:
            return unescape(title_match.group(1)).strip()

        text_match = _TEXT_RE.search(snippet)
        if text_match:
            text = unescape(text_match.group(1)).strip()
            if text:
                return text

        return fallback.strip().title()

    @staticmethod
    def _extract_thumb(snippet):
        img_match = _IMG_RE.search(snippet)
        if not img_match:
            return ""
        return unescape(img_match.group(1)).replace("/w500", "/w185")

    @staticmethod
    def _safe_int(value, default=1):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _extract_episode_title(html, start, end, href):
        snippet = StarDimaScraper._anchor_snippet(html, start, end)
        title_match = _TITLE_ATTR_RE.search(snippet)
        if title_match:
            return unescape(title_match.group(1)).strip()

        text_match = _TEXT_RE.search(snippet)
        if text_match:
            text = unescape(text_match.group(1)).strip()
            if text:
                return text

        return href.rstrip("/").split("/")[-1]

    @staticmethod
    def _show_url(slug):
        return f"{SITE_ROOT}/tvshow/{slug}/"

    @staticmethod
    def _resolve_redirect(url):
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
