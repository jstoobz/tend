from urllib.error import URLError

from tend import crawl


class _FakeHeaders:
    def __init__(self, content_type):
        self._content_type = content_type

    def get_content_type(self):
        return self._content_type


class _FakeResponse:
    def __init__(self, html, content_type="text/html"):
        self._html = html
        self.headers = _FakeHeaders(content_type)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._html.encode()


def _serve(monkeypatch, pages):
    """Fake crawl.urlopen from {url: html | (html, content_type) | Exception}."""

    def opener(url, timeout=0):
        entry = pages.get(url)
        if entry is None:
            raise URLError(f"no route: {url}")
        if isinstance(entry, Exception):
            raise entry
        if isinstance(entry, tuple):
            return _FakeResponse(*entry)
        return _FakeResponse(entry)

    monkeypatch.setattr(crawl, "urlopen", opener)


def test_discover_returns_only_the_root_when_it_has_no_links(monkeypatch):
    _serve(monkeypatch, {"https://site.example": "<html><body>hello</body></html>"})

    pages = crawl.discover("https://site.example", delay_seconds=0)

    assert pages == ["https://site.example"]


def test_discover_follows_same_origin_links_breadth_first(monkeypatch):
    _serve(
        monkeypatch,
        {
            "https://site.example": (
                '<a href="/about">about</a>'
                '<a href="https://site.example/contact">contact</a>'
                '<a href="https://elsewhere.example/off-site">external</a>'
                '<a href="mailto:bob@site.example">mail</a>'
                '<a href="tel:+15551234567">call</a>'
            ),
            "https://site.example/about": '<a href="/team">team</a>',
            "https://site.example/contact": "<p>no links</p>",
            "https://site.example/team": "<p>leaf</p>",
        },
    )

    pages = crawl.discover("https://site.example", delay_seconds=0)

    assert pages == [
        "https://site.example",
        "https://site.example/about",
        "https://site.example/contact",
        "https://site.example/team",
    ]


def test_discover_stops_following_links_at_max_depth(monkeypatch):
    _serve(
        monkeypatch,
        {
            "https://site.example": '<a href="/depth-one">one</a>',
            "https://site.example/depth-one": '<a href="/depth-two">two</a>',
            "https://site.example/depth-two": "<p>too deep</p>",
        },
    )

    pages = crawl.discover("https://site.example", max_depth=1, delay_seconds=0)

    assert pages == ["https://site.example", "https://site.example/depth-one"]


def test_discover_stops_collecting_at_max_pages(monkeypatch):
    _serve(
        monkeypatch,
        {
            "https://site.example": (
                '<a href="/a">a</a><a href="/b">b</a><a href="/c">c</a><a href="/d">d</a>'
            ),
            "https://site.example/a": "<p>a</p>",
            "https://site.example/b": "<p>b</p>",
            "https://site.example/c": "<p>c</p>",
            "https://site.example/d": "<p>d</p>",
        },
    )

    pages = crawl.discover("https://site.example", max_pages=3, delay_seconds=0)

    assert pages == [
        "https://site.example",
        "https://site.example/a",
        "https://site.example/b",
    ]


def test_discover_keeps_unreachable_pages_so_checks_can_record_the_failure(monkeypatch):
    _serve(
        monkeypatch,
        {
            "https://site.example": '<a href="/broken">broken</a>',
        },
    )

    pages = crawl.discover("https://site.example", delay_seconds=0)

    assert pages == ["https://site.example", "https://site.example/broken"]


def test_discover_excludes_non_html_targets_from_pages(monkeypatch):
    _serve(
        monkeypatch,
        {
            "https://site.example": '<a href="/brochure.pdf">pdf</a><a href="/about">about</a>',
            "https://site.example/brochure.pdf": ("%PDF-1.7", "application/pdf"),
            "https://site.example/about": "<p>about</p>",
        },
    )

    pages = crawl.discover("https://site.example", delay_seconds=0)

    assert pages == ["https://site.example", "https://site.example/about"]


def test_discover_sleeps_between_fetches_but_not_before_the_first(monkeypatch):
    _serve(
        monkeypatch,
        {
            "https://site.example": '<a href="/a">a</a><a href="/b">b</a>',
            "https://site.example/a": "<p>a</p>",
            "https://site.example/b": "<p>b</p>",
        },
    )
    sleeps = []
    monkeypatch.setattr(crawl.time, "sleep", sleeps.append)

    crawl.discover("https://site.example", delay_seconds=0.25)

    assert sleeps == [0.25, 0.25]


def test_discover_treats_www_and_apex_as_the_same_origin_and_page(monkeypatch):
    _serve(
        monkeypatch,
        {
            "https://site.example": (
                '<a href="https://www.site.example/about">www form</a><a href="/about">apex</a>'
            ),
            "https://www.site.example/about": "<p>about</p>",
        },
    )

    pages = crawl.discover("https://site.example", delay_seconds=0)

    assert pages == ["https://site.example", "https://www.site.example/about"]


def test_discover_dedupes_fragment_and_trailing_slash_variants(monkeypatch):
    _serve(
        monkeypatch,
        {
            "https://site.example": (
                '<a href="/about">a</a><a href="/about/">b</a><a href="/about#team">c</a>'
                '<a href="/pricing?plan=starter">d</a><a href="/pricing">e</a>'
            ),
            "https://site.example/about": "<p>about</p>",
            "https://site.example/pricing?plan=starter": "<p>starter</p>",
            "https://site.example/pricing": "<p>pricing</p>",
        },
    )

    pages = crawl.discover("https://site.example", delay_seconds=0)

    assert pages == [
        "https://site.example",
        "https://site.example/about",
        "https://site.example/pricing?plan=starter",
        "https://site.example/pricing",
    ]
