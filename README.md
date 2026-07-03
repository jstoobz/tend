# tend

"To tend, simply put, is to rip it and ship it."

— Stoobz

Iterative SEO audits and improvement tracking for small-business websites.

`tend` tracks a site, runs a set of checks against it, and stores each run as an
immutable, timestamped snapshot — so you can see what changed between visits.

## Install

```bash
uv tool install tend
# or
pip install tend
```

Requires Python 3.11+.

## Quickstart

```bash
tend track "Bob's Bakery" https://bobsbakery.example.com
tend check bobs-bakery
tend show bobs-bakery
```

## Usage

### Track a site

```bash
tend track <name> <url>
```

Registers a site under a slug derived from `<name>` (e.g. `"Bob's Bakery"` → `bobs-bakery`).

### List tracked sites

```bash
tend sites
tend sites --json
```

### Run checks

```bash
tend check <slug>
```

Discovers the site's pages (same-origin breadth-first crawl: up to 25 pages, depth 2,
0.5s between fetches; `www.` and apex hosts are treated as one origin), runs the check
suite against every page, and writes the result as a new, immutable run — one artifact
per page under `pages/`, plus a manifest. Updates the site's `latest` pointer on
success.

Checks currently included:

- **onpage** — page title and meta description presence
- **links** — broken-link scan via [`lychee`](https://github.com/lycheeverse/lychee), if
  installed; skipped (not failed) when the tool isn't on `PATH`

### List runs

```bash
tend runs <slug>
tend runs <slug> --json
```

### Show a run

```bash
tend show <slug>              # latest run
tend show <slug> <run-id>     # a specific run
tend report <slug> [<run-id>] # same data, plain-text report
```

### Diff two runs

```bash
tend diff <slug> <run-id-a> <run-id-b>
```

Reports which root-page checks changed, were added, or were removed between two runs.
Output is always JSON.

### Check your setup

```bash
tend doctor
```

Prints resolved storage paths and whether optional external tools (e.g. `lychee`) are
available.

## Storage

`tend` follows the XDG Base Directory spec for its data, config, cache, and state roots.
Set `TEND_HOME` to override all of them at once (useful for testing or a portable
install). Run `tend doctor` to see the resolved paths on your system.

## Every command supports `--json`

Any command that prints structured data accepts `--json` for machine-readable output.

## License

MIT
