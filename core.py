"""
core.py — CORE LAYER: every financial formula of the app, as pure functions.

Rules (from the assignment brief):
  * no internet, no file reading, no Streamlit here;
  * input  = pandas Series / numbers (monthly data, decimals: 0.01 = 1%);
  * output = numbers or Series.
app.py only CALLS these functions; it never does arithmetic on returns itself.

Conventions follow the QIM course slides (see annex/QIM_hand_calculations.xlsx, README sheet):
  monthly returns, sample SD (n-1), annualise volatility with sqrt(12),
  CAGR is geometric, Sharpe uses the SD of EXCESS returns.
"""

import math

import numpy as np
import pandas as pd

MONTHS_PER_YEAR = 12


# =====================================================================
# 1. Returns, inflation, risk-free rate  (Week 2, Week 4, Week 5)
# =====================================================================

def returns(levels: pd.Series) -> pd.Series:
    """Monthly return r_t = UV_t / UV_{t-1} - 1. The first month has no return and is dropped."""
    return (levels / levels.shift(1) - 1).dropna()


def inflation(cpi_index: pd.Series) -> pd.Series:
    """CPI 'to previous month' (100.7) -> monthly inflation as a decimal (0.007)."""
    return cpi_index / 100 - 1


def real_returns(r: pd.Series, pi: pd.Series) -> pd.Series:
    """Real return (1 + r) / (1 + pi) - 1 (exact, not the approximation r - pi)."""
    return (1 + r) / (1 + pi) - 1


def monthly_rf(annual_rate_pct: pd.Series) -> pd.Series:
    """Annual deposit rate in % (12.0) -> monthly rate (1 + y)^(1/12) - 1 (not y/12)."""
    return (1 + annual_rate_pct / 100) ** (1 / MONTHS_PER_YEAR) - 1


def excess(r: pd.Series, rf: pd.Series) -> pd.Series:
    """Excess return over the deposit: x = r - rf."""
    return r - rf


# =====================================================================
# 2. Growth over the period  (Week 2)
# =====================================================================

def cumulative_return(r: pd.Series) -> float:
    """Total growth over the period: product of (1 + r) minus 1."""
    return float(np.prod(1 + r) - 1)


def cagr(r: pd.Series) -> float:
    """Geometric annual growth: (1 + cumulative)^(12 / n) - 1, n = number of months."""
    n = len(r)
    return float((1 + cumulative_return(r)) ** (MONTHS_PER_YEAR / n) - 1)


def wealth_path(r: pd.Series, start: float = 100.0) -> pd.Series:
    """Value of `start` tenge invested at the beginning: W_t = W_{t-1} * (1 + r_t), one value per month of r."""
    return start * (1 + r).cumprod()


# =====================================================================
# 3. Risk  (Week 4)
# =====================================================================

def sample_sd(r: pd.Series) -> float:
    """Sample standard deviation (n - 1), same as Excel STDEV.S."""
    return float(r.std(ddof=1))


def annual_vol(r: pd.Series) -> float:
    """Annual volatility = monthly SD * sqrt(12)."""
    return sample_sd(r) * math.sqrt(MONTHS_PER_YEAR)


def drawdown_series(r: pd.Series) -> pd.Series:
    """Drawdown in every month: W / (highest W so far, start included) - 1."""
    start = 100.0
    w = wealth_path(r, start)
    peak = w.cummax().clip(lower=start)     # the starting value counts as a peak too
    return w / peak - 1


def max_drawdown(r: pd.Series) -> float:
    """Maximum drawdown: the most negative drawdown (e.g. -0.10 = fell 10% from a peak)."""
    return float(drawdown_series(r).min())


def recovery_needed(mdd: float) -> float:
    """Gain needed to get back to the peak after a loss L: L / (1 - L)."""
    loss = abs(mdd)
    return loss / (1 - loss)


def correlation(a: pd.Series, b: pd.Series) -> float:
    """Pearson correlation of two return series (same months)."""
    return float(np.corrcoef(a, b)[0, 1])


# =====================================================================
# 4. Mixing a manager with ENPF  (Week 4 diversification, Week 8 weights)
# =====================================================================

def mix_vol(w: float, sd1: float, sd2: float, rho: float) -> float:
    """Volatility of a 2-asset mix: sqrt(w^2 s1^2 + (1-w)^2 s2^2 + 2 w (1-w) rho s1 s2)."""
    return math.sqrt(w**2 * sd1**2 + (1 - w)**2 * sd2**2 + 2 * w * (1 - w) * rho * sd1 * sd2)


def diversification_benefit(w: float, r1: pd.Series, r2: pd.Series) -> float:
    """Weighted average of the two annual volatilities minus the volatility of the mix (annual)."""
    s1, s2 = annual_vol(r1), annual_vol(r2)
    return w * s1 + (1 - w) * s2 - mix_vol(w, s1, s2, correlation(r1, r2))


def rebalanced_returns(r1: pd.Series, r2: pd.Series, w: float) -> pd.Series:
    """Monthly rebalancing back to weight w: r_p = w * r1 + (1 - w) * r2 every month."""
    return w * r1 + (1 - w) * r2


def buy_and_hold_cumulative(r1: pd.Series, r2: pd.Series, w: float) -> float:
    """One-off split, never rebalanced: w * prod(1 + r1) + (1 - w) * prod(1 + r2) - 1."""
    return float(w * np.prod(1 + r1) + (1 - w) * np.prod(1 + r2) - 1)


# =====================================================================
# 5. Risk-adjusted return  (Week 5)
# =====================================================================

def sharpe(x: pd.Series) -> float:
    """Annual Sharpe ratio: mean(x) / SD(x) * sqrt(12), x = excess returns over the deposit."""
    return float(x.mean() / sample_sd(x) * math.sqrt(MONTHS_PER_YEAR))


def sharpe_se(sr_annual: float, n: int) -> float:
    """Standard error of the annual Sharpe (Lo): sqrt(12) * sqrt((1 + SR_m^2 / 2) / n), SR_m = SR / sqrt(12)."""
    sr_m = sr_annual / math.sqrt(MONTHS_PER_YEAR)
    return math.sqrt(MONTHS_PER_YEAR) * math.sqrt((1 + sr_m**2 / 2) / n)


def sortino(x: pd.Series) -> float:
    """Sortino: mean(x) * 12 / downside deviation; downside = sqrt(sum(min(x,0)^2) / n) * sqrt(12)."""
    downside = math.sqrt(float((np.minimum(x, 0) ** 2).sum()) / len(x)) * math.sqrt(MONTHS_PER_YEAR)
    return float(x.mean() * MONTHS_PER_YEAR / downside)


def calmar(r: pd.Series) -> float:
    """Calmar: CAGR / |maximum drawdown|."""
    return cagr(r) / abs(max_drawdown(r))


def m_squared(r: pd.Series, b: pd.Series, rf: pd.Series) -> float:
    """
    M2 vs ENPF (HEADLINE), % per year as a decimal.
    = Sharpe(manager) * sigma_ENPF + mean(rf)*12 - mean(r_ENPF)*12,
    sigma_ENPF = SD of ENPF excess returns * sqrt(12).  M2 of ENPF vs itself = 0.
    Meaning: extra annual return of the manager if it took exactly ENPF's level of risk.
    """
    sigma_b = annual_vol(excess(b, rf))
    return sharpe(excess(r, rf)) * sigma_b + rf.mean() * MONTHS_PER_YEAR - b.mean() * MONTHS_PER_YEAR


# =====================================================================
# 6. Comparison with ENPF  (Week 5 tracking error, Week 6 beta)
# =====================================================================

def beta_alpha_r2(y: pd.Series, x: pd.Series) -> dict:
    """
    Regression of manager EXCESS returns (y) on ENPF EXCESS returns (x), y = a + beta * x + e.
    Returns beta, annual alpha (a * 12), R^2, SE of beta and its 95% confidence interval.
    """
    n = len(y)
    x_dev, y_dev = x - x.mean(), y - y.mean()
    sxx = float((x_dev**2).sum())
    beta = float((x_dev * y_dev).sum()) / sxx
    a = float(y.mean() - beta * x.mean())
    resid = y - a - beta * x
    ssr = float((resid**2).sum())
    syy = float((y_dev**2).sum())
    se_beta = math.sqrt(ssr / (n - 2)) / math.sqrt(sxx)
    return {
        "beta": beta,
        "alpha_annual": a * MONTHS_PER_YEAR,
        "r2": 1 - ssr / syy,
        "se_beta": se_beta,
        "ci_low": beta - 1.96 * se_beta,
        "ci_high": beta + 1.96 * se_beta,
    }


def tracking_error(r: pd.Series, b: pd.Series) -> float:
    """Annual tracking error vs ENPF: SD(r - b) * sqrt(12)."""
    return annual_vol(r - b)


def information_ratio(r: pd.Series, b: pd.Series):
    """mean(r - b) / SD(r - b) * sqrt(12). Returns None if the two series are identical (SD ~ 0)."""
    d = r - b
    sd = sample_sd(d)
    if sd < 1e-12:
        return None
    return float(d.mean() / sd * math.sqrt(MONTHS_PER_YEAR))


def mean_diff_tstat(r: pd.Series, b: pd.Series) -> float:
    """t-statistic of the mean monthly difference r - b: mean / (SD / sqrt(n)). |t| < 2 -> not significant."""
    d = r - b
    return float(d.mean() / (sample_sd(d) / math.sqrt(len(d))))


# =====================================================================
# 7. Honesty checks  (Week 5)
# =====================================================================

def hit_rate(x: pd.Series) -> float:
    """Share of months in which the manager beat the deposit (x > 0)."""
    return float((x > 0).mean())


def autocorr_lag1(r: pd.Series) -> float:
    """Lag-1 autocorrelation: sum(d_t * d_{t-1}) / sum(d^2), d = r - mean. > 0.4 -> suspiciously smooth prices."""
    d = (r - r.mean()).to_numpy()
    return float((d[1:] * d[:-1]).sum() / (d**2).sum())


# =====================================================================
# 8. Plain-language summary for ordinary savers
# =====================================================================

def worst_fall(r: pd.Series) -> dict:
    """
    The deepest fall from a previous high: depth, the month of the high and the month of the bottom.
    The start of the period counts as a high.
    """
    dd = drawdown_series(r)
    bottom = dd.idxmin()
    before = wealth_path(r).loc[:bottom]
    peak = before.idxmax() if before.max() > 100.0 else None      # None = the start of the period
    return {"depth": float(dd.min()), "fall": abs(float(dd.min())), "peak_month": peak, "bottom_month": bottom}


def saver_summary(r: pd.Series, b: pd.Series, rf: pd.Series, pi: pd.Series, amount: float) -> dict:
    """
    Everything the screen needs to explain the result in plain words, on the same months.
    r = manager, b = ENPF, rf = deposit (monthly), pi = inflation (monthly), amount = KZT invested.
    """
    final = {
        "manager": float(wealth_path(r, amount).iloc[-1]),
        "enpf": float(wealth_path(b, amount).iloc[-1]),
        "deposit": float(wealth_path(rf, amount).iloc[-1]),
        "prices": float(wealth_path(pi, amount).iloc[-1]),   # what you needed just to keep purchasing power
    }
    real = {
        "manager": cagr(real_returns(r, pi)),
        "enpf": cagr(real_returns(b, pi)),
        "deposit": cagr(real_returns(rf, pi)),
    }
    m2 = m_squared(r, b, rf)
    t = mean_diff_tstat(r, b)
    return {
        "final": final,
        "vs_enpf_kzt": final["manager"] - final["enpf"],
        "vs_deposit_kzt": final["manager"] - final["deposit"],
        "vs_prices_kzt": final["manager"] - final["prices"],
        "gap_enpf_kzt": abs(final["manager"] - final["enpf"]),          # size of the gap, sign below
        "gap_deposit_kzt": abs(final["manager"] - final["deposit"]),
        "more_than_enpf": bool(final["manager"] > final["enpf"]),
        "more_than_deposit": bool(final["manager"] > final["deposit"]),
        "real": real,
        "real_abs": {k: abs(v) for k, v in real.items()},              # for "grew / shrank by X%" wording
        "grew": {k: bool(v > 0) for k, v in real.items()},
        "m2": m2,
        "t": t,
        "beat_prices": bool(real["manager"] > 0),
        "beat_enpf_same_risk": bool(m2 > 0),
        "beat_deposit": bool(real["manager"] > real["deposit"]),
        "reliable": bool(abs(t) >= 2),
        "months": len(r),
    }


def split_transfer(r: pd.Series, b: pd.Series, w: float, amount: float) -> dict:
    """
    Moving only a share w to the manager, the rest stays in ENPF. Values in KZT at the end of the period.
    one_off = transfer once and never touch it (buy-and-hold); rebalanced = reset to w every month.
    """
    rp = rebalanced_returns(r, b, w)
    return {
        "one_off_kzt": amount * (1 + buy_and_hold_cumulative(r, b, w)),
        "rebalanced_kzt": float(wealth_path(rp, amount).iloc[-1]),
        "vol_mix": annual_vol(rp),
        "vol_average": w * annual_vol(r) + (1 - w) * annual_vol(b),
        "benefit": diversification_benefit(w, r, b),
        "worst_fall_mix": max_drawdown(rp),
    }


# =====================================================================
# 9. Window: put series on the same months
# =====================================================================

def align_window(series: dict, start=None, end=None):
    """
    Keep only the months where ALL given series have a value (optionally inside [start, end]).
    Returns (DataFrame of aligned series, list of months dropped from the requested range) —
    the dropped months go to the honesty panel.
    """
    frame = pd.DataFrame(series)
    if start is not None:
        frame = frame.loc[frame.index >= pd.Period(start, freq="M")]
    if end is not None:
        frame = frame.loc[frame.index <= pd.Period(end, freq="M")]
    complete = frame.dropna()
    dropped = [str(p) for p in frame.index.difference(complete.index)]
    return complete, dropped
