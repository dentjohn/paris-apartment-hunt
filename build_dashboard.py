"""Build the listings dashboard.

Pipeline:
  1. Load DVF for all arrondissements where we have listings
  2. Compute per-arr / per-surface-band fair-value benchmarks
  3. For each listing, compute verdict + expert analysis text
  4. Write listings.json
  5. Render dashboard.html (reads listings.json client-side)

To add new listings: append to LISTINGS below and rerun.
"""

from __future__ import annotations
import json
import re
import urllib.parse
from datetime import date
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent
OUT_DIR = DATA_DIR / "dashboard"
OUT_DIR.mkdir(exist_ok=True)

YEARS = [2024, 2025]

# Arrondissement codes used. Add to this when new listings come from
# new arrondissements (and download the corresponding CSV first).
DVF_ARRS = ["75101", "75102", "75103", "75104", "75105", "75106", "75107", "75108", "75109", "75116"]

# Surface bucket boundaries (m²) and labels
BUCKETS = [(0, 50, "<50"), (50, 80, "50-80"), (80, 120, "80-120"),
           (120, 200, "120-200"), (200, 10_000, "200+")]


# ============================================================
# 1. Load + clean DVF (same logic across the analysis)
# ============================================================
def _load_arr(arr: str) -> pd.DataFrame:
    frames = []
    for y in YEARS:
        p = DATA_DIR / f"dvf_{arr}_{y}.csv"
        if p.exists() and p.stat().st_size > 200:
            frames.append(pd.read_csv(p, low_memory=False))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df["date_mutation"] = pd.to_datetime(df["date_mutation"], errors="coerce")
    df = df[df["nature_mutation"] == "Vente"]

    has_non_apt = (
        df.assign(other=df["type_local"].notna() & (df["type_local"] != "Appartement"))
        .groupby("id_mutation")["other"].any()
    )
    df = df[df["id_mutation"].isin(has_non_apt[~has_non_apt].index)]
    df = df[df["type_local"] == "Appartement"]
    df = df.dropna(subset=["valeur_fonciere", "surface_reelle_bati"])
    df = df[(df["valeur_fonciere"] > 0) & (df["surface_reelle_bati"] > 0)]

    agg = df.groupby("id_mutation").agg(
        date_mutation=("date_mutation", "first"),
        valeur_fonciere=("valeur_fonciere", "first"),
        surface=("surface_reelle_bati", "sum"),
        adresse=("adresse_nom_voie", "first"),
        numero=("adresse_numero", "first"),
        code_commune=("code_commune", "first"),
    ).reset_index()
    agg["eur_per_m2"] = agg["valeur_fonciere"] / agg["surface"]
    return agg[(agg["eur_per_m2"] >= 5_000) & (agg["eur_per_m2"] <= 40_000)]


def _bucket_for(surface: float | None) -> str | None:
    if surface is None: return None
    for lo, hi, label in BUCKETS:
        if lo <= surface < hi:
            return label
    return None


def _bucket_stats(df: pd.DataFrame, surface: float | None) -> dict:
    """Stats for the surface band most relevant to this listing.

    For surfaces ≥ 80 m², we *widen* to the 80-250 m² range to avoid
    single-digit-sample noise in the narrow 120-200 bucket.
    """
    if df.empty or surface is None:
        return {}
    if surface < 80:
        sub = df[df["surface"] < 80]
        band = "<80 m²"
    else:
        sub = df[(df["surface"] >= 80) & (df["surface"] <= 250)]
        band = "80-250 m²"
    if sub.empty:
        return {}
    s = sub["eur_per_m2"]
    return {
        "band": band,
        "n": len(sub),
        "median": float(s.median()),
        "p25": float(s.quantile(0.25)),
        "p75": float(s.quantile(0.75)),
        "p10": float(s.quantile(0.10)),
        "p90": float(s.quantile(0.90)),
    }


def _listing_url(L: dict) -> tuple[str, str]:
    """Resolve the best clickable URL for a listing.

    Returns (url, kind). kind="specific" means it points to a unique listing
    page. kind="search" means it points to a (narrow) result set on the
    source site or a Google site-restricted search.

    Most scraped sources (Bien'ici, SeLoger, Barnes, Daniel Féau, Green Acres)
    don't expose deep links to individual listings — only filterable search
    URLs or JS-rendered detail pages. For those, we synthesize the narrowest
    possible search URL using price ±2%, surface ±5%, arr, and (when
    available) neighborhood.
    """
    url = (L.get("url") or "").strip()
    source = (L.get("source") or "").lower()

    # ---- Specific deep links: pass through ----
    if "/annonce-" in url:
        return url, "specific"
    if "ap.immo/p/" in url:
        return url, "specific"
    if re.match(r"^https://properties\.lefigaro\.com/announces/[^/]+/\d+/?$", url):
        return url, "specific"

    # ---- Fall back to a synthesized search URL ----
    arr = L.get("arr") or ""
    arr_n = int(arr[-2:]) if arr.startswith("751") and arr[-2:].isdigit() else None
    zipcode = f"750{arr[-2:]}" if arr_n is not None else None
    price = L.get("price_eur")
    surface = L.get("surface_m2")
    neighborhood = L.get("neighborhood") or ""

    # Without price + surface we can't narrow the search — give back the
    # original URL but mark it as search so the dashboard UI is honest.
    if not (price and surface):
        return url, "search"

    p_lo = int(price * 0.98)
    p_hi = int(price * 1.02)
    s_lo = max(1, int(surface * 0.95))
    s_hi = int(surface * 1.05)

    # Bien'ici has URL-filterable search — most precise option for them.
    if "bien" in source and "ici" in source:
        rooms = L.get("pieces") or 4
        return (
            f"https://www.bienici.com/recherche/achat/paris-{zipcode}"
            f"/appartement/{rooms}-pieces-et-plus"
            f"?prix-min={p_lo}&prix-max={p_hi}"
            f"&surface-min={s_lo}&surface-max={s_hi}",
            "search",
        )

    # SeLoger search URL has a documented form too.
    if "seloger" in source:
        rooms = L.get("pieces") or 4
        return (
            f"https://www.seloger.com/list.htm?projects=2&types=1"
            f"&places=%5B%7B%22subDivisions%22%3A%5B%22{arr}%22%5D%7D%5D"
            f"&price={p_lo}%2F{p_hi}&surface={s_lo}%2F{s_hi}"
            f"&rooms={rooms}",
            "search",
        )

    # Site-restricted Google search for the rest (Green Acres, Barnes,
    # Daniel Féau, Sotheby's, Nouvelle Vague when the ap.immo link is broken).
    SITE_MAP = {
        "green acres": "site:green-acres.fr OR site:green-acres.com",
        "barnes": "site:barnes-paris.com",
        "daniel féau": "site:danielfeau.com",
        "daniel feau": "site:danielfeau.com",
        "sotheby": "site:parissothebysrealty.com OR site:sothebysrealty.com",
        "nouvelle vague": "site:nouvellevague-paris.fr OR site:ap.immo",
        "le figaro": "site:immobilier.lefigaro.fr OR site:properties.lefigaro.com",
    }
    site_filter = next((v for k, v in SITE_MAP.items() if k in source), "")

    q_parts = []
    if site_filter:
        q_parts.append(site_filter)
    q_parts.append(f'"{int(round(surface))} m²"')
    # French thousand-separator (space) — Google handles unicode space
    q_parts.append(f'"{int(price):,}"'.replace(",", " "))
    if neighborhood:
        q_parts.append(f'"{neighborhood}"')
    if arr_n:
        q_parts.append(f'Paris {arr_n}')
    q = urllib.parse.quote(" ".join(q_parts), safe='":')
    return f"https://www.google.com/search?q={q}", "search"


def arr_name(arr_code: str) -> str:
    """Convert a commune code like '75103' to 'Paris 3rd'.

    Correct for 11/12/13 (falls through to 'th'). Only valid for Paris
    arrondissements 1-20 — for anything else the ordinal is wrong but the
    function never raises.
    """
    n = int(arr_code[-2:])
    if 10 <= n % 100 <= 20:
        suf = "th"  # 11th, 12th, 13th
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"Paris {n}{suf}"


def _arr_overall(df: pd.DataFrame) -> dict:
    if df.empty: return {}
    s = df["eur_per_m2"]
    return {
        "n": len(df),
        "median": float(s.median()),
        "p25": float(s.quantile(0.25)),
        "p75": float(s.quantile(0.75)),
    }


# ============================================================
# 2. Listings — structured data
# ============================================================
LISTINGS = json.loads((DATA_DIR / "listings_input.json").read_text())
# ============================================================
# 3. Analysis per listing
# ============================================================
def _verdict(ask_per_m2: float, fair_lo: float, fair_hi: float) -> tuple[str, str]:
    """Classify ask vs fair-value range."""
    if ask_per_m2 < fair_lo * 0.92:
        return "underpriced", "Material discount to band median, worth investigating closely."
    if ask_per_m2 < fair_lo:
        return "below-band", "Priced below the IQR floor — likely reflects a real handicap (north exposure, low floor, condition)."
    if ask_per_m2 <= fair_hi:
        return "in-band", "Priced inside the interquartile range — fair for the size class in this arrondissement."
    if ask_per_m2 <= fair_hi * 1.08:
        return "above-band", "Above the p75 of recent sales — typical for renovated/exceptional units."
    return "overpriced", "Materially above the p75 — needs strong condition/floor/view justification."


def _expert_analysis(listing: dict, arr_overall: dict, band: dict) -> str:
    """Markdown blob — read on the dashboard side."""
    parts = []
    price = listing.get("price_eur")
    surface = listing.get("surface_m2")
    ask = price / surface if (price and surface) else None

    if listing.get("needs_data"):
        parts.append(f"**Cannot value — surface missing from listing.** Price €{price:,} alone is not enough.")
        parts.append(f"For context, recent {listing['arr_name']} apartment-only sales median **€{arr_overall.get('median', 0):,.0f}/m²** "
                     f"(n={arr_overall.get('n', 0)}, 2024-25).")
        parts.append(f"→ Action: fetch the full listing or ask Anne-Sophie for the m² and a recent visit summary.")
        return "\n\n".join(parts)

    parts.append(f"**Ask: €{price:,} for {surface} m² = €{ask:,.0f}/m².**")

    if band:
        verdict, blurb = _verdict(ask, band["p25"], band["p75"])
        parts.append(
            f"Against recent {listing['arr_name']} sales in the {band['band']} surface band "
            f"(n={band['n']}): median €{band['median']:,.0f}/m², "
            f"IQR €{band['p25']:,.0f}–€{band['p75']:,.0f}/m². "
            f"Asking €{ask:,.0f}/m² → **{verdict.upper()}** — {blurb}"
        )
        delta_med = (ask - band["median"]) / band["median"] * 100
        parts.append(f"Premium vs median: **{delta_med:+.1f}%**.")
    else:
        parts.append(f"⚠ No DVF comps available for this band.")

    # Visual condition assessment from photo (when available)
    if listing.get("condition_signals"):
        signals = ", ".join(listing["condition_signals"][:4])
        parts.append(f"**Photo signals:** {signals}.")

    # Compounding red flag: above-market price + visually dated
    cond_lower = (listing.get("condition") or "").lower()
    is_dated = any(k in cond_lower for k in ["dated", "needs work", "average"])
    is_premium_ask = (ask is not None) and band and ask > band["p75"]
    if is_dated and is_premium_ask:
        parts.append("**⚠ Compounding concern:** asking price is above the band's p75 *and* photos show dated finishes — material renovation budget needs to be priced in.")

    # Strengths
    strengths = []
    if listing.get("elevator"):
        strengths.append("elevator")
    if listing.get("floor") and listing.get("floor") >= 2:
        suffix = 'nd' if listing['floor'] == 2 else 'rd' if listing['floor'] == 3 else 'th'
        strengths.append(f"{listing['floor']}{suffix} floor (above street noise)")
    if listing.get("exposure") and "double" in (listing.get("exposure") or "").lower():
        strengths.append(f"double exposure ({listing['exposure']})")
    if any(k in cond_lower for k in ["perfect", "renovated", "showcase", "good,"]):
        strengths.append(f"condition: {listing['condition']}")
    if listing.get("year_built") and listing["year_built"] < 1900:
        strengths.append(f"period building ({listing['year_built']}s)")
    if listing.get("features"):
        for f in listing["features"][:3]:
            strengths.append(f)
    if strengths:
        parts.append("**Strengths:** " + ", ".join(strengths) + ".")

    # Concerns
    concerns = []
    if listing.get("exposure") and "north" in listing["exposure"].lower():
        concerns.append("north exposure (less natural light)")
    if listing.get("floor") == 1 and not listing.get("features", []):
        concerns.append("ground/first floor (street noise)")
    if listing.get("elevator") is False:
        concerns.append("no elevator")
    if "unknown" in cond_lower:
        concerns.append("condition not visible from listing photo")
    if is_dated:
        concerns.append("photos show dated finishes (renovation budget required)")
    if listing.get("dpe_class") and listing["dpe_class"] in ("D", "E", "F", "G"):
        concerns.append(f"DPE class {listing['dpe_class']} (potential future works)")
    if concerns:
        parts.append("**Concerns:** " + ", ".join(concerns) + ".")

    if listing.get("notes"):
        parts.append(f"**Notes:** {listing['notes']}")

    return "\n\n".join(parts)


# ============================================================
# 4. Run pipeline
# ============================================================
def main():
    print("Loading DVF…")
    cleaned = {arr: _clean(_load_arr(arr)) for arr in DVF_ARRS}
    arr_stats = {arr: _arr_overall(df) for arr, df in cleaned.items()}

    listings_out = []
    for L in LISTINGS:
        arr = L["arr"]
        df = cleaned.get(arr, pd.DataFrame())
        overall = arr_stats.get(arr, {})
        band = _bucket_stats(df, L.get("surface_m2"))

        ask_per_m2 = None
        verdict_key = None
        delta_med = None
        if L.get("price_eur") and L.get("surface_m2"):
            ask_per_m2 = L["price_eur"] / L["surface_m2"]
            if band:
                verdict_key, _ = _verdict(ask_per_m2, band["p25"], band["p75"])
                delta_med = (ask_per_m2 - band["median"]) / band["median"] * 100

        analysis = _expert_analysis(L, overall, band)
        resolved_url, url_kind = _listing_url(L)

        listings_out.append({
            **L,
            "url": resolved_url,
            "url_kind": url_kind,
            "price_per_m2": round(ask_per_m2) if ask_per_m2 else None,
            "dvf_arr_median": round(overall["median"]) if overall else None,
            "dvf_arr_n": overall.get("n") if overall else None,
            "dvf_band_median": round(band["median"]) if band else None,
            "dvf_band_p25": round(band["p25"]) if band else None,
            "dvf_band_p75": round(band["p75"]) if band else None,
            "dvf_band_n": band.get("n") if band else None,
            "dvf_band_label": band.get("band") if band else None,
            "verdict": verdict_key,
            "premium_vs_median_pct": round(delta_med, 1) if delta_med is not None else None,
            "expert_analysis": analysis,
        })

    payload = {
        "generated_at": str(date.today()),
        "filter_criteria": {
            "budget_eur": [1_500_000, 2_500_000],
            "surface_m2": [80, 200],
            "geography": "Paris arrondissements 1-9 + 16",
        },
        "arrondissement_stats": {
            arr: {**stats, "arr_name": arr_name(arr)}
            for arr, stats in arr_stats.items() if stats
        },
        "listings": listings_out,
    }

    # Ensure verdict is set for needs-data entries so the dashboard can filter
    for L in payload["listings"]:
        if L.get("needs_data") and not L.get("verdict"):
            L["verdict"] = "needs-data"

    json_str = json.dumps(payload, indent=2, ensure_ascii=False)
    (OUT_DIR / "listings.json").write_text(json_str)
    print(f"Wrote {OUT_DIR / 'listings.json'} ({len(listings_out)} listings)")

    # Render self-contained dashboard.html from template
    template_path = DATA_DIR / "dashboard_template.html"
    template = template_path.read_text()
    # Escape '</script>' inside the JSON to prevent breaking out of the script tag
    safe_json = json_str.replace("</", "<\\/")
    rendered = template.replace("__LISTINGS_DATA_JSON__", safe_json)
    (OUT_DIR / "dashboard.html").write_text(rendered)
    print(f"Wrote {OUT_DIR / 'dashboard.html'} (self-contained, no sibling files needed)")

    # Clean up obsolete listings.js if present
    js_path = OUT_DIR / "listings.js"
    if js_path.exists():
        js_path.unlink()
        print(f"Removed obsolete {js_path}")

    # Quick console summary
    print("\n=== Listings analyzed ===")
    for L in listings_out:
        ppm = L.get("price_per_m2")
        v = L.get("verdict") or "needs-data"
        print(f"  {L['arr_name']:<12} | €{(L['price_eur'] or 0)/1e6:.2f}M | "
              f"{(L.get('surface_m2') or 0):>5.0f} m² | "
              f"{(f'€{ppm:,}' if ppm else '—'):>10} /m² | {v:<13} | {L['title'][:50]}")


if __name__ == "__main__":
    main()
