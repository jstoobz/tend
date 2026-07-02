import json
import shutil
import subprocess

TOOL = "lychee"


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
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        parsed = {"raw_stdout": result.stdout}

    return {
        "name": "links",
        "ok": result.returncode == 0,
        "skipped": False,
        "detail": {"returncode": result.returncode, "output": parsed},
    }
