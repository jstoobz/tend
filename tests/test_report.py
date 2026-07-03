from tend import report


def test_render_run_includes_run_id_site_and_status():
    manifest = {
        "run_id": "20260702-070000-abc123",
        "site_slug": "bobs-bakery",
        "status": "complete",
        "checks": [],
    }

    rendered = report.render_run(manifest)

    assert "20260702-070000-abc123" in rendered
    assert "bobs-bakery" in rendered
    assert "complete" in rendered


def test_render_run_marks_each_check_ok_fail_or_skipped():
    manifest = {
        "run_id": "r1",
        "site_slug": "bobs-bakery",
        "status": "complete",
        "checks": [
            {"name": "onpage", "ok": True, "skipped": False, "detail": {}},
            {"name": "links", "ok": True, "skipped": True, "detail": {}},
            {"name": "broken", "ok": False, "skipped": False, "detail": {}},
        ],
    }

    rendered = report.render_run(manifest)

    assert "[OK] onpage" in rendered
    assert "[SKIPPED] links" in rendered
    assert "[FAIL] broken" in rendered


def test_render_run_lists_pages_when_present():
    manifest = {
        "run_id": "r1",
        "site_slug": "bobs-bakery",
        "status": "complete",
        "checks": [{"name": "onpage", "ok": True, "skipped": False, "detail": {}}],
        "pages": [
            {"url": "https://example.com", "ok": True, "artifact": "pages/index.json"},
            {"url": "https://example.com/about", "ok": False, "artifact": "pages/about.json"},
        ],
    }

    rendered = report.render_run(manifest)

    assert "pages (2):" in rendered
    assert "[OK] https://example.com" in rendered
    assert "[FAIL] https://example.com/about" in rendered


def test_render_run_handles_v1_manifests_without_pages():
    manifest = {
        "run_id": "r1",
        "site_slug": "bobs-bakery",
        "status": "complete",
        "checks": [{"name": "onpage", "ok": True, "skipped": False, "detail": {}}],
    }

    rendered = report.render_run(manifest)

    assert "pages" not in rendered
    assert "[OK] onpage" in rendered
