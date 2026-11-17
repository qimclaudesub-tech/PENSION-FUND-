# Pension Fund Evaluator

A small Streamlit app for a Kazakhstani saver who is deciding whether to move pension savings from ENPF (managed by the National Bank) to a private investment portfolio manager.
For any manager and period it shows the real (after-inflation) return, the risk, and one headline number — **M² vs ENPF, % per year** — compared with ENPF and a tenge deposit.

## Install and run (one command)

Requires Python 3.10+ (tested with 3.12). From the project folder:

**macOS / Linux**
```
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && streamlit run app.py
```

**Windows (PowerShell)**
```
python -m venv .venv; .venv\Scripts\Activate.ps1; pip install -r requirements.txt; streamlit run app.py
```

The app opens in the browser at http://localhost:8501. The first start downloads fresh data from the ENPF public API (10–30 s).

## Offline mode

All raw data are saved in `data/raw/`. Without internet (or with the sidebar switch "Download fresh data from ENPF" off) the app uses the saved files and shows an **OFFLINE MODE** banner.

## Run the tests

```
pytest -v
```
15 known-answer tests in `tests/test_core.py`; 3 of them use answers calculated by hand (photos in `annex/`), 1 checks real data against an official ENPF figure.

## Project structure

| File / folder | Layer | What it does |
|---|---|---|
| `data.py` | Data | Downloads ENPF unit values (public API), reads CPI and deposit files, saves raw files with source and pull date, offline fallback |
| `data/raw/` | Data | Raw files exactly as downloaded (see DATA.md) |
| `core.py` | Core | Every formula as a pure function (no internet, no UI) |
| `tests/` | Tests | Known-answer tests (`pytest`) |
| `app.py` | Screen | Streamlit screen; calls `core.py` only, no calculations |
| `annex/` | Checks | Excel recomputation of every number + hand calculations |

## API keys

No API keys are needed: the ENPF API, stat.gov.kz and nationalbank.kz data are public. `.env` is listed in `.gitignore`; if a key is ever added, copy `.env.example` to `.env` and put it there — never commit it.

## Reused vs new (brief section 3)

No code from the Week 4 Portfolio Risk X-Ray was copied; the X-Ray concepts we use again (volatility, drawdown, correlation, diversification benefit) were written anew in `core.py`.
New relative to the X-Ray: real returns after CPI, deposit risk-free rate, Sharpe and its standard error, Sortino, Calmar, **M²** (Week 5), beta/alpha/R² vs ENPF with confidence interval, tracking error and information ratio (Weeks 5–6), buy-and-hold vs monthly rebalancing (Week 8), and a different user question.

Historical data, not a forecast, not investment advice.
