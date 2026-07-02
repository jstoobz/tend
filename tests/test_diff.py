from tend import diff, store


def _write_manifest(tmp_path, name, run_id, checks):
    run_dir = tmp_path / name
    run_dir.mkdir()
    store.atomic_write_json(run_dir / "manifest.json", {"run_id": run_id, "checks": checks})
    return run_dir


def test_diff_runs_reports_unchanged_when_identical(tmp_path):
    checks = [{"name": "onpage", "ok": True, "detail": {}}]
    run_a = _write_manifest(tmp_path, "a", "run-a", checks)
    run_b = _write_manifest(tmp_path, "b", "run-b", checks)

    result = diff.diff_runs(run_a, run_b)

    assert result["unchanged"] == ["onpage"]
    assert result["changed"] == []
    assert result["added_checks"] == []
    assert result["removed_checks"] == []


def test_diff_runs_reports_changed_result_for_same_check(tmp_path):
    run_a = _write_manifest(tmp_path, "a", "run-a", [{"name": "onpage", "ok": True, "detail": {}}])
    run_b = _write_manifest(tmp_path, "b", "run-b", [{"name": "onpage", "ok": False, "detail": {}}])

    result = diff.diff_runs(run_a, run_b)

    assert result["changed"] == [
        {
            "name": "onpage",
            "before": {"name": "onpage", "ok": True, "detail": {}},
            "after": {"name": "onpage", "ok": False, "detail": {}},
        }
    ]


def test_diff_runs_reports_added_and_removed_checks(tmp_path):
    run_a = _write_manifest(tmp_path, "a", "run-a", [{"name": "onpage", "ok": True, "detail": {}}])
    run_b = _write_manifest(tmp_path, "b", "run-b", [{"name": "links", "ok": True, "detail": {}}])

    result = diff.diff_runs(run_a, run_b)

    assert result["added_checks"] == ["links"]
    assert result["removed_checks"] == ["onpage"]
