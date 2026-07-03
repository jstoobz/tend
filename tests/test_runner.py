from tend import runner, store


def test_execute_run_writes_per_page_artifacts_and_page_summaries(tmp_path, monkeypatch):
    monkeypatch.setenv("TEND_HOME", str(tmp_path))
    monkeypatch.setattr(
        runner.crawl, "discover", lambda url, **kwargs: [url, f"{url}/about", f"{url}/about/team"]
    )
    ok = {"name": "onpage", "ok": True, "skipped": False, "detail": {}}
    fail = {"name": "onpage", "ok": False, "skipped": False, "detail": {}}
    results = {
        "https://example.com": [ok],
        "https://example.com/about": [fail],
        "https://example.com/about/team": [ok],
    }
    monkeypatch.setattr(runner, "run_all", lambda url: results[url])

    finalized = runner.execute_run(site_slug="bobs-bakery", url="https://example.com")

    run_dir = runner.runs_root("bobs-bakery") / finalized["run_id"]
    index = store.read_json(run_dir / "pages" / "index.json")
    about = store.read_json(run_dir / "pages" / "about.json")
    team = store.read_json(run_dir / "pages" / "about-team.json")
    assert index["url"] == "https://example.com"
    assert index["checks"] == [ok]
    assert about["checks"] == [fail]
    assert team["checks"] == [ok]
    assert finalized["checks"] == [ok]
    assert finalized["pages"] == [
        {"url": "https://example.com", "ok": True, "artifact": "pages/index.json"},
        {"url": "https://example.com/about", "ok": False, "artifact": "pages/about.json"},
        {"url": "https://example.com/about/team", "ok": True, "artifact": "pages/about-team.json"},
    ]


def test_execute_run_writes_manifest_last_with_check_results(tmp_path, monkeypatch):
    monkeypatch.setenv("TEND_HOME", str(tmp_path))
    monkeypatch.setattr(runner.crawl, "discover", lambda url, **kwargs: [url])
    canned = [{"name": "onpage", "ok": True, "skipped": False, "detail": {}}]
    monkeypatch.setattr(runner, "run_all", lambda url: canned)

    finalized = runner.execute_run(site_slug="bobs-bakery", url="https://example.com")

    run_dir = runner.runs_root("bobs-bakery") / finalized["run_id"]
    assert (run_dir / "manifest.json").exists()
    assert finalized["status"] == "complete"
    assert finalized["checks"] == canned


def test_execute_run_swaps_latest_symlink_to_new_run(tmp_path, monkeypatch):
    monkeypatch.setenv("TEND_HOME", str(tmp_path))
    monkeypatch.setattr(runner.crawl, "discover", lambda url, **kwargs: [url])
    monkeypatch.setattr(runner, "run_all", lambda url: [])

    finalized = runner.execute_run(site_slug="bobs-bakery", url="https://example.com")

    latest = runner.runs_root("bobs-bakery") / "latest"
    expected = runner.runs_root("bobs-bakery") / finalized["run_id"]
    assert latest.resolve() == expected.resolve()


def test_list_runs_excludes_dirs_without_a_manifest(tmp_path, monkeypatch):
    monkeypatch.setenv("TEND_HOME", str(tmp_path))
    monkeypatch.setattr(runner.crawl, "discover", lambda url, **kwargs: [url])
    monkeypatch.setattr(runner, "run_all", lambda url: [])
    finalized = runner.execute_run(site_slug="bobs-bakery", url="https://example.com")
    (runner.runs_root("bobs-bakery") / "20260101-000000-crashed").mkdir(parents=True)

    result = runner.list_runs("bobs-bakery")

    assert result == [finalized["run_id"]]


def test_list_runs_empty_for_untracked_site(tmp_path, monkeypatch):
    monkeypatch.setenv("TEND_HOME", str(tmp_path))

    assert runner.list_runs("never-tracked") == []
