import re
from urllib.request import urlopen

_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_META_DESCRIPTION_RE = re.compile(r'<meta[^>]+name=["\']description["\']', re.IGNORECASE)


def run(url: str) -> dict:
    try:
        with urlopen(url, timeout=10) as response:
            html = response.read().decode("utf-8", errors="replace")
    except OSError as exc:
        return {"name": "onpage", "ok": False, "skipped": False, "detail": {"error": str(exc)}}

    title_match = _TITLE_RE.search(html)
    title = title_match.group(1).strip() if title_match else None
    has_meta_description = bool(_META_DESCRIPTION_RE.search(html))

    return {
        "name": "onpage",
        "ok": title is not None,
        "skipped": False,
        "detail": {"title": title, "has_meta_description": has_meta_description},
    }
