"""DVF analysis for Paris 3rd (75103).

Loads geo-DVF CSVs for 2024 and 2025, isolates clean apartment sales, and
produces summary statistics + a per-sale CSV for downstream charting.

Key DVF gotchas handled:
  - A single `id_mutation` (one sale) can have multiple CSV rows: one per
    lot or parcel. The `valeur_fonciere` is the *total* sale price, repeated
    on every row. We must group by `id_mutation` to avoid double-counting.
  - Many sales bundle an apartment with a cellar (`Dependance`) or parking
    (`Local industriel ...`). If we only sum apartment surface but use the
    full sale price, €/m² is inflated. We drop mutations that include any
    non-apartment local type, which is conservative but defensible.
  - VEFA / new-build sales (`Vente en l'etat futur d'achevement`) trade at
    different prices than resales; we keep only `Vente` (existing stock).
  - DVF lacks a quality/condition field, so outliers can be genuine (a wreck
    or a fully-renovated piano nobile). We trim hard outliers (< €5,000/m²
    or > €30,000/m²) as data errors rather than market signal.
"""

import sys
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent
SUBJECT_PRICE_PER_M2 = 10_750  # asking, EUR/m2

YEARS = [2024, 2025]


def load() -> pd.DataFrame:
    frames = [pd.read_csv(DATA_DIR / f"dvf_75103_{y}.csv", low_memory=False) for y in YEARS]
    return pd.concat(frames, ignore_index=True)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date_mutation"] = pd.to_datetime(df["date_mutation"], errors="coerce")
    df = df[df["nature_mutation"] == "Vente"]

    # Drop mutations that include any non-apartment local (parking, shop, etc.)
    # so that valeur_fonciere matches the surface we sum.
    has_non_apt = (
        df.assign(other=df["type_local"].notna() & (df["type_local"] != "Appartement"))
        .groupby("id_mutation")["other"]
        .any()
    )
    keep_ids = has_non_apt[~has_non_apt].index
    df = df[df["id_mutation"].isin(keep_ids)]

    # Keep apartment rows only and group by sale.
    df = df[df["type_local"] == "Appartement"]
    df = df.dropna(subset=["valeur_fonciere", "surface_reelle_bati"])
    df = df[(df["valeur_fonciere"] > 0) & (df["surface_reelle_bati"] > 0)]

    agg = (
        df.groupby("id_mutation")
        .agg(
            date_mutation=("date_mutation", "first"),
            valeur_fonciere=("valeur_fonciere", "first"),  # repeated on every row
            surface=("surface_reelle_bati", "sum"),
            pieces=("nombre_pieces_principales", "sum"),
            adresse=("adresse_nom_voie", "first"),
            numero=("adresse_numero", "first"),
            code_postal=("code_postal", "first"),
            n_rows=("id_mutation", "size"),
        )
        .reset_index()
    )

    agg["eur_per_m2"] = agg["valeur_fonciere"] / agg["surface"]

    # Outlier trim
    trimmed = agg[(agg["eur_per_m2"] >= 5_000) & (agg["eur_per_m2"] <= 30_000)].copy()
    return trimmed


def bucket(s: float) -> str:
    if s < 50:
        return "<50"
    if s < 80:
        return "50-80"
    if s < 120:
        return "80-120"
    if s < 200:
        return "120-200"
    return "200+"


def summarize(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    overall = pd.DataFrame(
        {
            "metric": ["n_sales", "median_eur_per_m2", "mean_eur_per_m2",
                      "p25", "p75", "p10", "p90",
                      "median_price", "median_surface"],
            "value": [
                len(df),
                df["eur_per_m2"].median(),
                df["eur_per_m2"].mean(),
                df["eur_per_m2"].quantile(0.25),
                df["eur_per_m2"].quantile(0.75),
                df["eur_per_m2"].quantile(0.10),
                df["eur_per_m2"].quantile(0.90),
                df["valeur_fonciere"].median(),
                df["surface"].median(),
            ],
        }
    )

    df = df.copy()
    df["surface_bucket"] = df["surface"].apply(bucket)
    order = ["<50", "50-80", "80-120", "120-200", "200+"]

    by_bucket = (
        df.groupby("surface_bucket")
        .agg(
            n=("eur_per_m2", "size"),
            median=("eur_per_m2", "median"),
            mean=("eur_per_m2", "mean"),
            p25=("eur_per_m2", lambda s: s.quantile(0.25)),
            p75=("eur_per_m2", lambda s: s.quantile(0.75)),
            median_price=("valeur_fonciere", "median"),
            median_surface=("surface", "median"),
        )
        .reindex(order)
        .reset_index()
    )
    return overall, by_bucket


def main() -> int:
    raw = load()
    print(f"Loaded {len(raw):,} raw DVF rows from {YEARS}")

    clean_df = clean(raw)
    print(f"Clean apartment sales (apt-only mutations, trimmed): {len(clean_df):,}")

    overall, by_bucket = summarize(clean_df)
    print("\n=== OVERALL ===")
    print(overall.to_string(index=False))
    print("\n=== BY SURFACE BUCKET ===")
    print(by_bucket.to_string(index=False))

    clean_df.sort_values("date_mutation").to_csv(DATA_DIR / "dvf_75103_clean.csv", index=False)
    overall.to_csv(DATA_DIR / "summary_overall.csv", index=False)
    by_bucket.to_csv(DATA_DIR / "summary_by_bucket.csv", index=False)

    # Subject-property positioning
    subj_pct = (clean_df["eur_per_m2"] < SUBJECT_PRICE_PER_M2).mean() * 100
    print(f"\nSubject asking €{SUBJECT_PRICE_PER_M2:,}/m² is above {subj_pct:.1f}% "
          f"of cleaned 2024-2025 sales.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
