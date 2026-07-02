from tend import runner


def test_execute_run_writes_manifest_last_with_check_results(tmp_path, monkeypatch):
    monkeypatch.setenv("TEND_HOME", str(tmp_path))
    canned = [{"name": "onpage", "ok": True, "skipped": False, "detail": {}}]
    monkeypatch.setattr(runner, "run_all", lambda url: canned)

    finalized = runner.execute_run(site_slug="bobs-bakery", url="https://example.com")

    run_dir = runner.runs_root("bobs-bakery") / finalized["run_id"]
    assert (run_dir / "manifest.json").exists()
    assert finalized["status"] == "complete"
    assert finalized["checks"] == canned


def test_execute_run_swaps_latest_symlink_to_new_run(tmp_path, monkeypatch):
    monkeypatch.setenv("TEND_HOME", str(tmp_path))
    monkeypatch.setattr(runner, "run_all", lambda url: [])

    finalized = runner.execute_run(site_slug="bobs-bakery", url="https://example.com")

    latest = runner.runs_root("bobs-bakery") / "latest"
    expected = runner.runs_root("bobs-bakery") / finalized["run_id"]
    assert latest.resolve() == expected.resolve()


def test_list_runs_excludes_dirs_without_a_manifest(tmp_path, monkeypatch):
    monkeypatch.setenv("TEND_HOME", str(tmp_path))
    monkeypatch.setattr(runner, "run_all", lambda url: [])
    finalized = runner.execute_run(site_slug="bobs-bakery", url="https://example.com")
    (runner.runs_root("bobs-bakery") / "20260101-000000-crashed").mkdir(parents=True)

    result = runner.list_runs("bobs-bakery")

    assert result == [finalized["run_id"]]


def test_list_runs_empty_for_untracked_site(tmp_path, monkeypatch):
    monkeypatch.setenv("TEND_HOME", str(tmp_path))

    assert runner.list_runs("never-tracked") == []
