import time
from collections import deque
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.request import urlopen


class _HrefCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        for name, value in attrs:
            if name == "href" and value:
                self.hrefs.append(value)


def _host_key(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def _normalize(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    normalized = f"{parsed.scheme}://{parsed.netloc}{path}"
    if parsed.query:
        normalized += f"?{parsed.query}"
    return normalized


def _page_key(url: str) -> str:
    parsed = urlparse(url)
    key = f"{_host_key(url)}{parsed.path.rstrip('/')}"
    if parsed.query:
        key += f"?{parsed.query}"
    return key


def _fetch(url: str) -> tuple[str, str] | None:
    try:
        with urlopen(url, timeout=10) as response:
            content_type = response.headers.get_content_type()
            return content_type, response.read().decode("utf-8", errors="replace")
    except OSError:
        return None


def _extract_hrefs(html: str) -> list[str]:
    collector = _HrefCollector()
    collector.feed(html)
    return collector.hrefs


def discover(
    url: str, *, max_pages: int = 25, max_depth: int = 2, delay_seconds: float = 0.5
) -> list[str]:
    origin = _host_key(url)
    root = _normalize(url)
    pages: list[str] = []
    queue = deque([(root, 0)])
    seen = {_page_key(root)}

    fetches = 0
    while queue and len(pages) < max_pages:
        page_url, depth = queue.popleft()
        is_root = not pages

        if fetches and delay_seconds > 0:
            time.sleep(delay_seconds)
        fetched = _fetch(page_url)
        fetches += 1
        if fetched is None:
            pages.append(page_url)  # checks will record the fetch failure per page
            continue
        content_type, html = fetched
        if content_type != "text/html" and not is_root:
            continue
        pages.append(page_url)

        if depth >= max_depth or content_type != "text/html":
            continue

        for href in _extract_hrefs(html):
            absolute = _normalize(urljoin(page_url, href))
            parsed = urlparse(absolute)
            if parsed.scheme not in ("http", "https"):
                continue
            if _host_key(absolute) != origin:
                continue
            key = _page_key(absolute)
            if key in seen:
                continue
            seen.add(key)
            queue.append((absolute, depth + 1))

    return pages
