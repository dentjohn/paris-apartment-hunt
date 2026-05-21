"""Merge new listings into listings_input.json.

Typical workflow:
  1. A Claude conversation scrapes a filtered listing page and returns a JSON
     array of listing objects (see scraping-prompt section in README).
  2. Save that array to `new_listings.json` in this folder.
  3. Run:  python merge_listings.py new_listings.json [--rebuild] [--push]

The script:
  - Validates each entry has the required fields
  - Dedupes by `id` against existing listings_input.json
  - Auto-downloads DVF for any new arrondissement codes (75XXX) referenced
  - Updates DVF_ARRS in build_dashboard.py if needed
  - Appends new entries to listings_input.json
  - With --rebuild, runs build_dashboard.py
  - With --push, commits and pushes to git

Exit code 0 on success, 1 on any validation or download failure.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
LISTINGS = REPO / "listings_input.json"
BUILD_SCRIPT = REPO / "build_dashboard.py"

REQUIRED = ("id", "price_eur", "surface_m2", "arr", "arr_name")
ARR_PATTERN = re.compile(r"^751\d{2}$")
DVF_URL = "https://files.data.gouv.fr/geo-dvf/latest/csv/{year}/communes/75/{arr}.csv"


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def validate(entries: list[dict]) -> list[dict]:
    """Drop invalid entries with a warning, return the clean list."""
    clean = []
    for i, e in enumerate(entries):
        if not isinstance(e, dict):
            print(f"skip [{i}]: not a dict")
            continue
        missing = [k for k in REQUIRED if not e.get(k)]
        if missing:
            print(f"skip [{i}] id={e.get('id','?')}: missing fields {missing}")
            continue
        if not ARR_PATTERN.match(e["arr"]):
            print(f"skip [{i}] id={e['id']}: bad arr code {e['arr']!r} (expected 751XX)")
            continue
        if not (50_000 <= e["price_eur"] <= 50_000_000):
            print(f"skip [{i}] id={e['id']}: price {e['price_eur']} out of plausible range")
            continue
        if not (10 <= e["surface_m2"] <= 1000):
            print(f"skip [{i}] id={e['id']}: surface {e['surface_m2']} out of plausible range")
            continue
        clean.append(e)
    return clean


def fetch_dvf(arr: str) -> bool:
    """Download DVF CSVs for one arrondissement (2024 + 2025). Returns True on success."""
    ok = True
    for year in (2024, 2025):
        out = REPO / f"dvf_{arr}_{year}.csv"
        if out.exists() and out.stat().st_size > 200:
            continue
        url = DVF_URL.format(year=year, arr=arr)
        print(f"  fetching dvf {arr}/{year}…", end=" ", flush=True)
        # Use curl rather than urllib because macOS framework Python (3.14+)
        # ships without root certs by default and TLS verification fails.
        # curl uses the OS cert store.
        r = subprocess.run(
            ["curl", "-sL", "--fail", "--max-time", "30", "-o", str(out), url],
            capture_output=True, text=True,
        )
        if r.returncode != 0 or not out.exists() or out.stat().st_size < 200:
            print(f"FAILED (curl exit {r.returncode}): {r.stderr.strip()[:200]}")
            ok = False
        else:
            print(f"{out.stat().st_size:,} bytes")
    return ok


def patch_dvf_arrs(new_arrs: set[str]) -> bool:
    """Insert new arrondissement codes into the DVF_ARRS literal in build_dashboard.py."""
    if not new_arrs:
        return True
    src = BUILD_SCRIPT.read_text()
    m = re.search(r"DVF_ARRS\s*=\s*\[([^\]]*)\]", src)
    if not m:
        print("warning: couldn't find DVF_ARRS in build_dashboard.py — patch it by hand")
        return False
    current = {q.strip().strip('"').strip("'") for q in m.group(1).split(",") if q.strip()}
    merged = sorted(current | new_arrs)
    new_block = "DVF_ARRS = [" + ", ".join(f'"{a}"' for a in merged) + "]"
    BUILD_SCRIPT.write_text(src.replace(m.group(0), new_block, 1))
    print(f"patched DVF_ARRS in build_dashboard.py → {len(merged)} arrondissements")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("input", help="Path to new_listings.json (a JSON array of listing objects)")
    ap.add_argument("--rebuild", action="store_true", help="Run build_dashboard.py after merge")
    ap.add_argument("--push", action="store_true",
                    help="Stage all changes, commit, and push to origin (implies --rebuild)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Validate + dedupe + show what would change, write nothing")
    args = ap.parse_args()

    inp = Path(args.input)
    if not inp.exists():
        die(f"input file not found: {inp}")
    try:
        new_raw = json.loads(inp.read_text())
    except json.JSONDecodeError as exc:
        die(f"input is not valid JSON: {exc}")
    if not isinstance(new_raw, list):
        die(f"input must be a JSON array of listing objects (got {type(new_raw).__name__})")

    if not LISTINGS.exists():
        die(f"listings_input.json not found at {LISTINGS} — are you in the repo root?")
    existing = json.loads(LISTINGS.read_text())
    existing_ids = {l.get("id") for l in existing}

    print(f"input: {len(new_raw)} candidate entries")
    print(f"current: {len(existing)} listings in {LISTINGS.name}")

    valid = validate(new_raw)
    dupes = [e for e in valid if e["id"] in existing_ids]
    to_add = [e for e in valid if e["id"] not in existing_ids]

    print(f"valid: {len(valid)}, dupes: {len(dupes)}, to add: {len(to_add)}")
    if not to_add:
        print("nothing to merge — exiting clean")
        return 0

    new_arrs = {e["arr"] for e in to_add}
    have_dvf = {p.name.split("_")[1] for p in REPO.glob("dvf_751*_2024.csv")}
    need_dvf = sorted(new_arrs - have_dvf)
    if need_dvf:
        print(f"new arrondissements needing DVF: {need_dvf}")
    if args.dry_run:
        for e in to_add[:5]:
            print(f"  would add: {e['id']} | {e['arr_name']} | €{e['price_eur']:,} / {e['surface_m2']}m²")
        if len(to_add) > 5:
            print(f"  …and {len(to_add) - 5} more")
        return 0

    if need_dvf:
        for arr in need_dvf:
            if not fetch_dvf(arr):
                die(f"DVF fetch failed for {arr} — aborting before mutating files")
        patch_dvf_arrs(set(need_dvf))

    merged = existing + to_add
    LISTINGS.write_text(json.dumps(merged, indent=2, ensure_ascii=False))
    print(f"wrote {LISTINGS.name}: {len(existing)} → {len(merged)} listings")

    if args.rebuild or args.push:
        print("running build_dashboard.py …")
        r = subprocess.run([sys.executable, str(BUILD_SCRIPT)], cwd=REPO)
        if r.returncode != 0:
            die("build_dashboard.py failed — fix and rerun")

    if args.push:
        print("committing and pushing …")
        n = len(to_add)
        msg = f"Add {n} listing{'s' if n != 1 else ''}"
        subprocess.run(["git", "add", "-A"], cwd=REPO, check=True)
        # If nothing is staged (e.g. re-merge of an already-merged input),
        # skip commit + push instead of dying.
        diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=REPO)
        if diff.returncode == 0:
            print("no changes to commit — skipping push")
        else:
            r = subprocess.run(["git", "commit", "-q", "-m", msg], cwd=REPO)
            if r.returncode != 0:
                die("git commit failed")
            r = subprocess.run(["git", "push", "-q", "origin"], cwd=REPO)
            if r.returncode != 0:
                die("git push failed")
            print("pushed.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
