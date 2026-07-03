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
    pages = manifest.get("pages")
    if pages:
        lines.append(f"  pages ({len(pages)}):")
        for page in pages:
            status = "OK" if page["ok"] else "FAIL"
            lines.append(f"    [{status}] {page['url']}")
    return "\n".join(lines)
