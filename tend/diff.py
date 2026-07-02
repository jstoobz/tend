from pathlib import Path

from tend import store


def diff_runs(run_dir_a: Path, run_dir_b: Path) -> dict:
    manifest_a = store.read_json(run_dir_a / "manifest.json")
    manifest_b = store.read_json(run_dir_b / "manifest.json")
    checks_a = {c["name"]: c for c in manifest_a["checks"]}
    checks_b = {c["name"]: c for c in manifest_b["checks"]}

    names_a, names_b = set(checks_a), set(checks_b)
    changed = []
    unchanged = []
    for name in sorted(names_a & names_b):
        if checks_a[name] == checks_b[name]:
            unchanged.append(name)
        else:
            changed.append({"name": name, "before": checks_a[name], "after": checks_b[name]})

    return {
        "run_a": manifest_a["run_id"],
        "run_b": manifest_b["run_id"],
        "added_checks": sorted(names_b - names_a),
        "removed_checks": sorted(names_a - names_b),
        "changed": changed,
        "unchanged": unchanged,
    }
