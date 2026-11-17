# AI_USE

| Date | Tool | Location in code | Prompt / request | What we changed | How we verified |
|---|---|---|---|---|---|
| 2026-10-17 | Claude | data.py: download_unit_values, load_unit_values, drop_placeholder | Find a data source for pension unit values; write a downloader for the ENPF API with raw-file saving and offline fallback | — | Ran `python data.py`; cross-check: BCC Invest 12-month return from API (01.09.2025→01.09.2026) = 10.95%, matches invest.enpf.kz; offline test with Wi-Fi off |
| 2026-10-17 | Claude | data.py: load_cpi, load_deposit_rates, month_end_levels, build_monthly_dataset | Read the stat.gov.kz CPI xlsx and the NBK deposit rate xlsx without editing them; align all series monthly | — | Ran `python data.py`; CPI compounded Oct-2025..Sep-2026 = 9.38% vs official 9.3% (rounding of monthly values); 2022 = 20.35% vs official 20.3% |

| 2026-10-18 | Claude | annex/QIM_hand_calculations.xlsx; data/raw/stat_cpi_2026-10-17.xlsx | Build Excel check of all formulas on synthetic and real data; add 2021 CPI from BNS press releases; extend window to Apr-2021..Aug-2026 | Kept the original stat.gov.kz values for 2022-2026; 2021 rows added by hand and disclosed in DATA.md | 38 known-answer tests PASS; independent Python recomputation, 0 mismatches; 2021 CPI identical in 2 official releases; all 11 official cross-checks MATCH (UV, CPI, deposit) |

| 2026-10-18 | Claude | core.py (all functions) | Write all course formulas as pure functions (returns, CAGR, volatility, MDD, Sharpe, M², beta, TE/IR, portfolio mix) | — | Checked against annex/QIM_hand_calculations.xlsx: 26 synthetic values and all scorecard metrics for 6 managers match (max diff 7e-13) |

| 2026-10-18 | Claude | tests/test_core.py | Write ≥8 known-answer tests: 3 hand-calculated (CAGR, MDD+volatility, Sharpe), 1 real-data cross-check, synthetic data labelled | — | Expected values from annex Excel; team ran pytest: 15 passed; deliberately broke Sharpe formula → 3 tests failed |

| 2026-10-18 | Claude | app.py | Write Streamlit screen: inputs, headline M², growth chart, comparison table, partial transfer, honesty panel, offline banner; no calculations in the screen code | — | We ran streamlit: BCC M² = +1.00% matches annex Excel; changed manager/period → headline and chart update; Wi-Fi off → OFFLINE MODE banner; searched app.py for arithmetic: none |