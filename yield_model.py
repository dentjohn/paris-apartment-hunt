"""Sensitivity & yield model for the rue Sainte-Apolline subject property.

All inputs at the top — tweak and rerun.

Outputs:
  acquisition_cost.csv  — price × renovation matrix, all-in cost
  carrying_cost.csv     — annual ownership cost breakdown
  rental_yield.csv      — gross & net yield at low/mid/high rent
  irr_sensitivity.csv   — total IRR by appreciation scenario × hold period
  buy_vs_rent.csv       — annual all-in carry vs. renting equivalent
"""

from pathlib import Path
import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent

# ============================================================
# Property
# ============================================================
SURFACE_M2 = 186.08
ASKING_EUR = 2_000_000              # ~€10,750/m²
PRICE_PER_M2_LOW = 9_500            # DVF 10th-band midpoint, average condition
PRICE_PER_M2_MID = 10_500           # blended 10th/3rd, average condition
PRICE_PER_M2_ASK = ASKING_EUR / SURFACE_M2  # ~€10,750

PRICE_SCENARIOS = {
    "Negotiated to 10th-band":  round(PRICE_PER_M2_LOW * SURFACE_M2),    # ~€1.77M
    "Negotiated to mid-band":   round(PRICE_PER_M2_MID * SURFACE_M2),    # ~€1.95M
    "Full ask":                 ASKING_EUR,                              #  €2.00M
}

# Renovation scenarios — anchored to the same-street €9,195→€13,053 spread
# (~€3,858/m² of value lift between condition extremes) and to typical Paris
# renovation cost benchmarks (€1.5k-€4k/m² for cosmetic to full gut).
RENO_SCENARIOS = {
    "Move-in ready":            0,
    "Cosmetic refresh":         100_000,
    "Significant works":        300_000,
    "Full gut renovation":      600_000,
}

# ============================================================
# Transaction & holding costs (France)
# ============================================================
NOTARY_PCT = 0.075                  # frais de notaire, resale: ~7-8%
EXIT_AGENCY_PCT = 0.040             # selling agency fees if buyer sells later

# Annual carrying costs (€ unless % indicated)
ANNUAL_CHARGES = 4_582              # from listing
ANNUAL_TAXE_FONCIERE = 3_335        # from listing
ANNUAL_INSURANCE = 1_200            # MRH for ~€2M property
ANNUAL_MAINT_RESERVE_PCT = 0.005    # 0.5% of value — Paris co-ownership reality
# IFI (Impôt sur la fortune immobilière) — applies above €1.3M net real estate
# at progressive rates. Approx blended rate at this price point: ~0.5-0.8%
# of the property value annually. Highly dependent on owner's full estate.
# Set to 0 if non-resident or if IFI exemption applies.
IFI_ANNUAL_PCT = 0.005              # 0.5% — conservative-ish mid estimate

# ============================================================
# Rental assumptions (Paris 75003, encadrement des loyers in force)
# ============================================================
# Achievable monthly rent per m² in 75003. Encadrement caps the headline
# figure; furnished/short-term lifts the floor. Quick ranges:
RENT_PER_M2_LOW = 25                # unfurnished, encadré
RENT_PER_M2_MID = 30                # furnished, mid market
RENT_PER_M2_HIGH = 35               # high-end furnished, complement de loyer
VACANCY_PCT = 0.08                  # ~1 month/year average for prime central
MGMT_PCT = 0.07                     # gestion locative (agency-managed)
# French rental income tax: highly buyer-specific. Use 30% effective rate
# as a planning placeholder (régime réel after deductions for a top-bracket
# resident; lower for micro-foncier or non-residents).
RENTAL_TAX_PCT = 0.30

# ============================================================
# Appreciation scenarios (annualized, in € terms)
# ============================================================
APPREC_SCENARIOS = {
    "Bear (Paris prime stagnant)":    -0.005,  # -0.5%/yr
    "Base (flat to mild recovery)":    0.010,  # +1.0%/yr
    "Bull (return to long-run trend)": 0.030,  # +3.0%/yr
}
HOLD_YEARS = [5, 10]


# ============================================================
# Models
# ============================================================
def acquisition_cost_matrix() -> pd.DataFrame:
    rows = []
    for pname, price in PRICE_SCENARIOS.items():
        notary = price * NOTARY_PCT
        for rname, reno in RENO_SCENARIOS.items():
            all_in = price + notary + reno
            rows.append({
                "Purchase scenario": pname,
                "Price (€)": price,
                "Notary 7.5% (€)": round(notary),
                "Renovation scenario": rname,
                "Reno budget (€)": reno,
                "All-in cost (€)": round(all_in),
                "€/m² all-in": round(all_in / SURFACE_M2),
            })
    return pd.DataFrame(rows)


def carrying_cost_table() -> pd.DataFrame:
    rows = []
    for pname, price in PRICE_SCENARIOS.items():
        maint = price * ANNUAL_MAINT_RESERVE_PCT
        ifi = price * IFI_ANNUAL_PCT
        total = ANNUAL_CHARGES + ANNUAL_TAXE_FONCIERE + ANNUAL_INSURANCE + maint + ifi
        rows.append({
            "Scenario": pname,
            "Charges (€)": ANNUAL_CHARGES,
            "Taxe foncière (€)": ANNUAL_TAXE_FONCIERE,
            "Insurance (€)": ANNUAL_INSURANCE,
            "Maint reserve 0.5% (€)": round(maint),
            "IFI ~0.5% (€)": round(ifi),
            "Annual total (€)": round(total),
            "Monthly (€)": round(total / 12),
        })
    return pd.DataFrame(rows)


def rental_yield_table() -> pd.DataFrame:
    rents = {
        "Low (encadré unfurnished, €25/m²)":  RENT_PER_M2_LOW * SURFACE_M2 * 12,
        "Mid (furnished, €30/m²)":            RENT_PER_M2_MID * SURFACE_M2 * 12,
        "High (premium furnished, €35/m²)":   RENT_PER_M2_HIGH * SURFACE_M2 * 12,
    }
    rows = []
    for pname, price in PRICE_SCENARIOS.items():
        all_in_no_reno = price * (1 + NOTARY_PCT)  # exclude reno for yield denominator
        maint = price * ANNUAL_MAINT_RESERVE_PCT
        ifi = price * IFI_ANNUAL_PCT
        carry = ANNUAL_CHARGES + ANNUAL_TAXE_FONCIERE + ANNUAL_INSURANCE + maint + ifi
        for rname, gross_rent in rents.items():
            effective_rent = gross_rent * (1 - VACANCY_PCT)
            mgmt = effective_rent * MGMT_PCT
            pretax_net = effective_rent - mgmt - carry
            posttax_net = pretax_net * (1 - RENTAL_TAX_PCT) if pretax_net > 0 else pretax_net
            rows.append({
                "Price scenario": pname,
                "Rent scenario": rname,
                "Gross rent (€)": round(gross_rent),
                "Effective rent after vacancy (€)": round(effective_rent),
                "Carrying cost (€)": round(carry + mgmt),
                "Pre-tax net (€)": round(pretax_net),
                "Post-tax net @30% (€)": round(posttax_net),
                "Gross yield %": round(gross_rent / all_in_no_reno * 100, 2),
                "Net yield % (pre-tax)": round(pretax_net / all_in_no_reno * 100, 2),
                "Net yield % (post-tax)": round(posttax_net / all_in_no_reno * 100, 2),
            })
    return pd.DataFrame(rows)


def irr_sensitivity() -> pd.DataFrame:
    """Total return (annualized) under each appreciation × hold-period scenario.

    Treats the apartment as a residence (no rental income). Captures only
    capital appreciation net of acquisition + exit friction. The buyer's
    'use value' (housing services consumed) is excluded — that's a separate
    line in the buy-vs-rent table.
    """
    rows = []
    for pname, price in PRICE_SCENARIOS.items():
        all_in_no_reno = price * (1 + NOTARY_PCT)
        for aname, rate in APPREC_SCENARIOS.items():
            for years in HOLD_YEARS:
                exit_price = price * (1 + rate) ** years
                exit_proceeds = exit_price * (1 - EXIT_AGENCY_PCT)
                total_gain = exit_proceeds - all_in_no_reno
                # Annualized return on initial outlay (acquisition only)
                if exit_proceeds > 0:
                    ann_return = (exit_proceeds / all_in_no_reno) ** (1 / years) - 1
                else:
                    ann_return = float("nan")
                rows.append({
                    "Price scenario": pname,
                    "Appreciation scenario": aname,
                    "Hold (yrs)": years,
                    "Exit price (€)": round(exit_price),
                    "Net of 4% exit fees (€)": round(exit_proceeds),
                    "All-in basis (€)": round(all_in_no_reno),
                    "Total gain (€)": round(total_gain),
                    "Annualized return": round(ann_return * 100, 2),
                })
    return pd.DataFrame(rows)


def break_even_appreciation() -> pd.DataFrame:
    """Annual appreciation needed to break even after acquisition + exit costs."""
    rows = []
    for pname, price in PRICE_SCENARIOS.items():
        all_in = price * (1 + NOTARY_PCT)
        for years in HOLD_YEARS:
            # exit_proceeds = price * (1+g)^years * (1-EXIT_AGENCY_PCT) = all_in
            target = all_in / (1 - EXIT_AGENCY_PCT) / price
            g = target ** (1 / years) - 1
            rows.append({
                "Price scenario": pname,
                "Hold (yrs)": years,
                "Break-even annual appreciation %": round(g * 100, 2),
            })
    return pd.DataFrame(rows)


def buy_vs_rent_table() -> pd.DataFrame:
    """Annual cost of owning vs. renting equivalent unit.

    Renting an equivalent 186 m² apartment in 75003 at mid-market furnished
    rate (~€30/m²/mo encadré) sets the alternative. Owner's annual cost is
    carry + 'opportunity cost of capital' on the all-in basis (assumed 4%
    risk-free benchmark). This isolates whether ownership is cost-equivalent
    before counting appreciation.
    """
    OPP_COST_RATE = 0.04
    rent_per_yr = RENT_PER_M2_MID * SURFACE_M2 * 12  # equivalent rent
    rows = []
    for pname, price in PRICE_SCENARIOS.items():
        all_in = price * (1 + NOTARY_PCT)
        maint = price * ANNUAL_MAINT_RESERVE_PCT
        ifi = price * IFI_ANNUAL_PCT
        carry = ANNUAL_CHARGES + ANNUAL_TAXE_FONCIERE + ANNUAL_INSURANCE + maint + ifi
        opp = all_in * OPP_COST_RATE
        owner_cost = carry + opp
        rows.append({
            "Price scenario": pname,
            "All-in basis (€)": round(all_in),
            "Annual carry (€)": round(carry),
            "Opp cost of capital @4% (€)": round(opp),
            "Owner annual cost (€)": round(owner_cost),
            "Equivalent rent (€)": round(rent_per_yr),
            "Own vs rent gap (€)": round(owner_cost - rent_per_yr),
            "Break-even appreciation needed %": round(
                max(0, owner_cost - rent_per_yr) / price * 100, 2),
        })
    return pd.DataFrame(rows)


# ============================================================
# Run
# ============================================================
def main():
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 20)

    acq = acquisition_cost_matrix()
    print("=== ACQUISITION COST MATRIX ===")
    print(acq.to_string(index=False))

    carry = carrying_cost_table()
    print("\n=== ANNUAL CARRYING COST ===")
    print(carry.to_string(index=False))

    yield_tbl = rental_yield_table()
    print("\n=== RENTAL YIELD ===")
    print(yield_tbl.to_string(index=False))

    irr = irr_sensitivity()
    print("\n=== IRR / EXIT SENSITIVITY (residence — no rental income) ===")
    print(irr.to_string(index=False))

    be = break_even_appreciation()
    print("\n=== BREAK-EVEN APPRECIATION TO RECOVER FRICTION ===")
    print(be.to_string(index=False))

    bvr = buy_vs_rent_table()
    print("\n=== BUY VS RENT EQUIVALENT (annual cost comparison) ===")
    print(bvr.to_string(index=False))

    acq.to_csv(DATA_DIR / "acquisition_cost.csv", index=False)
    carry.to_csv(DATA_DIR / "carrying_cost.csv", index=False)
    yield_tbl.to_csv(DATA_DIR / "rental_yield.csv", index=False)
    irr.to_csv(DATA_DIR / "irr_sensitivity.csv", index=False)
    be.to_csv(DATA_DIR / "break_even.csv", index=False)
    bvr.to_csv(DATA_DIR / "buy_vs_rent.csv", index=False)


if __name__ == "__main__":
    main()
