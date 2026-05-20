# Paris Apartment Hunt — Analysis & Dashboard

A reproducible pipeline for evaluating Paris apartment listings against actual recorded transactions (DVF), with a self-contained HTML dashboard for browsing.

## What this is

- **DVF-based pricing benchmark.** All asking prices in `listings_input.json` are scored against the median + IQR of *recorded* apartment sales in the same arrondissement and surface band, using the French government's open `geo-DVF` dataset.
- **Per-listing "expert analysis"** — strengths, concerns, photo signals where available, and a verdict (`underpriced` / `below-band` / `in-band` / `above-band` / `overpriced` / `needs-data`).
- **Static dashboard** — `dashboard/dashboard.html` is fully self-contained. No server, no Python needed to view. Just open it in a browser.
- **Deep-dive reports** — `dvf_analysis.md` and `yield_model.md` walk through the methodology and the financial model in detail.

## Quick start

```bash
# 1. Create a venv and install deps (~30 seconds, ~80 MB)
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. Regenerate the dashboard
.venv/bin/python build_dashboard.py

# 3. Open dashboard/dashboard.html in any browser
open dashboard/dashboard.html        # macOS
xdg-open dashboard/dashboard.html    # Linux
start dashboard/dashboard.html       # Windows
```

The build script reads `listings_input.json` + the `dvf_*.csv` files in this folder, computes verdicts, and writes `dashboard/dashboard.html` (self-contained) and `dashboard/listings.json` (for tooling).

## How to add a listing

Edit `listings_input.json` — append a new object with the fields below. Then rerun `python build_dashboard.py` and refresh the dashboard.

```json
{
  "id": "unique-string",
  "source": "agency or portal",
  "url": "https://...",
  "title": "Apartment, rue X (neighborhood)",
  "arr": "75107",          // five-digit commune code, prefix 751
  "arr_name": "Paris 7th",
  "neighborhood": "Saint-Thomas-d'Aquin",
  "street": "rue de Verneuil",
  "price_eur": 2100000,
  "surface_m2": 125,
  "bedrooms": 3,
  "floor": 2,
  "elevator": true,
  "exposure": "South",
  "year_built": 1880,
  "condition": "perfect condition",
  "condition_signals": ["herringbone parquet", "fresh paint"],
  "features": ["19th-c. building", "Carré des Antiquaires"],
  "notes": "Free-form text appended to the analysis verbatim.",
  "image": "img/<id>.jpg"
}
```

Required: `id`, `price_eur`, `surface_m2`, `arr`, `arr_name`. Everything else is optional but improves the analysis.

### Bulk add via `merge_listings.py`

The fastest way to add many listings at once is to scrape them with a Claude conversation that has the Chrome MCP connected (see the **Scrape prompt** section below), save the returned JSON to `new_listings.json`, and run:

```bash
.venv/bin/python merge_listings.py new_listings.json --rebuild --push
```

What it does:
- Validates each entry (drops bad arr codes, missing fields, absurd prices)
- Dedupes against existing IDs in `listings_input.json`
- Auto-downloads DVF for any arrondissement not yet covered
- Patches `DVF_ARRS` in `build_dashboard.py`
- `--rebuild` runs `build_dashboard.py`; `--push` commits and pushes to git
- `--dry-run` shows what would change without writing anything

Paris commune codes are `751XX` where XX is the arrondissement (`75103` for the 3rd, `75116` for the 16th — **NOT** `750XX`).

### Scrape prompt (for a fresh Claude conversation with Chrome MCP)

Open the listing site in your browser, apply filters, then paste this in a new Claude conversation:

> You're helping me extract listings for the paris-apartment-hunt dashboard. I'm at a Paris real-estate listing site with filters applied. Use the `mcp__Claude_in_Chrome__*` tools to scrape every listing visible on this page that matches: Paris proper (drop "À Xkm de Paris" suburbs), surface ≥ 80 m², price ≤ €2.5M, apartment or duplex.
>
> Use `javascript_tool` to extract structured data in one call — for each article card, parse the URL, the largest 6-7 digit number as the total price (skips €/m² and €/month), the m² value, the arrondissement number, bedroom/piece counts, and the agency. Return a JSON array I can paste into `new_listings.json`. Required keys per entry: `id` (prefix by source, e.g. `LF-` `SL-` `BI-`), `source`, `url`, `title`, `arr` (e.g. `"75107"`), `arr_name` (e.g. `"Paris 7th"`), `price_eur`, `surface_m2`, `bedrooms`, `pieces`, `data_quality: "search-results-extract"`. Don't fabricate URLs or surfaces — skip anything you can't confirm.

Then locally:

```bash
# Paste Claude's JSON array into new_listings.json
.venv/bin/python merge_listings.py new_listings.json --rebuild --push
```

## File map

```
.
├── README.md                   You are here
├── requirements.txt            Python deps (pandas, matplotlib)
├── listings_input.json         Source of truth — edit this to add/change listings
├── build_dashboard.py          Main pipeline (run this)
├── dashboard_template.html     HTML template (data is injected at build time)
├── dvf_751XX_YYYY.csv          Raw DVF transaction data (per arr, per year)
├── dvf_analysis.md             Deep dive on one listing — full methodology
├── yield_model.md              Sensitivity & yield model — applicable to any listing
├── analyze_dvf.py              Standalone DVF analysis for Paris 3rd
├── cross_arr_analysis.py       Cross-arrondissement comparison
├── street_analysis.py          Street-level comp finder
├── yield_model.py              Generates the sensitivity/yield tables
└── dashboard/
    ├── dashboard.html          The deliverable — self-contained, just open it
    ├── listings.json           Same data as embedded in HTML, for external tooling
    ├── img/<id>.jpg            Listing photos
    ├── charts/*.png            DVF distribution charts
    └── README.md               Dashboard-specific notes
```

## Methodology in one paragraph

DVF (Demandes de Valeurs Foncières) is the French open registry of all recorded property transactions, published by DGFiP. For each listing, the pipeline groups DVF rows by `id_mutation` (one sale = potentially many rows), drops mixed-lot sales (apartment + parking/cellar) to avoid €/m² inflation, trims outliers, and computes per-arrondissement medians + IQR by surface band (`<80 m²` vs `80-250 m²`). A listing's asking €/m² is positioned against the median + IQR of its band. What DVF does **not** capture: condition, floor, exposure, view. So the verdict answers "is the seller inside the recorded-transaction range for this size + arrondissement?" — not "is the unit worth this." Condition is the dominant variable; only a visit settles it.

## What sub-agents do during intake

When a new listing is forwarded, three things can run in parallel as sub-agents to keep the main context lean:

1. **URL fetcher** — pull the listing page, extract structured fields (most major French portals block bots; agency sites usually work)
2. **Image analyzer** — download the lead photo, view it, return condition signals (modern kitchen, original moldings, dated wallpaper, etc.)
3. **Chart builder** — if a new arrondissement is added, regenerate the distribution PNGs

Each sub-agent returns ~200 tokens of structured data to the parent. The full HTML pages and image binaries stay in the sub-agents' contexts. See `dashboard/README.md` §"Agent-augmented enrichment" for details.

## Data sources

- **DVF** — https://files.data.gouv.fr/geo-dvf/ (Etalab-curated, public domain)
- **Listings** — forwarded broker emails (e.g. Nouvelle Vague), Le Figaro Properties, SeLoger.com, agency websites (Daniel Féau, Barnes Paris, Sotheby's)

## License & sharing

The DVF data is French public-sector open data (Licence Ouverte). Listing data is whatever each agency published publicly. The code in this folder is yours to share, modify, and extend.

To hand off to another developer:

```bash
# zip the folder (excluding venv)
cd ~/Documents && zip -r paris-apartment.zip paris-apartment -x 'paris-apartment/.venv/*' 'paris-apartment/__pycache__/*'
```

Recipient unzips, runs the Quick Start above, and is fully operational in under a minute.
