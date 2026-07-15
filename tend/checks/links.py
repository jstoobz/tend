import json
import shutil
import subprocess

TOOL = "lychee"

# lychee embeds wall-clock timings at every level of its report; storing them
# would make any two runs diff as changed. Run timing lives on the manifest.
_VOLATILE_KEYS = {"duration"}

# lychee checks links concurrently, so entries in its per-page maps arrive in
# completion order; sort them so identical site states capture identically.
# Only these top-level maps are sorted — nested lists like an entry's redirect
# chain are ordered data.
_LINK_MAP_KEYS = {"error_map", "fail_map", "excluded_map", "success_map", "suggestion_map"}


def _strip_volatile(value):
    if isinstance(value, dict):
        return {k: _strip_volatile(v) for k, v in value.items() if k not in _VOLATILE_KEYS}
    if isinstance(value, list):
        return [_strip_volatile(v) for v in value]
    return value


def _entry_key(entry):
    if not isinstance(entry, dict):
        return (str(entry), 0, 0)
    span = entry.get("span") or {}
    return (str(entry.get("url", "")), span.get("line", 0), span.get("column", 0))


def _order_link_maps(parsed):
    if not isinstance(parsed, dict):
        return parsed
    return {
        key: {
            page: sorted(entries, key=_entry_key) if isinstance(entries, list) else entries
            for page, entries in value.items()
        }
        if key in _LINK_MAP_KEYS and isinstance(value, dict)
        else value
        for key, value in parsed.items()
    }


def run(url: str) -> dict:
    if shutil.which(TOOL) is None:
        return {
            "name": "links",
            "ok": True,
            "skipped": True,
            "detail": {"reason": f"'{TOOL}' not found on PATH"},
        }

    result = subprocess.run(
        [TOOL, "--format", "json", url],
        capture_output=True,
        text=True,
        timeout=60,
    )
    try:
        parsed = _order_link_maps(_strip_volatile(json.loads(result.stdout)))
    except json.JSONDecodeError:
        parsed = {"raw_stdout": result.stdout}

    detail = {"returncode": result.returncode, "output": parsed}
    if result.returncode != 0 and result.stderr:
        detail["stderr"] = result.stderr.strip()

    return {
        "name": "links",
        "ok": result.returncode == 0,
        "skipped": False,
        "detail": detail,
    }
