"""Street-level comp analysis for the subject property on rue Sainte-Apolline.

Compares the northern edge of 75003 (around Porte Saint-Denis / Réaumur) against
the Marais core (rues de Turenne, Bretagne, Vieille-du-Temple, etc.) to test
the hypothesis that the subject's location explains its sub-median €/m².
"""

from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent
df = pd.read_csv(DATA_DIR / "dvf_75103_clean.csv")
df["adresse"] = df["adresse"].fillna("").str.upper()

# Geographic clusters within 75003
NORTHERN_EDGE = [
    "SAINTE APOLLINE", "STE APOLLINE", "BLONDEL", "MESLAY", "VOLTA",
    "PORTE ST DENIS", "PORTE SAINT DENIS", "SAINT-DENIS", "ST DENIS",
    "DUSSOUBS", "FORTUNY", "PALESTRO",
]
MARAIS_CORE = [
    "TURENNE", "BRETAGNE", "VIEILLE DU TEMPLE", "VIEILLE-DU-TEMPLE",
    "FRANCS BOURGEOIS", "FRANCS-BOURGEOIS", "ARCHIVES", "ROSIERS",
    "SAINTONGE", "POITOU", "PERLE", "DEBELLEYME", "ELZEVIR",
    "PAYENNE", "FROISSART", "PICASSO",
]

def label(addr: str) -> str:
    for k in NORTHERN_EDGE:
        if k in addr:
            return "Northern edge"
    for k in MARAIS_CORE:
        if k in addr:
            return "Marais core"
    return "Other 75003"

df["cluster"] = df["adresse"].apply(label)

# Restrict to the subject's surface class for fair comparison
band = df[(df["surface"] >= 80) & (df["surface"] <= 250)].copy()

summary = (
    band.groupby("cluster")
    .agg(
        n=("eur_per_m2", "size"),
        median_eur_m2=("eur_per_m2", "median"),
        p25=("eur_per_m2", lambda s: s.quantile(0.25)),
        p75=("eur_per_m2", lambda s: s.quantile(0.75)),
        median_surface=("surface", "median"),
        median_price=("valeur_fonciere", "median"),
    )
    .reset_index()
    .sort_values("median_eur_m2", ascending=False)
)

print("=== €/m² by location cluster, 80-250 m² apartments only ===")
print(summary.to_string(index=False))

# All northern-edge sales (any size) — small dataset, list them
ne_all = df[df["cluster"] == "Northern edge"].sort_values("eur_per_m2")
print(f"\n=== All {len(ne_all)} Northern edge sales (any size), 2024-2025 ===")
cols = ["date_mutation", "numero", "adresse", "surface", "valeur_fonciere", "eur_per_m2"]
print(ne_all[cols].to_string(index=False))

# Specifically rue Sainte-Apolline
sa = df[df["adresse"].str.contains("APOLLINE")]
print(f"\n=== Rue Sainte-Apolline sales (any size): {len(sa)} ===")
if len(sa):
    print(sa[cols].to_string(index=False))

summary.to_csv(DATA_DIR / "summary_by_cluster.csv", index=False)
ne_all.to_csv(DATA_DIR / "northern_edge_sales.csv", index=False)
