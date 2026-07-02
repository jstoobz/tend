def render_run(manifest: dict) -> str:
    lines = [f"Run {manifest['run_id']} — {manifest['site_slug']} — {manifest['status']}"]
    for check in manifest["checks"]:
        if check.get("skipped"):
            status = "SKIPPED"
        elif check["ok"]:
            status = "OK"
        else:
            status = "FAIL"
        lines.append(f"  [{status}] {check['name']}")
    return "\n".join(lines)
