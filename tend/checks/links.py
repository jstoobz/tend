import json
import shutil
import subprocess

TOOL = "lychee"

# lychee embeds wall-clock timings at every level of its report; storing them
# would make any two runs diff as changed. Run timing lives on the manifest.
_VOLATILE_KEYS = {"duration"}


def _strip_volatile(value):
    if isinstance(value, dict):
        return {k: _strip_volatile(v) for k, v in value.items() if k not in _VOLATILE_KEYS}
    if isinstance(value, list):
        return [_strip_volatile(v) for v in value]
    return value


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
        parsed = _strip_volatile(json.loads(result.stdout))
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
