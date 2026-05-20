# Sensitivity & Yield Model — Rue Sainte-Apolline Subject

**Property:** 186 m² apartment, asking €2.0M
**Analysis date:** 2026-05-19
**Companion to:** [dvf_analysis.md](dvf_analysis.md)

---

## TL;DR

This is **not an investment property by any normal yardstick**. Net post-tax rental yield is **0.6–1.5%**, well below the 4% opportunity cost of the €2M capital. To break even against renting an equivalent unit, the apartment needs to appreciate at **~2.0–2.4%/year indefinitely** — higher than Paris prime has delivered in the last decade.

Under all scenarios examined, total annualized return over a 5-year hold ranges from **−2.7% (bear) to +0.7% (bull)**. Over a 10-year hold: **−1.6% to +1.8%**. These already include the ~7.5% notary friction and 4% exit fees.

The case for buying therefore rests on **use value** (you want to live there) and **non-financial benefits** (currency/jurisdiction diversification, estate planning, identity-as-Parisian-owner). Not yield.

If you proceed, the **negotiated-to-10th-band scenario (€1.77M) with move-in-ready condition** is the only configuration that is even directionally rational on financial terms. The full-ask + significant-works scenario (€2.45M all-in, €13,166/m²) is materially above any defensible market level.

---

## 1. Assumptions

All values editable in [yield_model.py](yield_model.py). Defaults below.

### Property
- Surface (Carrez): **186.08 m²**
- Asking: **€2,000,000** (€10,750/m²)

### Three purchase-price scenarios

| Scenario | Price | €/m² | Rationale |
|---|---:|---:|---|
| Negotiated to 10th-band | €1,767,760 | €9,500 | Subject location functions like Paris 10th (DVF median €9,284) |
| Negotiated to mid-band | €1,953,840 | €10,500 | Blended 10th/3rd, average-condition unit |
| **Full ask** | **€2,000,000** | **€10,750** | Listed price |

### Renovation budgets

| Scenario | Budget | €/m² reno cost |
|---|---:|---:|
| Move-in ready | €0 | — |
| Cosmetic refresh | €100,000 | €538 |
| Significant works | €300,000 | €1,613 |
| Full gut renovation | €600,000 | €3,225 |

The same-street DVF spread (€9,195 → €13,053 at 9 rue Sainte-Apolline) implies ~€700k of value lift between condition extremes, consistent with these figures.

### Costs
- **Notary fees**: 7.5% of price (Paris standard for resale)
- **Exit agency fees**: 4% on sale
- **Annual co-ownership charges**: €4,582 (from listing)
- **Taxe foncière**: €3,335 (from listing)
- **Insurance (MRH)**: €1,200/yr
- **Maintenance reserve**: 0.5% of price/yr (Paris co-ownership reality)
- **IFI (wealth tax)**: 0.5% of price/yr (kicks in above €1.3M; conservative blended rate; set to 0 if non-resident or fully offset)

### Rental
- Encadrement des loyers in force in Paris 75003. Achievable rents:
  - **Low**: €25/m²/mo unfurnished (€55,824/yr)
  - **Mid**: €30/m²/mo furnished (€66,989/yr)
  - **High**: €35/m²/mo premium furnished with complément (€78,154/yr)
- Vacancy: 8%
- Management: 7% of effective rent
- Rental income tax: 30% effective (top-bracket French resident, régime réel)

### Appreciation
- **Bear**: −0.5%/yr (Paris prime stagnant, continued consolidation)
- **Base**: +1.0%/yr (flat to mild recovery)
- **Bull**: +3.0%/yr (return to long-run historical trend)

Hold periods modeled: 5 and 10 years.

---

## 2. Acquisition Cost Matrix

All-in cost = price + 7.5% notary + renovation budget.

| Purchase | Reno | All-in (€) | €/m² all-in |
|---|---|---:|---:|
| **Negotiated to 10th-band** | Move-in ready | **€1,900,342** | **€10,212** |
| Negotiated to 10th-band | Cosmetic | €2,000,342 | €10,750 |
| Negotiated to 10th-band | Significant | €2,200,342 | €11,825 |
| Negotiated to 10th-band | Full gut | €2,500,342 | €13,437 |
| Negotiated to mid-band | Move-in ready | €2,100,378 | €11,288 |
| Negotiated to mid-band | Cosmetic | €2,200,378 | €11,825 |
| Negotiated to mid-band | Significant | €2,400,378 | €12,900 |
| Negotiated to mid-band | Full gut | €2,700,378 | €14,512 |
| **Full ask** | **Move-in ready** | **€2,150,000** | **€11,554** |
| Full ask | Cosmetic | €2,250,000 | €12,092 |
| Full ask | Significant | €2,450,000 | €13,166 |
| Full ask | Full gut | €2,750,000 | €14,779 |

**Read:** Even at full ask + move-in ready, the all-in €/m² (€11,554) is below the 4th-arr median (€12,474) but above the 10th, 11th, and 3rd-arr medians. Add significant works and you're priced like prime 4th-arr Marais without being in it.

---

## 3. Annual Carrying Cost

| Scenario | Charges | Taxe fonc. | Insurance | Maint. reserve | IFI | **Annual total** | Monthly |
|---|---:|---:|---:|---:|---:|---:|---:|
| Negotiated to 10th-band | €4,582 | €3,335 | €1,200 | €8,839 | €8,839 | **€26,795** | €2,233 |
| Negotiated to mid-band | €4,582 | €3,335 | €1,200 | €9,769 | €9,769 | **€28,655** | €2,388 |
| Full ask | €4,582 | €3,335 | €1,200 | €10,000 | €10,000 | **€29,117** | €2,426 |

**IFI dominates the variable portion.** If the buyer can offset IFI via mortgage debt on the property or non-residence status, annual carry drops by €9-10k/yr. Worth modeling specifically once buyer's full estate is known.

---

## 4. Rental Yield (if rented out)

Computed against price + 7.5% notary (no reno).

| Price | Rent | Gross yield | Net pre-tax | Net post-tax (30%) |
|---|---|---:|---:|---:|
| 10th-band | Low (€25/m²) | 2.94% | 1.10% | 0.77% |
| 10th-band | Mid (€30/m²) | 3.53% | 1.61% | 1.12% |
| 10th-band | High (€35/m²) | 4.11% | 2.11% | 1.48% |
| Full ask | Low (€25/m²) | 2.60% | 0.87% | 0.61% |
| Full ask | Mid (€30/m²) | 3.12% | 1.31% | 0.92% |
| Full ask | High (€35/m²) | 3.64% | 1.76% | 1.23% |

**Read:** Even the best case (10th-band purchase + €35/m² rent) is a **1.48% post-tax yield**. The risk-free 4% benchmark crushes this. As a buy-to-let pure-investment thesis, this property doesn't pass the first filter.

---

## 5. IRR / Exit Sensitivity (residence — no rental income)

Annualized total return after notary + exit fees:

| Purchase | Hold | Bear (-0.5%/yr) | Base (+1%/yr) | Bull (+3%/yr) |
|---|---:|---:|---:|---:|
| 10th-band | 5 yrs | **−2.73%** | −1.26% | +0.70% |
| 10th-band | 10 yrs | −1.62% | −0.14% | +1.84% |
| Mid-band | 5 yrs | −2.73% | −1.26% | +0.70% |
| Mid-band | 10 yrs | −1.62% | −0.14% | +1.84% |
| Full ask | 5 yrs | **−2.73%** | **−1.26%** | **+0.70%** |
| Full ask | 10 yrs | −1.62% | −0.14% | **+1.84%** |

**Key reading:** The annualized return is the same across price scenarios (a mathematical property — appreciation is a % of basis, so the % return is invariant). What differs is the **absolute** € outcome. At full ask, 10-yr bear case loses **€324k**; bull case gains **€430k**.

**Break-even appreciation** to recover acquisition + exit friction:
- 5-year hold: **2.29%/yr**
- 10-year hold: **1.14%/yr**

A 10-year hold has a meaningfully achievable break-even (the 1.1%/yr threshold is roughly Paris's long-run real-terms appreciation). A 5-year hold needs prime to actually return to growth.

---

## 6. Buy vs Rent Equivalent

What does it cost to *own* the apartment annually (carry + opportunity cost of the €2M capital at a 4% risk-free benchmark) vs. *rent* an equivalent unit?

| Scenario | Owner cost/yr | Equivalent rent/yr | **Annual gap** | Break-even appreciation needed |
|---|---:|---:|---:|---:|
| Negotiated to 10th-band | €102,808 | €66,989 | **+€35,819** | **2.03%/yr** |
| Negotiated to mid-band | €112,671 | €66,989 | +€45,682 | 2.34%/yr |
| Full ask | €115,117 | €66,989 | **+€48,128** | **2.41%/yr** |

**Read:** Owning costs **€36-48k/yr more** than renting the same apartment, before any appreciation. The apartment must appreciate at ~2.0-2.4%/yr indefinitely just to neutralize that gap.

For context, the Paris prime €/m² index has been roughly flat for the last 5 years. The 10-year and 20-year averages are positive but not consistently above 2%.

---

## 7. Verdict

**Financially, this is a high-friction residence purchase, not an investment.**

The most defensible read of the numbers:

1. **At full ask (€2.0M), the owner faces a structural €48k/yr negative carry vs. renting**, and needs ~2.4%/yr appreciation to neutralize it. Bear/base appreciation scenarios produce nominal losses over both 5- and 10-year holds.

2. **Negotiating down to the 10th-band level (~€1.77M) materially improves the math:** the negative carry drops to €36k/yr and break-even appreciation drops to 2.0%/yr — still above recent Paris prime trends but within historical norms.

3. **The renovation decision is binary.** Either buy move-in-ready or buy at a price that fully discounts renovation cost. The "buy cosmetic, do significant works yourself" middle path (€2.25-2.45M all-in) prices the property like prime Marais while it isn't in prime Marais.

4. **The thesis is not yield.** If you proceed, the justification must be: (a) you actively want to live there for 7-10+ years, (b) you value euro/Paris exposure for non-financial reasons, or (c) you are confident in a renovation arbitrage thesis that closes the €9,195 → €13,053 gap visible on the same street.

**Recommendation for negotiation:**
- **Anchor price discussion to the 10th-arr DVF median** (€9,284/m², ~€1.73M) given the location.
- **Target a transacted price ≤€1.85M** (€9,943/m²) for a move-in-ready unit.
- **Walk away above €1.95M** unless you've personally verified renovated condition and have a 10+ year hold horizon.
- **The €2.0M ask is realistically a 5-8% over-market opening position** in DVF terms, not the negotiation floor it appears to be.

---

## 8. What this model does NOT capture

1. **Mortgage financing.** All-cash assumed. Mortgage interest deductibility, leverage on appreciation, and mortgage netting of IFI base would all change the picture. Worth a follow-up model if financing is in scope.
2. **Tax residency / nationality effects.** The IFI line, rental tax rate, and capital gains tax differ substantially for residents vs. non-residents and for citizens of countries with tax treaties.
3. **Currency.** A non-EUR buyer is taking explicit EUR exposure. EUR has depreciated ~5% vs. USD in the last 24 months; if that continues, the implicit FX cost compounds with the negative carry.
4. **Use value.** The whole point of a residence is the housing services it provides. The model treats those as worth exactly the equivalent rent (€67k/yr), which is a strong assumption — for a buyer who specifically wants *this* apartment and would not rent an equivalent unit, the use value exceeds €67k and the math improves accordingly.
5. **Optionality.** A residence is also an option on Paris life (children's schooling, retirement, business presence). Hard to price; not zero.
6. **Estate planning.** French real estate inside an estate has specific inheritance treatment that may be favorable depending on heirs and timing.

---

## Files produced

- `yield_model.py` — reproducible model (edit assumptions at top, rerun)
- `acquisition_cost.csv` — §2
- `carrying_cost.csv` — §3
- `rental_yield.csv` — §4
- `irr_sensitivity.csv` — §5
- `break_even.csv` — §5
- `buy_vs_rent.csv` — §6
