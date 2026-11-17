# DECISIONS.md — decision record (syllabus 9.2)

Each decision: what we chose, the alternatives, the evidence, and AI advice accepted or rejected.

| # | Decision | Alternatives considered | Evidence / reason | AI advice |
|---|---|---|---|---|
| 1 | Track 8 (own idea): evaluate ENPF private managers for a Kazakhstani saver | Tracks 1–7 | Since 2021 savers may move up to 100% of savings to a private manager; ENPF shows only nominal returns, no inflation or risk | AI helped check that monthly data exist (ENPF API) — accepted |
| 2 | Headline = **M² vs ENPF, % per year** | Sharpe ratio; real CAGR | Sharpe is hard to read for a saver; M² turns it into "% per year at ENPF's level of risk"; M² of ENPF vs itself = 0 is a built-in check | Suggested by AI, accepted after checking the course slides (Week 5) |
| 3 | Benchmark and risk-free rate = weighted average rate on new KZT term deposits of individuals (NBK) | NBK base rate; government bond yields | A saver can actually get a deposit rate; the base rate is not available to individuals | AI suggested the deposit rate instead of the base rate — accepted |
| 4 | Monthly frequency; UV on the 1st day of month M+1 = end of month M | Daily returns; last calendar day of the month | CPI and deposit rates are monthly; ENPF reports returns "as of the 1st" | Accepted |
| 5 | Window **Apr-2021 – Aug-2026 (65 months)** | Jan-2022 – Aug-2026 (56 months, CPI file starts in 2022) | Private managers started 12–30.03.2021; longer window lowers the Sharpe standard error (0.46 → 0.43) and includes the 2022 shock | Accepted |
| 6 | CPI 2021 added by hand into the stat.gov.kz file, disclosed in DATA.md | Keep the official file untouched and add 2021 as a separate raw CSV merged in `data.py` | Simpler; values identical in two official BNS releases; 8.5% vs official 8.4% (rounding) | **AI advised a separate CSV (brief: raw files never edited by hand) — rejected by the team**; we disclose the edit instead |
| 7 | Exclude Tansar Capital | Show it with a warning | Real data only from April 2026 (≈5 months) — too short for risk measures | Accepted |
| 8 | Halyk Finance on its own window (Jan-2023 –) and compared with ENPF on the same months | Drop it; shorten everybody to 2023 | Keeps the longer window for the other managers; fair comparison | Accepted |
| 9 | Remove the API placeholder 100 before the first transfer (`drop_placeholder`) | Start each series by hand at a fixed date | A rule works for every manager and future data; rows dropped are reported | Accepted |
| 10 | Exact real return (1+r)/(1+π) − 1; monthly rf = (1+y)^(1/12) − 1; CAGR geometric; SD with n−1; volatility × √12 | r − π; y/12; mean × 12; STDEV.P | Course conventions (Weeks 4–5); the wrong versions are shown side by side in the Excel annex | Accepted |
| 11 | Sharpe denominator = SD of excess returns; SE of Sharpe (Lo) shown next to it | SD of raw returns; no uncertainty | Course convention (Week 5); with 65 months SE ≈ 0.43, so most differences are noise — said on screen | Accepted |
| 12 | Beta = regression of manager excess returns on ENPF excess returns, with 95% CI | Beta vs KASE index | The user's alternative is ENPF, not the stock market; ENPF is the benchmark asked about | Accepted |
| 13 | Partial transfer shown as buy-and-hold (one-off) and monthly rebalancing | Rebalancing only | A saver transfers once and does not rebalance monthly; rebalancing shown for comparison (Week 8) | Accepted |
| 14 | No calculations in `app.py`; every number from `core.py` | Quick formatting arithmetic in the screen | Brief caps Methods at half otherwise; the share slider returns a fraction directly | Accepted |
