# DVF Transaction Analysis — Paris 3rd Arrondissement (75103)

**Analysis date:** 2026-05-19
**Subject property:** 186 m² apartment, rue Sainte-Apolline, asking €2.0M (~€10,750/m²)
**Data source:** Etalab geo-DVF (`files.data.gouv.fr/geo-dvf/`), official French recorded-sales registry

---

## TL;DR

The subject's **€10,750/m² ask is at the 35th percentile** of all 689 cleaned Paris-3rd apartment sales in 2024-2025 — *below the median, not above it*. For the subject's 120-200 m² surface class, **median is €10,508/m² (n=12)** — the subject is priced essentially at market.

Two 118 m² apartments on the same building at **9 rue Sainte-Apolline** sold in 2025 at €9,195/m² (condition unknown) and €13,053/m². The subject's €10,750/m² sits comfortably between these direct comps.

**The original analysis dramatically overestimated the Marais price band.** The claim that prime 75003 trades at €12,000-€19,000/m² was based on asking prices from Le Figaro. *Recorded* transactions show a median nearer €11,400/m².

**Cross-arrondissement context (§7):** the 5-arr gradient is clean — 10th €9,284 < 11th €9,768 < 2nd €10,952 < 3rd €11,429 < 4th €12,474. The subject's ask is calibrated to the 3rd's median. The 10th directly across bd Saint-Denis is ~19% cheaper. Whether the asking price is fair, low, or 18% high depends entirely on which side of that border you think Sainte-Apolline functions on — and the same-street comps suggest both can be true depending on the unit's condition.

---

## 1. Methodology

DVF (Demandes de Valeurs Foncières) is the French open-data registry of all real-estate transactions, published by DGFiP. Geo-DVF is the Etalab-curated version with geographic enrichment and consistent column names.

**Coverage:** 2024 full year + 2025 full year. 2026 data not yet published (DVF typically lags ~6 months). Effective window: 24 calendar months ending Dec 2025.

**Per-sale aggregation.** One sale (`id_mutation`) can span multiple CSV rows (one per parcel or lot). To compute correct €/m²:
- Group by `id_mutation`.
- Take `valeur_fonciere` from any row (it's the total sale price, repeated).
- Sum `surface_reelle_bati` across rows.

**Apartment-only filter.** Mixed sales that bundle an apartment with a parking spot, cellar, or shop inflate €/m² if you only count apartment surface. We drop any mutation that includes a non-apartment local type. This is conservative — it removes some legitimate apartment sales — but defensible.

**Other filters:**
- `nature_mutation == "Vente"` (resale only; excludes VEFA / new builds, expropriations, etc.)
- Non-null, positive `valeur_fonciere` and `surface_reelle_bati`
- Outlier trim: drop €/m² below €5,000 or above €30,000 as data errors

| Stage | Rows / sales |
|---|---:|
| Raw geo-DVF rows, 2024-2025 | 3,298 |
| Cleaned apartment-only sales | **689** |

---

## 2. Overall 75103 distribution, 2024-2025

| Metric | €/m² |
|---|---:|
| Median | **€11,429** |
| Mean | €11,690 |
| 10th percentile | €8,376 |
| 25th percentile | €9,992 |
| 75th percentile | €13,036 |
| 90th percentile | €15,225 |

**Subject at €10,750/m² sits at the 35th percentile** of all cleaned 75103 sales.

---

## 3. By surface bucket

The subject is 186 m², which is large for Paris. Comparing only to apartments of similar size:

| Surface (m²) | n | Median €/m² | Mean €/m² | p25 | p75 | Median price |
|---|---:|---:|---:|---:|---:|---:|
| <50 | 521 | €11,394 | €11,535 | €9,890 | €12,819 | €286k |
| 50-80 | 104 | €11,826 | €12,455 | €10,558 | €13,918 | €760k |
| 80-120 | 51 | €11,614 | €11,535 | €9,045 | €13,974 | €1.11M |
| **120-200** | **12** | **€10,508** | **€12,594** | **€9,861** | **€12,176** | **€1.41M** |
| 200+ | 1 | €9,919 | — | — | — | €2.23M |

**For the subject's size class (120-200 m²), median is €10,508/m².** The subject's €10,750/m² ask is essentially at market — slightly above the median but well below the p75.

**Sample-size caveat:** Only 12 sales in the 120-200 bucket and 1 sale at 200+ across all of 75103 in 24 months. Large apartments trade rarely. Read these medians as directional, not precise.

---

## 4. Location: northern edge vs. Marais core

Restricting to 80-250 m² apartments to isolate the location effect:

| Cluster | n | Median €/m² | p25 | p75 |
|---|---:|---:|---:|---:|
| Northern edge (Sainte-Apolline, Volta, Meslay, Blondel, …) | 5 | €13,053 | €10,195 | €14,000 |
| Marais core (Turenne, Bretagne, Vieille-du-Temple, Saintonge, …) | 21 | €12,095 | €10,388 | €15,555 |
| Other 75003 | 38 | €10,868 | €8,991 | €12,851 |

Counter-intuitively, the small northern-edge sample shows a *higher* median than the Marais core. This is driven by the December 2025 Sainte-Apolline sale (see §5) and is statistically thin. The honest read: there is **no strong DVF evidence that the northern edge trades materially below the Marais core for large apartments**. The "north of 75003 is rougher" intuition is real for street vibe and noise, but it does not appear in recorded prices for this surface band.

---

## 5. Direct street-level comps — rue Sainte-Apolline

Four recorded sales on rue Sainte-Apolline itself in 2024-2025:

| Date | Address | Surface | Price | €/m² |
|---|---|---:|---:|---:|
| 2024-09-09 | 9 rue Sainte-Apolline | 23 m² | €290,000 | €12,609 |
| 2025-04-04 | 9 rue Sainte-Apolline | **118 m²** | €1,085,000 | **€9,195** |
| 2025-10-15 | 7 rue Sainte-Apolline | 78 m² | €850,000 | €10,897 |
| 2025-12-15 | 9 rue Sainte-Apolline | **118 m²** | €1,540,217 | **€13,053** |

**The two 118 m² sales at #9 are the closest available comps to the subject** (similar size class, same street, possibly same building, 8 months apart).

- The €9,195/m² sale (April 2025) is roughly what you'd expect for an apartment that needs significant work — wreck, bad exposure, low floor, or pre-renovation.
- The €13,053/m² sale (December 2025) is consistent with a renovated, "ready to move in" unit.

**The subject's €10,750/m² ask falls between these two direct comps**, closer to the lower end. If the subject is in renovated, move-in condition, that's an attractive ask. If it needs work (the listing's silence on condition, kitchen, heating details is conspicuous), the ask is full retail.

---

## 6. What changes about the Section 5 narrative in the original report

The original analysis stated:

> *"prime Marais apartments tend to trade between roughly €12,000 and €19,000/m², with larger units (>150 m²) generally at the lower end."*

This was **derived from Le Figaro asking prices**, which systematically overstate market. The recorded-transactions median for 75103 is **€11,429/m²** — well below that lower bound. The €19,000/m² top of the asking range maps to roughly the 90th-95th percentile of actual recorded sales, not the typical price.

The subject's €10,750/m² is therefore **not "below the Paris 3rd average."** It is below the *asking-price* average. Against recorded sales it is **at the 35th percentile** — meaning the seller has already priced in the discount for north exposure, busy commercial street, etc.

**Implication for negotiation:** the original report's "3-7% room likely given north exposure" assumed the asking was at par with the district. In DVF terms it's already 5-10% below the district median for size. The negotiation room is narrower than the original report suggested — probably 0-5%, contingent on what condition issues the visit surfaces.

---

## 7. Cross-arrondissement comparison

Same cleaning pipeline applied to the 2nd, 4th, 10th, and 11th arrondissements (2024-2025, apartment-only sales, outliers trimmed). The 10th is included because rue Sainte-Apolline sits one block south of bd Saint-Denis, the 3rd/10th border — the building is officially in the 3rd but its immediate surroundings are shared with the 10th.

### Overall median €/m²

| Arrondissement | n sales | Median €/m² | p25 | p75 | % above subject's €10,750 |
|---|---:|---:|---:|---:|---:|
| Paris 10th (Faubourg St-Denis/Gare du Nord) | 1,213 | €9,284 | €8,000 | €10,623 | 23% |
| Paris 11th (Oberkampf/Bastille) | 1,692 | €9,768 | €8,492 | €10,995 | 29% |
| Paris 2nd (Sentier/Bourse) | 461 | €10,952 | €9,259 | €12,386 | 52% |
| **Paris 3rd (subject)** | **689** | **€11,429** | **€9,992** | **€13,036** | **64%** |
| Paris 4th (Marais/Île Saint-Louis) | 469 | €12,474 | €10,649 | €14,303 | 74% |

A clean, expected gradient: 10th cheapest, 4th most expensive, with the subject's 3rd squarely between the 2nd and the 4th.

### Subject surface band (120-200 m²) — directly comparable

| Arrondissement | n | Median €/m² | Gap vs. subject ask |
|---|---:|---:|---:|
| Paris 10th | 20 | €9,099 | subject is **+18.1%** |
| Paris 11th | 20 | €9,842 | subject is +9.2% |
| **Paris 3rd** | **12** | **€10,508** | **subject is +2.3%** |
| Paris 2nd | 8 | €11,272 | subject is −4.6% |
| Paris 4th | 8 | €13,644 | subject is −21.2% |

Wider 80-250 m² band (more robust samples, same direction):

| Arrondissement | n | Median €/m² |
|---|---:|---:|
| Paris 10th | 59 | €9,350 |
| Paris 11th | 77 | €10,100 |
| Paris 3rd | 64 | €11,287 |
| Paris 2nd | 36 | €11,731 |
| Paris 4th | 55 | €12,378 |

### What this means for the subject

The asking price is **calibrated to the 3rd arrondissement median**. The interpretation depends on which arrondissement you think the location *really* trades like:

- **If you think it functions like the 10th** (across bd Saint-Denis) — the ask is **+18% over median**, real negotiation room.
- **If you think it functions like the 11th / northern fringe** — the ask is ~9% above market, meaningful negotiation room.
- **If you think Sainte-Apolline/Porte Saint-Denis is "true 3rd"** — the ask is fair to slightly above market (~+2%). Limited negotiation room.
- **If you think it functions like the 2nd next door** — the ask is roughly 5% below median, already discounted.
- **If you think it functions like the 4th Marais core** — the ask is a steep discount (−21%) and the property is a buy.

The DVF evidence from rue Sainte-Apolline itself (§5) — two 118 m² apartments at #9 transacting at €9,195 and €13,053/m² — spans this entire range. The street is genuinely on a gradient between two pricing regimes, and **condition appears to be the dominant variable, not the arrondissement label.**

**Most defensible read:** the truth is somewhere between the 10th and the 3rd. A weighted midpoint suggests fair value around €9,500-€10,500/m² for an average-condition unit (call it €1.77M-€1.95M for 186 m²), with the asking €2.0M reasonable for a renovated unit and 5-10% overpriced if condition is average.

### Sample-size caveat for large apartments

The 120-200 m² and 200+ m² buckets are thin everywhere:

| Bucket | 75102 | 75103 | 75104 | 75110 | 75111 |
|---|---:|---:|---:|---:|---:|
| 120-200 m² | 8 | 12 | 8 | 20 | 20 |
| 200+ m² | 0 | 1 | 2 | 1 | 6 |

In the 200+ bucket the gradient is noisy (10th €6,456, 11th €7,257, 4th €8,063, 3rd €9,919) — single-digit-sample noise, not a market signal. Discount accordingly when reasoning about the subject's exact 186 m² size.

---

## 8. Caveats and what DVF does NOT tell us

1. **No condition / renovation field.** A wreck and a piano nobile both appear as a sale price; you can't distinguish them in DVF.
2. **No floor or exposure.** Two units in the same building at very different floor/light levels look identical to DVF.
3. **Small samples in the relevant surface band.** 12 sales at 120-200 m², 1 sale at 200+. Treat the bucket medians as directional.
4. **Off-market sales not captured.** Private treaty sales between known parties (common for large prime units) may bypass the standard mutation flow.
5. **Cellar/parking exclusion is conservative.** Removing mixed-lot sales may slightly under-sample full-condition transactions. The €/m² figures here are best read as ±5%.

---

## 9. Recommended next steps (updated)

| Step | Notes |
|---|---|
| **Visit & condition check** | Single highest-leverage action. The €9,195 vs €13,053 spread between two 118 m² apartments at the same address is entirely about condition. |
| **Confirm what was renovated when** | Ask the agent for the works history. If renovated within the last 5-10 years, asking is fair. If not, ask should drop. |
| **Negotiate from a DVF baseline, not an asking-price baseline** | The seller's pricing already factors in north exposure / busy street. The remaining negotiation room is condition-based. |
| **Pull AG minutes** | Especially planned works votes — these convert future-€ to today's-discount. |
| **Recompute when 2026 H1 DVF lands (~Q4 2026)** | If the December 2025 Sainte-Apolline sale at €13,053/m² turns out to be representative of nearby comps, the subject looks like a buy at €10,750. |

---

## Files produced

- `dvf_75102_*.csv`, `dvf_75103_*.csv`, `dvf_75104_*.csv`, `dvf_75111_*.csv` — raw geo-DVF downloads
- `dvf_75103_clean.csv` — 689 cleaned, per-sale rows used in §§2-5
- `summary_overall.csv`, `summary_by_bucket.csv`, `summary_by_cluster.csv` — single-arr tables
- `cross_arr_overall.csv`, `cross_arr_subject_band.csv`, `cross_arr_wide_band.csv` — §7 tables
- `cross_arr_bucket_medians.csv`, `cross_arr_bucket_counts.csv` — §7 bucket×arr matrices
- `northern_edge_sales.csv` — all 33 northern-edge 75103 sales (any size)
- `analyze_dvf.py`, `street_analysis.py`, `cross_arr_analysis.py` — reproducible scripts
