import json

from typer.testing import CliRunner

from tend import __version__, runner
from tend.cli import app

cli = CliRunner()

_ONPAGE_OK = {"name": "onpage", "ok": True, "skipped": False, "detail": {}}
_ONPAGE_FAIL = {"name": "onpage", "ok": False, "skipped": False, "detail": {}}


def test_version_prints_version_string():
    result = cli.invoke(app, ["version"])

    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_track_creates_a_site(tmp_path, monkeypatch):
    monkeypatch.setenv("TEND_HOME", str(tmp_path))

    result = cli.invoke(app, ["track", "Bob's Bakery", "https://example.com"])

    assert result.exit_code == 0
    assert "bobs-bakery" in result.stdout


def test_sites_lists_tracked_sites_as_json(tmp_path, monkeypatch):
    monkeypatch.setenv("TEND_HOME", str(tmp_path))
    cli.invoke(app, ["track", "Bob's Bakery", "https://example.com"])

    result = cli.invoke(app, ["sites", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload[0]["slug"] == "bobs-bakery"


def test_check_errors_on_unknown_site(tmp_path, monkeypatch):
    monkeypatch.setenv("TEND_HOME", str(tmp_path))

    result = cli.invoke(app, ["check", "unknown-site"])

    assert result.exit_code == 1


def test_check_runs_a_site_and_show_reports_latest(tmp_path, monkeypatch):
    monkeypatch.setenv("TEND_HOME", str(tmp_path))
    monkeypatch.setattr(runner.crawl, "discover", lambda url, **kwargs: [url])
    monkeypatch.setattr(runner, "run_all", lambda url: [_ONPAGE_OK])
    cli.invoke(app, ["track", "Bob's Bakery", "https://example.com"])

    check_result = cli.invoke(app, ["check", "bobs-bakery"])
    show_result = cli.invoke(app, ["show", "bobs-bakery"])

    assert check_result.exit_code == 0
    assert show_result.exit_code == 0
    assert "onpage" in show_result.stdout


def test_show_and_report_accept_positional_run_id(tmp_path, monkeypatch):
    monkeypatch.setenv("TEND_HOME", str(tmp_path))
    monkeypatch.setattr(runner.crawl, "discover", lambda url, **kwargs: [url])
    monkeypatch.setattr(runner, "run_all", lambda url: [_ONPAGE_OK])
    cli.invoke(app, ["track", "Bob's Bakery", "https://example.com"])
    cli.invoke(app, ["check", "bobs-bakery"])
    run_id = runner.list_runs("bobs-bakery")[0]

    show_result = cli.invoke(app, ["show", "bobs-bakery", run_id])
    report_result = cli.invoke(app, ["report", "bobs-bakery", run_id])

    assert show_result.exit_code == 0
    assert run_id in show_result.stdout
    assert report_result.exit_code == 0
    assert run_id in report_result.stdout


def test_runs_lists_run_ids_after_check(tmp_path, monkeypatch):
    monkeypatch.setenv("TEND_HOME", str(tmp_path))
    monkeypatch.setattr(runner.crawl, "discover", lambda url, **kwargs: [url])
    monkeypatch.setattr(runner, "run_all", lambda url: [])
    cli.invoke(app, ["track", "Bob's Bakery", "https://example.com"])
    cli.invoke(app, ["check", "bobs-bakery"])

    result = cli.invoke(app, ["runs", "bobs-bakery", "--json"])

    assert result.exit_code == 0
    assert len(json.loads(result.stdout)) == 1


def test_diff_reports_between_two_runs(tmp_path, monkeypatch):
    monkeypatch.setenv("TEND_HOME", str(tmp_path))
    monkeypatch.setattr(runner.crawl, "discover", lambda url, **kwargs: [url])
    monkeypatch.setattr(runner, "run_all", lambda url: [_ONPAGE_OK])
    cli.invoke(app, ["track", "Bob's Bakery", "https://example.com"])
    cli.invoke(app, ["check", "bobs-bakery"])
    monkeypatch.setattr(runner.crawl, "discover", lambda url, **kwargs: [url])
    monkeypatch.setattr(runner, "run_all", lambda url: [_ONPAGE_FAIL])
    cli.invoke(app, ["check", "bobs-bakery"])
    run_ids = runner.list_runs("bobs-bakery")

    result = cli.invoke(app, ["diff", "bobs-bakery", run_ids[0], run_ids[1]])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["changed"][0]["name"] == "onpage"


def test_diff_errors_cleanly_on_unknown_run_id(tmp_path, monkeypatch):
    monkeypatch.setenv("TEND_HOME", str(tmp_path))
    cli.invoke(app, ["track", "Bob's Bakery", "https://example.com"])

    result = cli.invoke(app, ["diff", "bobs-bakery", "nope-a", "nope-b"])

    assert result.exit_code == 1
    assert not isinstance(result.exception, FileNotFoundError)
    assert "no run 'nope-a'" in result.stderr


def test_error_messages_go_to_stderr_leaving_stdout_clean(tmp_path, monkeypatch):
    monkeypatch.setenv("TEND_HOME", str(tmp_path))

    result = cli.invoke(app, ["show", "ghost-site", "--json"])

    assert result.exit_code == 1
    assert result.stdout == ""
    assert "no run 'latest' for site 'ghost-site'" in result.stderr


def test_doctor_reports_resolved_paths_as_json(tmp_path, monkeypatch):
    monkeypatch.setenv("TEND_HOME", str(tmp_path))

    result = cli.invoke(app, ["doctor", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["data_dir"] == str(tmp_path / "data")
