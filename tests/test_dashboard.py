"""End-to-end tests for the dashboard pipeline.

Run with:  python -m pytest -v

These tests catch the class of bugs that bit us in production:
  1. Build script crashes (regression in cleaning / aggregation)
  2. dashboard.html ships with the __LISTINGS_DATA_JSON__ placeholder un-replaced
  3. The inline dashboard JS has a parse error (e.g. duplicate `const`)
  4. A listing references an arrondissement with no DVF data (silent failure)
  5. arr_name() helper drifts away from correct English ordinals

Tests run against the real listings_input.json + DVF CSVs in the repo —
no fixtures required.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BUILD_SCRIPT = ROOT / "build_dashboard.py"
LISTINGS_INPUT = ROOT / "listings_input.json"
DASHBOARD_DIR = ROOT / "dashboard"


# ---------------------------------------------------------------------------
# Pipeline smoke tests
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def built_dashboard():
    """Run build_dashboard.py once per test session, return its rc."""
    r = subprocess.run(
        [sys.executable, str(BUILD_SCRIPT)],
        cwd=ROOT, capture_output=True, text=True, timeout=120,
    )
    return r


def test_build_succeeds(built_dashboard):
    assert built_dashboard.returncode == 0, (
        f"build_dashboard.py failed:\nstdout:\n{built_dashboard.stdout}\n"
        f"stderr:\n{built_dashboard.stderr}"
    )


def test_listings_json_is_valid(built_dashboard):
    """listings.json must parse and have ≥1 entry with required fields."""
    assert built_dashboard.returncode == 0
    data = json.loads((DASHBOARD_DIR / "listings.json").read_text())
    assert isinstance(data, dict)
    assert "listings" in data and len(data["listings"]) > 0
    for L in data["listings"]:
        assert L.get("id"), f"listing missing id: {L}"
        assert L.get("arr"), f"listing {L.get('id')} missing arr"
        assert L.get("arr_name"), f"listing {L.get('id')} missing arr_name"


def test_dashboard_html_template_fully_rendered(built_dashboard):
    """The placeholder must be fully replaced, and the embedded JSON must parse."""
    assert built_dashboard.returncode == 0
    html = (DASHBOARD_DIR / "dashboard.html").read_text()
    assert '<script id="listings-data"' in html
    assert "__LISTINGS_DATA_JSON__" not in html, (
        "template placeholder leaked into the rendered dashboard.html"
    )
    m = re.search(
        r'<script id="listings-data"[^>]*>(.+?)</script>',
        html, re.DOTALL,
    )
    assert m, "listings-data script tag not found in dashboard.html"
    embedded = m.group(1).replace("<\\/", "</")  # reverse the build-time escape
    data = json.loads(embedded)
    assert len(data["listings"]) > 0


def test_dashboard_js_parses(built_dashboard):
    """The dashboard's inline JS must be syntactically valid.

    Catches things like duplicate `const ppm` declarations that would prevent
    the entire IIFE from executing. Uses `node --check`; skipped if node isn't
    available locally (CI installs it).
    """
    assert built_dashboard.returncode == 0
    if not shutil.which("node"):
        pytest.skip("node not installed — skipping JS parse check")
    html = (DASHBOARD_DIR / "dashboard.html").read_text()
    html_no_data = re.sub(
        r'<script id="listings-data"[^>]*>.+?</script>',
        "", html, count=1, flags=re.DOTALL,
    )
    m = re.search(r"<script>(.+?)</script>", html_no_data, re.DOTALL)
    assert m, "dashboard inline JS not found"
    js = m.group(1)
    tf = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False)
    try:
        tf.write(js)
        tf.close()
        r = subprocess.run(
            ["node", "--check", tf.name],
            capture_output=True, text=True,
        )
        assert r.returncode == 0, f"JS parse failed:\n{r.stderr}"
    finally:
        os.unlink(tf.name)


# ---------------------------------------------------------------------------
# Data-integrity tests
# ---------------------------------------------------------------------------
def test_all_listing_arrs_covered_by_dvf():
    """Every listing's arr must have a corresponding DVF CSV.

    Otherwise the band analysis silently returns empty stats and the
    listing shows up with no verdict — a regression we'd only catch by eye.
    """
    listings = json.loads(LISTINGS_INPUT.read_text())
    used_arrs = {L["arr"] for L in listings if L.get("arr")}
    have_dvf = {p.name.split("_")[1] for p in ROOT.glob("dvf_751*_2024.csv")}
    missing = used_arrs - have_dvf
    assert not missing, (
        f"listings reference arrondissements without DVF data: {sorted(missing)}"
    )


def test_listings_input_arr_codes_well_formed():
    """All listings_input.json arr codes must match the 751XX pattern."""
    listings = json.loads(LISTINGS_INPUT.read_text())
    pat = re.compile(r"^751\d{2}$")
    bad = [L["id"] for L in listings if not pat.match(L.get("arr", ""))]
    assert not bad, f"listings with malformed arr codes: {bad}"


# ---------------------------------------------------------------------------
# Helper tests
# ---------------------------------------------------------------------------
def test_listing_url_specific_passthrough():
    """Specific deep-link URLs must pass through unchanged with kind='specific'."""
    sys.path.insert(0, str(ROOT))
    from build_dashboard import _listing_url
    cases = [
        # Le Figaro Immobilier annonce-XXX
        {"url": "https://immobilier.lefigaro.fr/annonces/annonce-12345.html",
         "source": "Hosman (via Le Figaro)", "arr": "75103",
         "price_eur": 2_000_000, "surface_m2": 100},
        # ap.immo (Nouvelle Vague)
        {"url": "https://ap.immo/p/86280768", "source": "Nouvelle Vague",
         "arr": "75106", "price_eur": 1_700_000, "surface_m2": 83},
        # Le Figaro Properties /announces/.../{id}/
        {"url": "https://properties.lefigaro.com/announces/apartment-paris-ile+de+france-france/100551831/",
         "source": "Le Figaro", "arr": "75103",
         "price_eur": 2_000_000, "surface_m2": 186},
    ]
    for L in cases:
        url, kind = _listing_url(L)
        assert kind == "specific", f"{L['url']} should be specific, got {kind}"
        assert url == L["url"], f"specific URL should pass through unchanged"


def test_listing_url_bienici_synthesizes_narrow_filter():
    """Bien'ici search-only sources should get a narrow filter URL."""
    sys.path.insert(0, str(ROOT))
    from build_dashboard import _listing_url
    L = {"url": "https://www.bienici.com/recherche/achat/paris-75000/...",
         "source": "Bien'ici aggregator", "arr": "75116",
         "price_eur": 1_500_000, "surface_m2": 120, "pieces": 5}
    url, kind = _listing_url(L)
    assert kind == "search"
    assert "bienici.com" in url
    assert "paris-75016" in url
    assert "prix-min=" in url and "prix-max=" in url
    assert "surface-min=" in url and "surface-max=" in url


def test_listing_url_falls_back_to_google_with_site_filter():
    """Listings without specific URLs and not on Bien'ici/SeLoger should get
    Google site-restricted search URLs with price + surface + arr."""
    sys.path.insert(0, str(ROOT))
    from build_dashboard import _listing_url
    L = {"url": "https://www.green-acres.fr/property/Av0778vy",
         "source": "Vaneau (via Green Acres)", "arr": "75115",
         "price_eur": 1_290_000, "surface_m2": 109}
    url, kind = _listing_url(L)
    assert kind == "search"
    assert "google.com/search" in url
    assert "green-acres" in url
    assert "1%20290%20000" in url or "1+290+000" in url


def test_renovation_tags_classification():
    """_renovation_tags must classify common French/English signals correctly."""
    sys.path.insert(0, str(ROOT))
    from build_dashboard import _renovation_tags

    # Renovated only
    assert "renovated" in _renovation_tags({"notes": "Apartment in parfait état, fully renovated"})
    assert "renovated" in _renovation_tags({"condition": "perfect condition (confirmed visually)"})
    assert "renovated" in _renovation_tags({"notes": "Clé en main, refait à neuf en 2023"})

    # Period preserved
    tags = _renovation_tags({"condition_signals": ["intact Louis XV marble fireplace", "boiserie wall paneling"]})
    assert "period-preserved" in tags

    # Needs work
    assert "needs-work" in _renovation_tags({"notes": "Appartement à rénover, travaux à prévoir"})
    assert "needs-work" in _renovation_tags({"condition": "dated finishes (visible)"})

    # Combined — renovated AND period-preserved
    tags = _renovation_tags({
        "condition": "renovated showcase Haussmannian",
        "features": ["fresh white paint", "elaborate ceiling moldings/rosette intact"],
    })
    assert "renovated" in tags and "period-preserved" in tags

    # No signal → unknown
    assert _renovation_tags({"notes": "Appartement de 100 m² au 3ème étage"}) == ["unknown"]
    assert _renovation_tags({}) == ["unknown"]


def test_arr_name_ordinals():
    """arr_name() must produce correct English ordinals — especially 11/12/13."""
    sys.path.insert(0, str(ROOT))
    from build_dashboard import arr_name
    cases = {
        "75101": "Paris 1st", "75102": "Paris 2nd", "75103": "Paris 3rd",
        "75104": "Paris 4th", "75109": "Paris 9th", "75110": "Paris 10th",
        "75111": "Paris 11th",  # not 11st
        "75112": "Paris 12th",  # not 12nd
        "75113": "Paris 13th",  # not 13rd
        "75116": "Paris 16th", "75120": "Paris 20th",
    }
    for code, expected in cases.items():
        assert arr_name(code) == expected, (
            f"arr_name({code!r}) = {arr_name(code)!r}, expected {expected!r}"
        )


def test_merge_listings_validates_bad_input(tmp_path):
    """merge_listings.py --dry-run must reject malformed entries without writing."""
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps([
        {"id": "BAD-arr", "arr": "75999", "arr_name": "x",
         "price_eur": 1_000_000, "surface_m2": 100},
        {"id": "BAD-missing"},  # missing required fields
        {"id": "OK-1", "arr": "75103", "arr_name": "Paris 3rd",
         "price_eur": 1_500_000, "surface_m2": 100},
    ]))
    r = subprocess.run(
        [sys.executable, "merge_listings.py", str(bad), "--dry-run"],
        cwd=ROOT, capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0
    assert "skip" in r.stdout.lower()
    assert "valid: 1" in r.stdout, (
        f"expected exactly 1 valid entry; got:\n{r.stdout}"
    )
