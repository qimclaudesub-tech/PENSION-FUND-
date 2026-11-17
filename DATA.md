# DATA.md — every series, its source and how we checked it

All series are monthly and in **KZT**. Raw files in `data/raw/` are kept exactly as downloaded, with one disclosed exception (CPI 2021, see below).

## 1. Pension asset unit values (UV) — ENPF and private managers

| Item | Value |
|---|---|
| Source | ENPF JSC, public API of invest.enpf.kz (no key): `https://invest.enpf.kz/api/invest/getUEByName?name=<name>` |
| Codes (API `name`) | ENPF / National Bank: `Национальный` · BCC Invest: `BCC` · Alatau City Invest: `Alatau` · Centras Securities: `Сентрас` · Halyk Global Markets: `Halyk Global Markets` · Halyk Finance: `Halyk Finance` · Tansar Capital: `Tansar` |
| What it is | Daily value of one pension "unit" (like a fund share price), KZT |
| Adjusted? | Net of the manager's fees; no dividends to add — the unit value already includes all income |
| Frequency used | Monthly: value on the 1st day of month M+1 = end of month M (ENPF reporting convention) |
| Raw files | `enpf_ue_<CODE>_<pull date>.json` + `.meta.json` (URL, pull time, rows) |
| Pull date | [2026-10-18] |
| First real value | ENPF 1998 · Alatau, BCC, HGM 12.03.2021 · Centras 30.03.2021 · Halyk Finance 15.12.2022 · Tansar 07.04.2026 (excluded: too short) |
| Last value | 01.09.2026 (≈1.5-month publication lag) |

**Data problems found**
- Before the first transfer of money the API returns a placeholder value of **100**; on the start date the UV is set equal to ENPF's UV (≈899 KZT in March 2021). Without cleaning this looks like a +800% one-day return. `data.drop_placeholder()` removes everything before that jump; the number of rows dropped is shown in the honesty panel.
- Moves of ±4–6% in February–April 2022 are real (tenge devaluation), not errors.
- Survivorship: only managers active today are available; managers that left the market (e.g. Jusan Invest) are not in the API.

## 2. Consumer price index (CPI)

| Item | Value |
|---|---|
| Source | Bureau of National Statistics (stat.gov.kz), dynamic table "CPI and its components", column "to previous month → goods and services" |
| File | `stat_cpi_2026-10-17.xlsx` |
| Unit | Index, previous month = 100 (100.7 = +0.7% in the month) |
| Period | January 2021 – September 2026 |
| Adjusted? | Not applicable (official index, not seasonally adjusted) |

**Disclosed manual edit.** The table downloaded from stat.gov.kz starts in 2022. The 2021 rows (January–December) were added by hand from two official BNS press releases "Inflation in the Republic of Kazakhstan" for December 2021 and January 2022 (identical values in both):
[Dec-2021 release](https://www.gov.kz/uploads/2021/12/31/3a93503b95afe95ddc89f2710afb08d5_original.115994.docx), [Jan-2022 release](https://www.gov.kz/uploads/2022/2/1/31f9b7d3fdf014da5ff7e213ea0532aa_original.107396.docx).
Only the headline column is filled for January–November 2021 (category breakdown is available only for December 2021). The 2022–2026 values are unchanged.
Values 2021: 100.6, 100.7, 100.6, 100.9, 100.7, 101.1, 100.7, 100.5, 100.4, 100.7, 100.7, 100.6. They compound to 8.5% vs the official 8.4% for 2021 — rounding of monthly values to 0.1.

## 3. Tenge deposit rate (benchmark and risk-free rate)

| Item | Value |
|---|---|
| Source | National Bank of Kazakhstan (nationalbank.kz), "Interest rates on deposits attracted by banks (by maturity and currency)" |
| Series | Deposits of individuals → term deposits, total → KZT |
| File | `nbk_deposit_rates_2026-10-17.xlsx` |
| Unit | Weighted average rate on new deposits, % per year |
| Period | January 2021 – August 2026 |
| How used | Monthly rate = (1 + y)^(1/12) − 1 |

Limitation: it is the average rate on deposits opened in that month, not the return of one specific deposit held for the whole period.

## 4. Analysis window

Common window: **April 2021 – August 2026, 65 monthly returns** (base = end of March 2021, the first month-end after the private managers started). Halyk Finance: January 2023 – August 2026, 44 months; it is compared with ENPF on the same 44 months. The user can shorten the window in the app; months dropped in joins are listed in the honesty panel.

## 5. Official cross-checks (at least two dates per series)

Recomputed in `annex/QIM_hand_calculations.xlsx`, sheet 5_Real_scorecard.

| Series | Check | Our value | Official | Result |
|---|---|---|---|---|
| ENPF (NBK) UV | 12-month return 01.12.2024 → 01.12.2025 | 9.69% | 9.69% (ENPF report) | MATCH |
| BCC Invest UV | 12-month return 01.12.2024 → 01.12.2025 | 10.13% | 10.13% | MATCH |
| BCC Invest UV | 12-month return 01.09.2025 → 01.09.2026 | 10.95% | 10.95% (invest.enpf.kz) | MATCH |
| Alatau City Invest UV | 12-month return 01.12.2024 → 01.12.2025 | 11.11% | 11.11% | MATCH |
| Centras Securities UV | 12-month return 01.12.2024 → 01.12.2025 | 15.72% | 15.72% | MATCH |
| Halyk Global Markets UV | 12-month return 01.12.2024 → 01.12.2025 | 10.50% | 10.50% | MATCH |
| Halyk Finance UV | 12-month return 01.12.2024 → 01.12.2025 | 9.45% | 9.45% | MATCH |
| CPI | Jan–Dec 2022 compounded | 20.35% | 20.3% (BNS) | MATCH (rounding) |
| CPI | Sep 2025 – Aug 2026 compounded | 9.92% | 9.8% (BNS year-on-year) | MATCH (rounding) |
| Deposit rate | November 2024 | 13.2% | 13.2% (NBK data, [nur.kz](https://www.nur.kz/nurfin/banks/2206559-skolko-deneg-kazahstancy-nakopili-na-depozitah-v-2024-godu/)) | MATCH |
| Deposit rate | June 2025 | 14.2% | 14.2% (NBK data via First Credit Bureau, [kapital.kz](https://kapital.kz/finance/139196/kakie-bankovskie-depozity-byli-vygodnee-vsego-dlya-fizlic-v-iyune.html)) | MATCH |
