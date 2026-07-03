from pathlib import Path

from tend import model, paths, store
from tend.checks import run_all


def runs_root(site_slug: str) -> Path:
    return paths.data_dir() / "runs" / site_slug


def execute_run(site_slug: str, url: str) -> dict:
    run_id = model.new_run_id()
    run_dir = runs_root(site_slug) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest = model.run_manifest(run_id=run_id, site_slug=site_slug)
    results = run_all(url)
    finalized = model.finalize_run_manifest(manifest, checks=results, pages=[])

    store.atomic_write_json(run_dir / "manifest.json", finalized)
    store.swap_symlink(runs_root(site_slug) / "latest", run_dir)

    return finalized


def list_runs(site_slug: str) -> list[str]:
    root = runs_root(site_slug)
    if not root.exists():
        return []
    return sorted(
        p.name
        for p in root.iterdir()
        if p.is_dir() and not p.is_symlink() and (p / "manifest.json").exists()
    )
