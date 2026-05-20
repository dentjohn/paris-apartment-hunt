"""Cross-arrondissement DVF comparison for the subject property.

Applies the identical cleaning pipeline from analyze_dvf.py across the
2nd, 3rd, 4th, and 11th arrondissements so the medians are directly
comparable.
"""

from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent
SUBJECT_PRICE_PER_M2 = 10_750

ARRS = {
    "75102": "Paris 2nd (Sentier/Bourse)",
    "75103": "Paris 3rd (subject)",
    "75104": "Paris 4th (Marais/Île St-Louis)",
    "75110": "Paris 10th (Faubourg St-Denis/Gare du Nord)",
    "75111": "Paris 11th (Oberkampf/Bastille)",
}
YEARS = [2024, 2025]


def load(arr: str) -> pd.DataFrame:
    frames = [pd.read_csv(DATA_DIR / f"dvf_{arr}_{y}.csv", low_memory=False) for y in YEARS]
    return pd.concat(frames, ignore_index=True)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date_mutation"] = pd.to_datetime(df["date_mutation"], errors="coerce")
    df = df[df["nature_mutation"] == "Vente"]

    has_non_apt = (
        df.assign(other=df["type_local"].notna() & (df["type_local"] != "Appartement"))
        .groupby("id_mutation")["other"]
        .any()
    )
    keep_ids = has_non_apt[~has_non_apt].index
    df = df[df["id_mutation"].isin(keep_ids)]

    df = df[df["type_local"] == "Appartement"]
    df = df.dropna(subset=["valeur_fonciere", "surface_reelle_bati"])
    df = df[(df["valeur_fonciere"] > 0) & (df["surface_reelle_bati"] > 0)]

    agg = (
        df.groupby("id_mutation")
        .agg(
            date_mutation=("date_mutation", "first"),
            valeur_fonciere=("valeur_fonciere", "first"),
            surface=("surface_reelle_bati", "sum"),
            adresse=("adresse_nom_voie", "first"),
            numero=("adresse_numero", "first"),
            code_commune=("code_commune", "first"),
        )
        .reset_index()
    )
    agg["eur_per_m2"] = agg["valeur_fonciere"] / agg["surface"]
    return agg[(agg["eur_per_m2"] >= 5_000) & (agg["eur_per_m2"] <= 30_000)]


def bucket(s):
    if s < 50: return "<50"
    if s < 80: return "50-80"
    if s < 120: return "80-120"
    if s < 200: return "120-200"
    return "200+"


def stats(s: pd.Series) -> dict:
    return {
        "n": len(s),
        "median": s.median(),
        "mean": s.mean(),
        "p10": s.quantile(0.10),
        "p25": s.quantile(0.25),
        "p75": s.quantile(0.75),
        "p90": s.quantile(0.90),
    }


cleaned = {arr: clean(load(arr)) for arr in ARRS}

# Overall comparison
overall_rows = []
for arr, label in ARRS.items():
    s = cleaned[arr]["eur_per_m2"]
    row = {"arr": arr, "label": label, **stats(s)}
    row["pct_above_subject"] = (s > SUBJECT_PRICE_PER_M2).mean() * 100
    overall_rows.append(row)
overall = pd.DataFrame(overall_rows)
print("=== OVERALL €/m², 2024-2025, all apartment-only sales ===")
print(overall.to_string(index=False, float_format=lambda x: f"{x:,.0f}"))

# 120-200 m² band (subject's surface class)
print("\n=== SUBJECT SURFACE BAND (120-200 m²) ===")
band_rows = []
for arr, label in ARRS.items():
    df = cleaned[arr]
    band = df[(df["surface"] >= 120) & (df["surface"] < 200)]["eur_per_m2"]
    band_rows.append({"arr": arr, "label": label, **stats(band)})
band_df = pd.DataFrame(band_rows)
print(band_df.to_string(index=False, float_format=lambda x: f"{x:,.0f}"))

# Wider band 80-250 m² for sample-size robustness
print("\n=== WIDER BAND (80-250 m²) for sample robustness ===")
wide_rows = []
for arr, label in ARRS.items():
    df = cleaned[arr]
    band = df[(df["surface"] >= 80) & (df["surface"] <= 250)]["eur_per_m2"]
    wide_rows.append({"arr": arr, "label": label, **stats(band)})
wide_df = pd.DataFrame(wide_rows)
print(wide_df.to_string(index=False, float_format=lambda x: f"{x:,.0f}"))

# By bucket, by arr
print("\n=== €/m² MEDIAN BY SURFACE BUCKET × ARR ===")
buckets_order = ["<50", "50-80", "80-120", "120-200", "200+"]
matrix = pd.DataFrame(index=buckets_order)
counts = pd.DataFrame(index=buckets_order)
for arr, label in ARRS.items():
    df = cleaned[arr].copy()
    df["b"] = df["surface"].apply(bucket)
    matrix[arr] = df.groupby("b")["eur_per_m2"].median().reindex(buckets_order)
    counts[arr] = df.groupby("b")["eur_per_m2"].size().reindex(buckets_order)
print("Medians:")
print(matrix.to_string(float_format=lambda x: f"{x:,.0f}"))
print("\nSample sizes:")
print(counts.to_string())

overall.to_csv(DATA_DIR / "cross_arr_overall.csv", index=False)
band_df.to_csv(DATA_DIR / "cross_arr_subject_band.csv", index=False)
wide_df.to_csv(DATA_DIR / "cross_arr_wide_band.csv", index=False)
matrix.to_csv(DATA_DIR / "cross_arr_bucket_medians.csv")
counts.to_csv(DATA_DIR / "cross_arr_bucket_counts.csv")
