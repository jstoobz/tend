import re
import secrets
import unicodedata
from datetime import UTC, datetime

SITE_SCHEMA_VERSION = 1
RUN_SCHEMA_VERSION = 2
PAGE_SCHEMA_VERSION = 1

_SUFFIX_ALPHABET = "abcdefghjkmnpqrstvwxyz23456789"  # no 0/1/i/l/o ambiguity


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_run_id() -> str:
    ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    suffix = "".join(secrets.choice(_SUFFIX_ALPHABET) for _ in range(6))
    return f"{ts}-{suffix}"


def slugify(value: str) -> str:
    value = value.strip().lower()
    if not value:
        raise ValueError("cannot slugify an empty value")
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"^https?://", "", value)
    value = re.sub(r"^www\.", "", value)
    value = value.replace("'", "")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    slug = value.strip("-")
    if not slug:
        raise ValueError(f"value has no sluggable characters: {value!r}")
    return slug


def site_record(name: str, url: str) -> dict:
    return {
        "schema_version": SITE_SCHEMA_VERSION,
        "slug": slugify(name),
        "name": name,
        "url": url,
        "created_at": _now_iso(),
    }


def run_manifest(run_id: str, site_slug: str) -> dict:
    return {
        "schema_version": RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "site_slug": site_slug,
        "status": "running",
        "started_at": _now_iso(),
        "finished_at": None,
        "checks": [],
        "pages": [],
    }


def finalize_run_manifest(manifest: dict, checks: list[dict], pages: list[dict]) -> dict:
    return {
        **manifest,
        "status": "complete",
        "finished_at": _now_iso(),
        "checks": checks,
        "pages": pages,
    }


def page_record(url: str, checks: list[dict]) -> dict:
    return {
        "schema_version": PAGE_SCHEMA_VERSION,
        "url": url,
        "checks": checks,
    }
