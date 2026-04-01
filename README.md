# CongressTrades

A serious, polished web platform that tracks U.S. congressional stock trades, detects policy-area overlaps, flags potentially relevant trades, reconstructs estimated portfolio performance, and surfaces the newest disclosures in a usable investigative dashboard.

## Features

- **Trade tracking** — full STOCK Act disclosure history from House + Senate
- **Policy-overlap detection** — scores every trade against member committee assignments and policy areas
- **Red-flag scoring** — transparent 0–100 conflict-relevance score with factor breakdown
- **Performance estimation** — reconstructed portfolio returns vs S&P 500 benchmark
- **Member profiles** — committees, policy areas, trade history, performance chart
- **Company pages** — who trades each stock, when, and how much
- **Advanced filters** — by member, ticker, party, chamber, state, sector, date, flagged-only

## Data Sources

| Source | Key Required | What it provides |
|--------|-------------|-----------------|
| [House Disclosures](https://disclosures.house.gov/) | ❌ None | Official House PTR ZIP archives |
| [Senate EFTS API](https://efts.senate.gov/LATEST/search-index) | ❌ None | Senate trade disclosures JSON API |
| [unitedstates/congress](https://unitedstates.github.io/congress-legislators/) | ❌ None | Member + committee metadata |
| [Yahoo Finance (yfinance)](https://finance.yahoo.com) | ❌ None | Price history + sector/industry |
| [SEC EDGAR tickers](https://www.sec.gov/files/company_tickers.json) | ❌ None | Ticker → company name map |
| congress.gov API | ✅ Free key (optional) | Richer committee data |

**This project runs with zero API keys by default.**

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/your-username/congress-trades
cd congress-trades
npm install
```

### 2. Generate seed data (no network required)

```bash
cd pipeline
pip install -r requirements.txt
python main.py --seed
```

This generates `data/artifacts/*.json` with realistic sample data so the app works immediately.

### 3. Run locally

```bash
npm run dev
# Open http://localhost:3000
```

### 4. Run the full data pipeline (fetches real data)

```bash
cd pipeline
python main.py         # Full fetch + process + export (~15-30 min on first run)
# Or step by step:
python main.py --step fetch    # Download raw data
python main.py --step process  # Normalize + resolve
python main.py --step export   # Score + estimate + write artifacts
```

## Architecture

```
congress-trades/
├── src/app/           # Next.js 15 App Router pages
├── src/components/    # React components (trades, charts, filters, UI)
├── src/lib/           # TypeScript types + data loaders + utilities
├── data/
│   ├── artifacts/     # Pre-computed JSON — committed to repo, read by Next.js
│   ├── raw/           # Gitignored raw fetched data
│   └── processed/     # Gitignored intermediate processed data
├── pipeline/          # Python data pipeline
│   ├── providers/     # House, Senate, congress.gov, Yahoo Finance fetchers
│   ├── normalizers/   # Member + ticker resolution (fuzzy matching)
│   ├── engines/       # Overlap scorer + performance estimator
│   └── exporters/     # JSON artifact exporter
└── .github/workflows/ # Scheduled daily pipeline + Vercel deploy
```

**Architecture choice: Hybrid static + API routes**
- Pipeline runs daily (GitHub Actions), writes JSON artifacts
- Next.js reads artifacts at build time via `fs` (server components)
- ISR revalidates stale pages every 6 hours
- No backend database required — cost ≈ $0/month on Vercel free tier

## Deployment

### Vercel (recommended, free)

```bash
npm i -g vercel
vercel
```

Set these optional secrets in your Vercel project:
- `CONGRESS_API_KEY` — free key from api.congress.gov (optional)

### GitHub Actions — scheduled pipeline

1. Fork this repo
2. The workflow at `.github/workflows/update-data.yml` runs daily at 06:00 UTC
3. It fetches new disclosures, regenerates artifacts, commits + pushes
4. If you set `VERCEL_DEPLOY_HOOK` in repo secrets, Vercel redeploys automatically

### Environment variables

Copy `.env.example` to `.env.local`. All variables are optional — the app works without any keys.

## Methodology

See [/about](/about) in the running app for full methodology documentation including:
- Data source details and limitations
- Policy overlap scoring factors and weights
- Performance estimation methodology and caveats

**Important**: This is a public-information transparency tool. It does not prove wrongdoing. All scores are informational signals only.

## Legal

All data is sourced from public U.S. government filings under the STOCK Act. No proprietary data sources are used.

---

Built with Next.js 15, TypeScript, Tailwind CSS, Recharts, TanStack Table, and Python.
