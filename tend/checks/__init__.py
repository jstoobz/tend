from tend.checks import links, onpage

CHECK_REGISTRY = {"onpage": onpage, "links": links}


def run_all(url: str) -> list[dict]:
    results = []
    for name, module in CHECK_REGISTRY.items():
        try:
            results.append(module.run(url))
        except Exception as exc:
            results.append(
                {"name": name, "ok": False, "skipped": False, "detail": {"error": str(exc)}}
            )
    return results
