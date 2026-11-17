"""
data.py — DATA LAYER.

What it does:
  1. Downloads the pension asset unit value (UV) for ENPF (managed by the
     National Bank of Kazakhstan) and for private investment portfolio
     managers (IPMs) from the public ENPF API, saves every API response to
     data/raw/ unchanged (+ a .meta.json file with source and pull date),
     and falls back to the latest saved file when offline.
  2. Reads two files downloaded once by hand from official websites and kept
     unchanged in data/raw/:
       - stat_cpi_<date>.xlsx           Bureau of National Statistics (stat.gov.kz),
                                        CPI, % of previous month, all goods and services
       - nbk_deposit_rates_<date>.xlsx  National Bank of Kazakhstan (nationalbank.kz),
                                        weighted average rate on new term deposits
                                        of individuals in KZT, % per year
  3. Puts everything on one monthly calendar (build_monthly_dataset).

No financial formulas here: returns, real returns, risk and Sharpe are
computed in core.py.
"""

import json
from datetime import date, datetime
from pathlib import Path

import openpyxl
import pandas as pd
import requests

# Folder for raw data (data/raw next to this file)
RAW_DIR = Path(__file__).parent / "data" / "raw"

# Public API of the ENPF platform invest.enpf.kz (no key required)
API_URL = "https://invest.enpf.kz/api/invest/getUEByName"

# Our short codes -> name the API expects (must stay exactly as is, some are
# in Cyrillic) and the English label shown on screen
MANAGERS = {
    "NBRK":    {"api_name": "Национальный",         "label": "ENPF (National Bank of Kazakhstan)"},
    "ALATAU":  {"api_name": "Alatau",               "label": "Alatau City Invest"},
    "BCC":     {"api_name": "BCC",                  "label": "BCC Invest"},
    "CENTRAS": {"api_name": "Сентрас",              "label": "Centras Securities"},
    "HGM":     {"api_name": "Halyk Global Markets", "label": "Halyk Global Markets"},
    "HF":      {"api_name": "Halyk Finance",        "label": "Halyk Finance"},
    "TANSAR":  {"api_name": "Tansar",               "label": "Tansar Capital"},
}

# Russian month names used in the stat.gov.kz CPI file
RU_MONTHS = {
    "январь": 1, "февраль": 2, "март": 3, "апрель": 4, "май": 5, "июнь": 6,
    "июль": 7, "август": 8, "сентябрь": 9, "октябрь": 10, "ноябрь": 11, "декабрь": 12,
}


# =====================================================================
# 1. ENPF unit values (API)
# =====================================================================

def download_unit_values(key: str) -> Path:
    """Download the unit value series of one manager and save the raw response to data/raw/."""
    api_name = MANAGERS[key]["api_name"]
    resp = requests.get(API_URL, params={"name": api_name}, timeout=20)
    resp.raise_for_status()  # raise an error if the server did not answer 200 OK

    data = resp.json()
    if not isinstance(data, list) or len(data) == 0:
        raise ValueError(f"API returned an empty response for {key}")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    pull_date = date.today().isoformat()                    # e.g. 2026-10-17
    path = RAW_DIR / f"enpf_ue_{key}_{pull_date}.json"
    # save the response exactly as received
    path.write_text(resp.text, encoding="utf-8")

    meta = {
        "source": "ENPF JSC, invest.enpf.kz platform, public API",
        "url": resp.url,
        "manager": MANAGERS[key]["label"],
        "series": "Pension asset unit value, KZT, daily",
        "pulled_at": datetime.now().isoformat(timespec="seconds"),
        "rows": len(data),
    }
    path.with_suffix(".meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return path


def latest_saved_file(pattern: str):
    """Return the most recent file in data/raw matching the pattern (or None)."""
    files = [p for p in RAW_DIR.glob(
        pattern) if not p.name.endswith(".meta.json")]
    # ISO date in the name -> sort by name = sort by date
    return sorted(files)[-1] if files else None


def parse_raw_file(path: Path) -> pd.Series:
    """Read a raw JSON file and turn it into a series: date -> unit value."""
    records = json.loads(path.read_text(encoding="utf-8"))
    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["dataDate"])
    df["unit_value"] = df["dataValue"].astype(float)
    df = df.drop_duplicates(subset="date").sort_values("date")
    return df.set_index("date")["unit_value"]


def drop_placeholder(s: pd.Series):
    """
    Remove the technical placeholder at the start of a series.

    Data issue: before the first real transfer of money, the API returns 100;
    on the start date the unit value is set equal to the ENPF unit value
    (~899 KZT in March 2021). Without cleaning, this would look like a
    +800% one-day return.

    Rule: if the first value stays flat and then the series jumps by more
    than 2x, everything before that jump is a placeholder and is dropped.
    Returns (cleaned series, number of rows dropped).
    """
    first = s.iloc[0]
    changed = s[s != first]
    if changed.empty:
        return s, 0
    if changed.iloc[0] > 2 * first:
        start = changed.index[0]
        cleaned = s.loc[start:]
        return cleaned, len(s) - len(cleaned)
    return s, 0


def load_unit_values(key: str, refresh: bool = True):
    """
    Return (daily unit value series, info dict).
    refresh=True  -> try to download fresh data; if that fails, use the saved file.
    refresh=False -> use the saved file directly.
    """
    path, used_saved, error = None, False, None

    if refresh:
        try:
            path = download_unit_values(key)
        except Exception as e:          # no internet, site unavailable, etc.
            error = str(e)

    if path is None:
        path = latest_saved_file(f"enpf_ue_{key}_*.json")
        used_saved = True
        if path is None:
            raise FileNotFoundError(
                f"No internet connection and no saved data for {key}. "
                "Run data.py once with an internet connection."
            )

    series, dropped = drop_placeholder(parse_raw_file(path))
    series.name = key

    info = {
        "key": key,
        "label": MANAGERS[key]["label"],
        "file": path.name,
        "pull_date": path.stem.split("_")[-1],
        "used_saved_file": used_saved,
        "download_error": error,
        "placeholder_rows_dropped": dropped,
        "first_date": series.index[0].date().isoformat(),
        "last_date": series.index[-1].date().isoformat(),
        "rows": len(series),
    }
    return series, info


def load_all(refresh: bool = True):
    """Load all managers. Returns (dict of daily series, list of info dicts)."""
    series_dict, infos = {}, []
    for key in MANAGERS:
        s, info = load_unit_values(key, refresh=refresh)
        series_dict[key] = s
        infos.append(info)
    return series_dict, infos


def month_end_levels(daily: pd.Series) -> pd.Series:
    """
    Convert a daily unit value series into one value per month.

    ENPF publishes the unit value for every calendar day; the value on the
    1st day of a month is the value at the END of the previous month
    (e.g. 1 Feb = end of January). This matches how ENPF reports returns
    ("as of 1 September"). Result: PeriodIndex by month, e.g. 2022-01 -> UV on 1 Feb 2022.
    Only re-labelling here, no calculations.
    """
    firsts = daily[daily.index.day == 1]
    out = firsts.copy()
    out.index = (firsts.index - pd.Timedelta(days=1)).to_period("M")
    return out


# =====================================================================
# 2. CPI (stat.gov.kz xlsx, downloaded by hand, never edited)
# =====================================================================

def load_cpi():
    """
    Read monthly CPI from the stat.gov.kz file.
    Takes the column 'К предыдущему месяцу' (to previous month) ->
    'товары и услуги' (all goods and services).
    Returns (series: PeriodIndex month -> index, e.g. 100.7 means +0.7% vs previous month, info).
    """
    path = latest_saved_file("stat_cpi_*.xlsx")
    if path is None:
        raise FileNotFoundError(
            "CPI file stat_cpi_<date>.xlsx not found in data/raw/")

    ws = openpyxl.load_workbook(path, data_only=True, read_only=True).active
    rows = [list(r) for r in ws.iter_rows(values_only=True)]

    # Find the column: header 'К предыдущему месяцу'; its first sub-column is 'товары и услуги'
    col = None
    for r in rows[:10]:
        for j, v in enumerate(r):
            if isinstance(v, str) and v.strip().lower().startswith("к предыдущему месяцу"):
                col = j
                break
        if col is not None:
            break
    if col is None:
        raise ValueError(
            "Column 'К предыдущему месяцу' not found in the CPI file")

    data, year = {}, None
    for r in rows:
        first = r[0]
        if first is None:
            continue
        text = str(first).strip()
        if text.isdigit() and len(text) == 4:          # a year row, e.g. 2022
            year = int(text)
            continue
        month = RU_MONTHS.get(text.lower())
        # future months are empty -> skipped
        if month and year and r[col] is not None:
            data[pd.Period(year=year, month=month, freq="M")] = float(r[col])

    s = pd.Series(data, name="cpi_mom_index").sort_index()
    info = {
        "key": "CPI",
        "label": "Consumer price index, % of previous month, all goods and services",
        "source": "Bureau of National Statistics of Kazakhstan (stat.gov.kz), dynamic tables",
        "file": path.name,
        "pull_date": path.stem.split("_")[-1],
        "first_month": str(s.index[0]),
        "last_month": str(s.index[-1]),
        "rows": len(s),
    }
    return s, info


# =====================================================================
# 3. Deposit rates (nationalbank.kz xlsx, downloaded by hand, never edited)
# =====================================================================

def load_deposit_rates():
    """
    Read the weighted average interest rate on new term deposits of
    individuals in KZT ('Депозиты физических лиц' -> 'срочные, всего' -> KZT).
    The values are annual rates in % (e.g. 14.7 = 14.7% per year) on deposits
    attracted during that month.
    Returns (series: PeriodIndex month -> % per year, info).
    """
    path = latest_saved_file("nbk_deposit_rates_*.xlsx")
    if path is None:
        raise FileNotFoundError(
            "Deposit file nbk_deposit_rates_<date>.xlsx not found in data/raw/")

    ws = openpyxl.load_workbook(path, data_only=True, read_only=True).active
    rows = [list(r) for r in ws.iter_rows(values_only=True)]

    # Header row with months like ' 01.21', the next row has currencies (KZT / СКВ)
    hdr_i = next(i for i, r in enumerate(rows)
                 if sum(isinstance(v, str) and v.strip()[:2].isdigit() and "." in v for v in r) > 5)
    months_row, ccy_row = rows[hdr_i], rows[hdr_i + 1]

    # Month label sits above the KZT column; the next column (СКВ) has no label
    kzt_cols, current = {}, None
    for j, v in enumerate(months_row):
        if isinstance(v, str) and v.strip():
            mm, yy = v.strip().split(".")
            current = pd.Period(year=2000 + int(yy), month=int(mm), freq="M")
        if current is not None and ccy_row[j] == "KZT":
            kzt_cols[current] = j

    # Row 'Депозиты физических лиц', then the first 'срочные, всего' below it
    ind_i = next(i for i, r in enumerate(rows)
                 if isinstance(r[0], str) and r[0].strip().lower().startswith("депозиты физических лиц"))
    term_i = next(i for i in range(ind_i, len(rows))
                  if isinstance(rows[i][0], str) and rows[i][0].strip().lower().startswith("срочные"))
    term_row = rows[term_i]

    s = pd.Series({p: term_row[j]
                  for p, j in kzt_cols.items()}, name="deposit_rate_pct")
    s = pd.to_numeric(s, errors="coerce").dropna(
    ).sort_index()   # '-' -> dropped
    info = {
        "key": "DEPOSIT",
        "label": "Weighted average rate on new term deposits of individuals, KZT, % per year",
        "source": "National Bank of Kazakhstan (nationalbank.kz), deposit market statistics",
        "file": path.name,
        "pull_date": path.stem.split("_")[-1],
        "first_month": str(s.index[0]),
        "last_month": str(s.index[-1]),
        "rows": len(s),
    }
    return s, info


# =====================================================================
# 4. Everything on one monthly calendar
# =====================================================================

def build_monthly_dataset(refresh: bool = True):
    """
    Returns (monthly DataFrame, list of info dicts, join report).

    Columns: one per manager (month-end unit value), 'cpi_mom_index',
    'deposit_rate_pct'. Index: months (PeriodIndex).
    The join report says which months have all series and which months
    are dropped when only the common window is used (for the honesty panel).
    """
    daily, infos = load_all(refresh=refresh)
    cpi, cpi_info = load_cpi()
    dep, dep_info = load_deposit_rates()

    frame = pd.DataFrame({k: month_end_levels(s) for k, s in daily.items()})
    frame["cpi_mom_index"] = cpi
    frame["deposit_rate_pct"] = dep
    frame = frame.sort_index()

    macro_ok = frame[["cpi_mom_index", "deposit_rate_pct"]].notna().all(axis=1)
    common = frame.index[macro_ok & frame["NBRK"].notna()]
    join = {
        "common_first_month": str(common[0]) if len(common) else None,
        "common_last_month": str(common[-1]) if len(common) else None,
        "common_months": len(common),
        "months_without_cpi": [str(p) for p in frame.index[frame["cpi_mom_index"].isna()]],
        "months_without_deposit_rate": [str(p) for p in frame.index[frame["deposit_rate_pct"].isna()]],
    }
    return frame, infos + [cpi_info, dep_info], join


# =====================================================================
# Run from the terminal: python data.py
# =====================================================================

if __name__ == "__main__":
    frame, infos, join = build_monthly_dataset(refresh=True)

    print(f"\n{'Series':<36} {'Rows':>6}  {'From':<11} {'To':<11}  Source")
    print("-" * 95)
    for i in infos:
        if i["key"] in MANAGERS:
            status = "SAVED FILE (offline)" if i["used_saved_file"] else "downloaded now"
            print(f"{i['label']:<36} {i['rows']:>6}  {i['first_date']:<11} {i['last_date']:<11}  "
                  f"{status}, placeholder rows dropped: {i['placeholder_rows_dropped']}")
        else:
            print(f"{i['key']:<36} {i['rows']:>6}  {i['first_month']:<11} {i['last_month']:<11}  "
                  f"file {i['file']}")

    print(f"\nCommon monthly window (all series available): "
          f"{join['common_first_month']} .. {join['common_last_month']} "
          f"({join['common_months']} months)")
    print("\nLast 3 months of the monthly dataset:")
    print(frame.tail(3).round(2).to_string())
    print(f"\nRaw files are saved in: {RAW_DIR}\n")
