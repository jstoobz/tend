import json
import shutil
import sys

import typer

from tend import __version__, diff, paths, report, runner, sites, store

app = typer.Typer(add_completion=False, no_args_is_help=True)


def _emit_json(data) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


@app.command()
def version() -> None:
    """Print the installed tend version."""
    print(__version__)


@app.command()
def track(name: str, url: str, json_out: bool = typer.Option(False, "--json")) -> None:
    """Start tracking a site."""
    record = sites.track(name=name, url=url)
    if json_out:
        _emit_json(record)
    else:
        print(f"tracking {record['slug']} ({record['url']})")


@app.command(name="sites")
def sites_command(json_out: bool = typer.Option(False, "--json")) -> None:
    """List tracked sites."""
    records = sites.list_sites()
    if json_out:
        _emit_json(records)
    else:
        for r in records:
            print(f"{r['slug']}  {r['url']}")


@app.command()
def check(slug: str, json_out: bool = typer.Option(False, "--json")) -> None:
    """Run checks for a tracked site, producing an immutable run snapshot."""
    try:
        site = sites.get_site(slug)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise typer.Exit(1) from exc
    finalized = runner.execute_run(site_slug=slug, url=site["url"])
    if json_out:
        _emit_json(finalized)
    else:
        print(report.render_run(finalized))


@app.command(name="runs")
def runs_command(slug: str, json_out: bool = typer.Option(False, "--json")) -> None:
    """List runs for a tracked site."""
    run_ids = runner.list_runs(slug)
    if json_out:
        _emit_json(run_ids)
    else:
        for run_id in run_ids:
            print(run_id)


@app.command()
def show(
    slug: str,
    run_id: str = typer.Argument("latest"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Show a single run (defaults to the latest)."""
    run_dir = runner.runs_root(slug) / run_id
    if not (run_dir / "manifest.json").exists():
        print(f"error: no run '{run_id}' for site '{slug}'", file=sys.stderr)
        raise typer.Exit(1)
    manifest = store.read_json(run_dir / "manifest.json")
    if json_out:
        _emit_json(manifest)
    else:
        print(report.render_run(manifest))


@app.command(name="diff")
def diff_command(slug: str, run_a: str, run_b: str) -> None:
    """Diff two runs for a site."""
    dir_a = runner.runs_root(slug) / run_a
    dir_b = runner.runs_root(slug) / run_b
    for run_id, run_dir in ((run_a, dir_a), (run_b, dir_b)):
        if not (run_dir / "manifest.json").exists():
            print(f"error: no run '{run_id}' for site '{slug}'", file=sys.stderr)
            raise typer.Exit(1)
    result = diff.diff_runs(dir_a, dir_b)
    _emit_json(result)


@app.command(name="report")
def report_command(slug: str, run_id: str = typer.Argument("latest")) -> None:
    """Render a run as human-readable text."""
    run_dir = runner.runs_root(slug) / run_id
    if not (run_dir / "manifest.json").exists():
        print(f"error: no run '{run_id}' for site '{slug}'", file=sys.stderr)
        raise typer.Exit(1)
    manifest = store.read_json(run_dir / "manifest.json")
    print(report.render_run(manifest))


@app.command()
def doctor(json_out: bool = typer.Option(False, "--json")) -> None:
    """Report resolved paths and external tool availability."""
    info = {
        "data_dir": str(paths.data_dir()),
        "config_dir": str(paths.config_dir()),
        "cache_dir": str(paths.cache_dir()),
        "state_dir": str(paths.state_dir()),
        "tools": {"lychee": shutil.which("lychee") is not None},
    }
    if json_out:
        _emit_json(info)
    else:
        for key, value in info.items():
            print(f"{key}: {value}")
