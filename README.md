# JW Opportunity Desk

Tender Desk (tender extraction) and Opportunity Radar (catalogue, signals, global trends) in one tool for JazzWorld Institutional Sales and the four SBUs.

Deployment steps are in `DEPLOY.md`.

## How it fits together

| Folder | What it holds |
| --- | --- |
| `scraper/` | `scan.py` reads EPADS, PPRA EPMS, the World Bank API, PITB and Google News feeds. `ai_reader.py` is the second reader for tenders and headlines. `digest.py` posts new tenders to Teams. |
| `build/` | `normalize.py` cleans the raw data. `rules.py` and `accounts.py` hold every matching rule and the buyer registry. `make_data.js` runs the engine and links news to themes. `seed/` holds the research file: catalogue, signals, forecasts, trends, themes. |
| `app/` | The site. `engine.js` makes every relevance and score decision. `opportunity-desk.html` is the interface. `data/` is rebuilt on each scan. |
| `functions/` | Cloudflare Pages functions: passphrase gate, `/api/ai` (server-side key), `/api/store` (team pipeline). |
| `archive/` | What has been seen before. It drives the "new" flag and grows the tender history with every scan. |
| `.github/workflows/scan.yml` | The schedule. |

## The 2026 history

`app/data/market.js` is built once from the Teknosys export: `python build/load_history.py tenders_full.csv` then `node build/make_market.js`. Rebuild it when a newer export arrives.

## Rebuild by hand

    python scraper/scan.py           # read every source (or --only epads,wb)
    python build/normalize.py
    python build/make_catalogue.py
    node   build/make_data.js
    python build/make_standalone.py  # dist/JW_Opportunity_Desk.html, one file that opens anywhere
    python scraper/tests/test_parsers.py

## Change a rule

Edit `build/rules.py`. A plain "phrase" qualifies a tender, "?word" only supports, and "not" lists contexts where a phrase is ignored. Add theme patterns in `build/seed/themes.json`.

## Where AI is used

An AI reader reads every digital tender alongside the rules; agreement and disagreement are shown on each tender. AI also reads Pakistani headlines into structured signals, drafts concept notes from evidence packs the rules assemble, writes the weekly brief and answers questions through read-only lookups. Every AI output is marked in the interface.
