from pathlib import Path

from tend import model, paths, store


def sites_dir() -> Path:
    return paths.data_dir() / "sites"


def track(name: str, url: str) -> dict:
    record = model.site_record(name=name, url=url)
    store.atomic_write_json(sites_dir() / f"{record['slug']}.json", record)
    return record


def list_sites() -> list[dict]:
    d = sites_dir()
    if not d.exists():
        return []
    return sorted((store.read_json(p) for p in d.glob("*.json")), key=lambda r: r["slug"])


def get_site(slug: str) -> dict:
    path = sites_dir() / f"{slug}.json"
    if not path.exists():
        raise FileNotFoundError(f"no tracked site: {slug}")
    return store.read_json(path)
