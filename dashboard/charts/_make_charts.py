"""Generate the three DVF distribution charts as PNGs."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, "/Users/johndent/Documents/paris-apartment")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

from build_dashboard import _clean, _load_arr, DVF_ARRS

OUT = Path("/Users/johndent/Documents/paris-apartment/dashboard/charts")
OUT.mkdir(parents=True, exist_ok=True)

# ----- styling -----
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "axes.edgecolor": "#444",
    "axes.labelcolor": "#222",
    "axes.titlesize": 11,
    "axes.titleweight": "bold",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": "#dddddd",
    "grid.linewidth": 0.6,
    "xtick.color": "#444",
    "ytick.color": "#444",
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})

ARR_NAMES = {
    "75102": "2e (Bourse)",
    "75103": "3e (Temple/Marais)",
    "75104": "4e (Hôtel-de-Ville)",
    "75106": "6e (Luxembourg)",
    "75107": "7e (Palais-Bourbon)",
    "75108": "8e (Élysée)",
    "75110": "10e (Entrepôt)",
    "75111": "11e (Popincourt)",
}

# Colour palette: tab10 ordered for the 8 arrs
palette = plt.get_cmap("tab10").colors
COLORS = {arr: palette[i] for i, arr in enumerate(DVF_ARRS)}


def euro_k(x, _pos=None):
    if x >= 1_000_000:
        return f"€{x/1_000_000:.1f}M"
    if x >= 1_000:
        return f"€{int(round(x/1_000))}k"
    return f"€{int(x)}"


# ----- load all data once -----
data = {}
for arr in DVF_ARRS:
    df = _clean(_load_arr(arr))
    data[arr] = df
    print(f"{arr}: n={len(df)}  med €/m² = {df['eur_per_m2'].median():,.0f}")


# ======================================================================
# Chart 1 — eur_per_m2_distributions.png
# ======================================================================
fig, axes = plt.subplots(2, 4, figsize=(14, 8), sharex=True)
axes_flat = axes.flatten()

# Common x range from 5th-95th pooled percentile for visual consistency
pooled = pd.concat([d["eur_per_m2"] for d in data.values()])
x_min, x_max = pooled.quantile(0.02), pooled.quantile(0.99)
bins = np.linspace(x_min, x_max, 36)

for ax, arr in zip(axes_flat, DVF_ARRS):
    df = data[arr]
    vals = df["eur_per_m2"].values
    n = len(vals)
    med = np.median(vals)
    p25, p75 = np.percentile(vals, [25, 75])

    ax.hist(vals, bins=bins, color=COLORS[arr], edgecolor="white", linewidth=0.5, alpha=0.85)
    ax.axvline(med, color="#222", linestyle="-", linewidth=1.5, label=f"median {euro_k(med)}")
    ax.axvline(p25, color="#222", linestyle="--", linewidth=1.0, alpha=0.7)
    ax.axvline(p75, color="#222", linestyle="--", linewidth=1.0, alpha=0.7)

    ax.set_title(f"{ARR_NAMES[arr]}  (n={n})")
    ax.xaxis.set_major_formatter(FuncFormatter(euro_k))
    ax.tick_params(axis="x", labelsize=8)
    ax.tick_params(axis="y", labelsize=8)
    ax.set_xlim(x_min, x_max)
    # annotate median in upper right
    ax.text(0.97, 0.92, f"med {euro_k(med)}", transform=ax.transAxes,
            ha="right", va="top", fontsize=8.5, color="#222",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#bbb", linewidth=0.5))

for ax in axes[:, 0]:
    ax.set_ylabel("sales")
for ax in axes[-1, :]:
    ax.set_xlabel("€ / m²")

fig.suptitle("Apartment €/m² distributions — DVF 2024–2026 (cleaned)", fontsize=14, fontweight="bold", y=1.00)
fig.tight_layout()
out1 = OUT / "eur_per_m2_distributions.png"
fig.savefig(out1, dpi=120, bbox_inches="tight")
plt.close(fig)
print("saved", out1)


# ======================================================================
# Chart 2 — arr_comparison_violin.png
# ======================================================================
# sort cheapest-first; with horizontal violin, item 1 is plotted at the bottom,
# so reverse so the cheapest sits at the bottom and priciest at the top
order = sorted(DVF_ARRS, key=lambda a: data[a]["eur_per_m2"].median())
vals_list = [data[a]["eur_per_m2"].values for a in order]
medians = [np.median(v) for v in vals_list]

fig, ax = plt.subplots(figsize=(12, 8))
parts = ax.violinplot(vals_list, vert=False, showmedians=False, showextrema=False, widths=0.85)

for i, body in enumerate(parts["bodies"]):
    arr = order[i]
    body.set_facecolor(COLORS[arr])
    body.set_edgecolor("#333")
    body.set_alpha(0.75)
    body.set_linewidth(0.8)

# overlay box stats: p25, median, p75
for i, v in enumerate(vals_list, start=1):
    p25, med, p75 = np.percentile(v, [25, 50, 75])
    ax.plot([p25, p75], [i, i], color="#222", linewidth=2.5, solid_capstyle="butt")
    ax.plot(med, i, "o", color="white", markersize=7, markeredgecolor="#222", markeredgewidth=1.4, zorder=5)
    # label median to the right
    ax.text(p75 + (max(pooled) - min(pooled)) * 0.005, i, f"  {euro_k(med)}  (n={len(v)})",
            va="center", fontsize=9, color="#222")

ax.set_yticks(range(1, len(order) + 1))
ax.set_yticklabels([ARR_NAMES[a] for a in order])
ax.xaxis.set_major_formatter(FuncFormatter(euro_k))
ax.set_xlabel("€ / m²  (apartment sales, DVF 2024–2026)")
ax.set_title("Arrondissement price gradient — cheapest to priciest", fontsize=14, fontweight="bold", pad=12)
ax.set_axisbelow(True)
ax.grid(axis="x")
ax.grid(axis="y", visible=False)
# extend x range so labels fit
xmin = min(v.min() for v in vals_list)
xmax = max(v.max() for v in vals_list)
ax.set_xlim(xmin * 0.95, xmax * 1.12)

fig.tight_layout()
out2 = OUT / "arr_comparison_violin.png"
fig.savefig(out2, dpi=120, bbox_inches="tight")
plt.close(fig)
print("saved", out2)


# ======================================================================
# Chart 3 — listings_vs_dvf_scatter.png
# ======================================================================
LISTINGS = [
    ("75103", 186, 2_000_000, "Sainte-Apolline (subject)"),
    ("75106", 83,  1_700_000, "rue Jacob"),
    ("75107", 85,  1_860_000, "rue du Bac"),
    ("75108", 144, 1_930_000, "Parc Monceau"),
    ("75107", 130, 1_950_000, "Solférino"),
    ("75107", 125, 2_100_000, "Verneuil/Beaune"),
    ("75107", 135, 2_370_000, "Verneuil/St-Pères"),
]

fig, ax = plt.subplots(figsize=(13, 8))

for arr in DVF_ARRS:
    df = data[arr]
    band = df[(df["surface"] >= 80) & (df["surface"] <= 250)]
    ax.scatter(band["surface"], band["valeur_fonciere"],
               s=28, color=COLORS[arr], alpha=0.55, edgecolor="white", linewidth=0.4,
               label=f"{ARR_NAMES[arr]} (n={len(band)})")

# listings as gold stars
star_color = "#d4a017"  # gold
for arr, surf, price, label in LISTINGS:
    ax.scatter(surf, price, marker="*", s=380, color=star_color,
               edgecolor="#222", linewidth=1.2, zorder=10)
    # label slightly offset
    ax.annotate(label, (surf, price), xytext=(8, 6), textcoords="offset points",
                fontsize=9, color="#222", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="white",
                          edgecolor="#d4a017", linewidth=0.8, alpha=0.92))

ax.set_xlim(78, 255)
ax.set_xlabel("surface (m²)")
ax.set_ylabel("sale price")
ax.yaxis.set_major_formatter(FuncFormatter(euro_k))
ax.set_title("Active listings vs. recent DVF sales (80–250 m²)", fontsize=14, fontweight="bold", pad=12)

# legend with extra star entry
from matplotlib.lines import Line2D
handles, labels = ax.get_legend_handles_labels()
handles.append(Line2D([0], [0], marker="*", color="w", markerfacecolor=star_color,
                      markeredgecolor="#222", markersize=15, label="active listing"))
labels.append("active listing")
ax.legend(handles, labels, loc="upper left", fontsize=9, framealpha=0.95, ncol=2)

ax.set_axisbelow(True)
fig.tight_layout()
out3 = OUT / "listings_vs_dvf_scatter.png"
fig.savefig(out3, dpi=120, bbox_inches="tight")
plt.close(fig)
print("saved", out3)
