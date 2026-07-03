from pathlib import Path
from urllib.parse import urlparse

from tend import crawl, model, paths, store
from tend.checks import run_all


def runs_root(site_slug: str) -> Path:
    return paths.data_dir() / "runs" / site_slug


def _page_slug(url: str) -> str:
    parsed = urlparse(url)
    target = parsed.path
    if parsed.query:
        target += f"-{parsed.query}"
    try:
        return model.slugify(target)
    except ValueError:
        return "index"


def execute_run(site_slug: str, url: str) -> dict:
    run_id = model.new_run_id()
    run_dir = runs_root(site_slug) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest = model.run_manifest(run_id=run_id, site_slug=site_slug)

    root_checks: list[dict] = []
    page_summaries = []
    used_slugs: set[str] = set()
    for page_url in crawl.discover(url):
        checks = run_all(page_url)
        if not page_summaries:
            root_checks = checks

        slug = _page_slug(page_url)
        if slug in used_slugs:
            counter = 2
            while f"{slug}-{counter}" in used_slugs:
                counter += 1
            slug = f"{slug}-{counter}"
        used_slugs.add(slug)

        artifact = f"pages/{slug}.json"
        store.atomic_write_json(
            run_dir / "pages" / f"{slug}.json", model.page_record(page_url, checks)
        )
        page_summaries.append(
            {"url": page_url, "ok": all(c["ok"] for c in checks), "artifact": artifact}
        )

    finalized = model.finalize_run_manifest(manifest, checks=root_checks, pages=page_summaries)

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
