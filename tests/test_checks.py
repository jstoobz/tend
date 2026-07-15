import json

from tend.checks import CHECK_REGISTRY, links, onpage, run_all


def test_onpage_extracts_title_and_meta_description(monkeypatch):
    html = b"""
    <html><head>
      <title>Bob's Bakery</title>
      <meta name="description" content="Fresh bread daily">
    </head><body></body></html>
    """

    class _FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return html

    monkeypatch.setattr(onpage, "urlopen", lambda url, timeout: _FakeResponse())

    result = onpage.run("https://example.com")

    assert result["name"] == "onpage"
    assert result["ok"] is True
    assert result["skipped"] is False
    assert result["detail"]["title"] == "Bob's Bakery"
    assert result["detail"]["has_meta_description"] is True


def test_onpage_handles_fetch_failure_without_raising(monkeypatch):
    def _boom(url, timeout):
        raise OSError("connection refused")

    monkeypatch.setattr(onpage, "urlopen", _boom)

    result = onpage.run("https://example.com")

    assert result["ok"] is False
    assert result["skipped"] is False
    assert "error" in result["detail"]


def test_links_check_skips_when_tool_absent(monkeypatch):
    monkeypatch.setattr(links.shutil, "which", lambda name: None)

    result = links.run("https://example.com")

    assert result["name"] == "links"
    assert result["skipped"] is True
    assert result["ok"] is True


def test_links_check_runs_tool_when_present(monkeypatch):
    monkeypatch.setattr(links.shutil, "which", lambda name: "/usr/local/bin/lychee")

    class _FakeCompleted:
        returncode = 0
        stdout = '{"error_map": {}}'

    monkeypatch.setattr(links.subprocess, "run", lambda *a, **k: _FakeCompleted())

    result = links.run("https://example.com")

    assert result["skipped"] is False
    assert result["ok"] is True


def test_links_check_strips_volatile_duration_fields(monkeypatch):
    monkeypatch.setattr(links.shutil, "which", lambda name: "/opt/homebrew/bin/lychee")

    real_shaped_output = {
        "total": 2,
        "errors": 1,
        "error_map": {
            "https://site.example": [
                {
                    "url": "https://site.example/broken",
                    "status": {"text": "Rejected status code: 404 Not Found", "code": 404},
                    "span": {"line": 1, "column": 76},
                    "duration": {"secs": 0, "nanos": 569811875},
                }
            ]
        },
        "duration": {"secs": 0, "nanos": 770958625},
    }

    class _FakeCompleted:
        returncode = 2
        stdout = json.dumps(real_shaped_output)
        stderr = ""

    monkeypatch.setattr(links.subprocess, "run", lambda *a, **k: _FakeCompleted())

    result = links.run("https://site.example")

    output = result["detail"]["output"]
    assert "duration" not in output
    broken = output["error_map"]["https://site.example"][0]
    assert "duration" not in broken
    assert broken["status"]["code"] == 404
    assert broken["span"] == {"line": 1, "column": 76}
    assert output["total"] == 2


def test_links_check_orders_link_map_entries_deterministically(monkeypatch):
    monkeypatch.setattr(links.shutil, "which", lambda name: "/opt/homebrew/bin/lychee")

    real_shaped_output = {
        "total": 4,
        "errors": 2,
        "error_map": {
            "https://site.example": [
                {
                    "url": "https://site.example/broken",
                    "status": {"text": "Rejected status code: 404 Not Found", "code": 404},
                    "span": {"line": 9, "column": 1},
                },
                {
                    "url": "https://site.example/broken",
                    "status": {"text": "Rejected status code: 404 Not Found", "code": 404},
                    "span": {"line": 2, "column": 5},
                },
            ]
        },
        "excluded_map": {
            "https://site.example": [
                {
                    "url": "tel:5551234",
                    "status": {
                        "text": "Excluded",
                        "details": "This is due to your 'exclude' values",
                    },
                    "span": {"line": 556, "column": 21},
                },
                {
                    "url": "mailto:owner@site.example",
                    "status": {
                        "text": "Excluded",
                        "details": "This is due to your 'exclude' values",
                    },
                    "span": {"line": 550, "column": 21},
                },
            ]
        },
    }

    class _FakeCompleted:
        returncode = 2
        stdout = json.dumps(real_shaped_output)
        stderr = ""

    monkeypatch.setattr(links.subprocess, "run", lambda *a, **k: _FakeCompleted())

    result = links.run("https://site.example")

    output = result["detail"]["output"]
    excluded = output["excluded_map"]["https://site.example"]
    assert [e["url"] for e in excluded] == ["mailto:owner@site.example", "tel:5551234"]
    errors = output["error_map"]["https://site.example"]
    assert [e["span"]["line"] for e in errors] == [2, 9]


def test_links_check_keeps_stderr_when_tool_fails(monkeypatch):
    monkeypatch.setattr(links.shutil, "which", lambda name: "/opt/homebrew/bin/lychee")

    class _FakeCompleted:
        returncode = 1
        stdout = ""
        stderr = "error: network failure\n"

    monkeypatch.setattr(links.subprocess, "run", lambda *a, **k: _FakeCompleted())

    result = links.run("https://site.example")

    assert result["ok"] is False
    assert result["detail"]["stderr"] == "error: network failure"


def test_run_all_returns_one_result_per_registered_check(monkeypatch):
    monkeypatch.setattr(
        onpage, "run", lambda url: {"name": "onpage", "ok": True, "skipped": False, "detail": {}}
    )
    monkeypatch.setattr(
        links, "run", lambda url: {"name": "links", "ok": True, "skipped": True, "detail": {}}
    )

    results = run_all("https://example.com")

    assert len(results) == len(CHECK_REGISTRY)
    assert {r["name"] for r in results} == {"onpage", "links"}


def test_run_all_isolates_a_check_that_raises(monkeypatch):
    def _boom(url):
        raise TimeoutError("lychee timed out")

    monkeypatch.setattr(
        onpage, "run", lambda url: {"name": "onpage", "ok": True, "skipped": False, "detail": {}}
    )
    monkeypatch.setattr(links, "run", _boom)

    results = run_all("https://example.com")

    by_name = {r["name"]: r for r in results}
    assert by_name["onpage"]["ok"] is True
    assert by_name["links"]["ok"] is False
    assert by_name["links"]["skipped"] is False
    assert "error" in by_name["links"]["detail"]
