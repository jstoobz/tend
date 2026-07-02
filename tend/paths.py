import os
from pathlib import Path

import platformdirs

_KINDS = ("data", "config", "cache", "state")


def _resolve(kind: str) -> Path:
    override = os.environ.get("TEND_HOME")
    if override:
        return Path(override) / kind
    return Path(getattr(platformdirs, f"user_{kind}_dir")("tend"))


def data_dir(ensure: bool = False) -> Path:
    return _ensure(_resolve("data"), ensure)


def config_dir(ensure: bool = False) -> Path:
    return _ensure(_resolve("config"), ensure)


def cache_dir(ensure: bool = False) -> Path:
    return _ensure(_resolve("cache"), ensure)


def state_dir(ensure: bool = False) -> Path:
    return _ensure(_resolve("state"), ensure)


def _ensure(path: Path, ensure: bool) -> Path:
    if ensure:
        path.mkdir(parents=True, exist_ok=True)
    return path
