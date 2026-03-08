from urllib.parse import parse_qsl, quote_plus, urlencode

from .constants import DEFAULT_HEADERS, SITE_ROOT
from .scraper import StarDimaScraper

try:
    import xbmc
    import xbmcgui
    import xbmcplugin
except ImportError:  # Local/dev fallback
    xbmc = xbmcgui = xbmcplugin = None


class PluginRouter:
    def __init__(self, handle):
        self.handle = handle
        self.scraper = StarDimaScraper()

    def dispatch(self, params):
        action = params.get("action")
        if action == "episodes":
            return self.show_episodes(params.get("slug", ""))
        if action == "play":
            return self.play(params.get("url", ""))
        return self.show_home()

    def show_home(self):
        try:
            shows = self.scraper.list_shows()
        except Exception as exc:
            self._notify(f"خطأ أثناء تحميل القائمة: {exc}", xbmcgui.NOTIFICATION_ERROR)
            xbmcplugin.endOfDirectory(self.handle, succeeded=False)
            return

        if not shows:
            self._notify("لم يتم العثور على محتوى في الصفحة الرئيسية", xbmcgui.NOTIFICATION_WARNING)
            xbmcplugin.endOfDirectory(self.handle, succeeded=False)
            return

        for show in shows:
            target = self._build_url({"action": "episodes", "slug": show["slug"]})
            li = xbmcgui.ListItem(label=show["title"])
            li.setArt({"thumb": show["thumb"], "icon": show["thumb"], "poster": show["thumb"]})
            xbmcplugin.addDirectoryItem(self.handle, target, li, isFolder=True)

        xbmcplugin.endOfDirectory(self.handle)

    def show_episodes(self, slug):
        if not slug:
            xbmcplugin.endOfDirectory(self.handle, succeeded=False)
            return

        try:
            episodes = self.scraper.list_episodes(slug)
        except Exception as exc:
            self._notify(f"خطأ أثناء تحميل الحلقات: {exc}", xbmcgui.NOTIFICATION_ERROR)
            xbmcplugin.endOfDirectory(self.handle, succeeded=False)
            return

        if not episodes:
            self._notify("لا توجد حلقات متاحة حالياً", xbmcgui.NOTIFICATION_WARNING)
            xbmcplugin.endOfDirectory(self.handle, succeeded=False)
            return

        for ep in episodes:
            target = self._build_url({"action": "play", "url": ep["url"]})
            li = xbmcgui.ListItem(label=ep["title"])
            li.setInfo("video", {"title": ep["title"], "season": ep["season"], "episode": ep["episode"]})
            xbmcplugin.addDirectoryItem(self.handle, target, li, isFolder=False)

        xbmcplugin.endOfDirectory(self.handle)

    def play(self, episode_url):
        try:
            stream_url = self.scraper.extract_stream_url(episode_url)
        except Exception as exc:
            self._notify(f"خطأ أثناء استخراج رابط التشغيل: {exc}", xbmcgui.NOTIFICATION_ERROR)
            xbmcplugin.setResolvedUrl(self.handle, False, xbmcgui.ListItem())
            return

        if not stream_url:
            self._notify("تعذر استخراج رابط التشغيل", xbmcgui.NOTIFICATION_ERROR)
            xbmcplugin.setResolvedUrl(self.handle, False, xbmcgui.ListItem())
            return

        header_string = urlencode(
            {
                "Referer": episode_url or (SITE_ROOT + "/"),
                "User-Agent": DEFAULT_HEADERS["User-Agent"],
            },
            quote_via=quote_plus,
        )
        playable = f"{stream_url}|{header_string}"
        item = xbmcgui.ListItem(path=playable)
        item.setProperty("IsPlayable", "true")
        xbmcplugin.setResolvedUrl(self.handle, True, item)

    @staticmethod
    def _build_url(query):
        return f"plugin://plugin.video.stardima/?{urlencode(query)}"

    @staticmethod
    def _notify(message, level):
        xbmcgui.Dialog().notification("StarDima", message, level)


def run():
    if xbmc is None:
        raise RuntimeError("This addon must run inside Kodi.")

    import sys

    handle = int(sys.argv[1])
    params = dict(parse_qsl(sys.argv[2].lstrip("?")))
    router = PluginRouter(handle)
    router.dispatch(params)
