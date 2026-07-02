import json
import os
import tempfile
from pathlib import Path


def atomic_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        os.replace(tmp_name, path)
    except BaseException:
        os.unlink(tmp_name)
        raise


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def swap_symlink(link: Path, target: Path) -> None:
    tmp_link = link.parent / f".{link.name}.tmp"
    if tmp_link.exists() or tmp_link.is_symlink():
        tmp_link.unlink()
    tmp_link.symlink_to(target)
    os.replace(tmp_link, link)
