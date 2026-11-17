"""
app.py — SCREEN LAYER (Streamlit).  Run:  streamlit run app.py

Rule from the brief: NO calculations here. Every number on screen comes from a
function in core.py; data comes from data.py. This file only picks inputs,
calls functions, formats text and draws.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import core
import data

st.set_page_config(page_title="Should I move my pension savings?", layout="wide")

# ---------------------------------------------------------------------
# Look: fonts, colours, spacing (CSS only — no numbers about money here)
# ---------------------------------------------------------------------
INK, MUTED, LINE, PANEL = "#14304A", "#5B6B7C", "#DCE3EA", "#F2F6F9"
MANAGER, ENPF, DEPOSIT = "#2a78d6", "#eb6834", "#1baf7a"   # validated palette (colour-blind safe)
GOOD, BAD, UNSURE = "#1E7D4B", "#B23A2A", "#9A6A00"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Golos+Text:wght@400;500;600&family=Unbounded:wght@500;700&display=swap');
html, body, [class*="css"], .stMarkdown, p, li, label {{ font-family: 'Golos Text', sans-serif; color: {INK}; }}
.block-container {{ max-width: 1080px; padding-top: 2.2rem; }}
h1, h2, h3 {{ font-family: 'Golos Text', sans-serif; color: {INK}; letter-spacing: -0.01em; }}
h1 {{ font-weight: 600; font-size: 2.1rem; margin-bottom: .2rem; }}
h2 {{ font-weight: 600; font-size: 1.35rem; margin-top: 2.4rem; }}
.lead {{ font-size: 1.08rem; color: {MUTED}; max-width: 62ch; line-height: 1.55; }}
.story {{ border-left: 4px solid {MANAGER}; padding: .2rem 0 .2rem 1.2rem; margin: 1.6rem 0 .4rem; }}
.story .if {{ font-size: 1.05rem; color: {MUTED}; }}
.story .amount {{ font-family: 'Unbounded', sans-serif; font-weight: 700; font-size: 2.6rem;
                  color: {INK}; line-height: 1.15; margin: .35rem 0; }}
.story .then {{ font-size: 1.05rem; line-height: 1.6; max-width: 66ch; }}
.verdicts {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0; margin-top: 1rem;
             border-top: 1px solid {LINE}; }}
.v {{ padding: 1.1rem 1.2rem 1.2rem 0; border-bottom: 1px solid {LINE}; }}
.v:nth-child(odd) {{ border-right: 1px solid {LINE}; }}
.v:nth-child(even) {{ padding-left: 1.4rem; }}
.v .q {{ font-size: .95rem; color: {MUTED}; margin-bottom: .35rem; }}
.v .a {{ font-family: 'Unbounded', sans-serif; font-weight: 500; font-size: 1.35rem; margin-bottom: .35rem; }}
.v .why {{ font-size: .95rem; line-height: 1.5; }}
.v.main {{ background: {PANEL}; padding-left: 1.2rem; }}
.badge {{ font-size: .78rem; color: {MUTED}; border: 1px solid {LINE}; border-radius: 999px;
          padding: .1rem .55rem; margin-left: .4rem; vertical-align: middle; white-space: nowrap; }}
.note {{ font-size: .9rem; color: {MUTED}; line-height: 1.5; max-width: 70ch; }}
.offline {{ background: #FFF4D6; border-left: 4px solid {UNSURE}; padding: .7rem 1rem; margin: 1rem 0; }}
@media (max-width: 760px) {{
  .verdicts {{ grid-template-columns: 1fr; }}
  .v:nth-child(odd) {{ border-right: none; }}
  .v:nth-child(even) {{ padding-left: 0; }}
  .story .amount {{ font-size: 2rem; }}
}}
</style>
""", unsafe_allow_html=True)


def tenge(v):
    return f"{v:,.0f}\u00a0₸".replace(",", "\u00a0")       # non-breaking spaces: the number never splits


def pct(v, digits=1):
    return f"{v:.{digits}%}"


def month(p):
    return p.strftime("%B %Y")


# ---------------------------------------------------------------------
# Data (downloaded once per session; falls back to saved files offline)
# ---------------------------------------------------------------------
@st.cache_data(show_spinner="Loading ENPF, inflation and deposit data…")
def load(refresh: bool):
    return data.build_monthly_dataset(refresh=refresh)


CHOICES = ["BCC", "ALATAU", "CENTRAS", "HGM", "HF"]       # Tansar Capital excluded: history only from April 2026
LABELS = {k: data.MANAGERS[k]["label"] for k in data.MANAGERS}
LABELS["NBRK"] = "ENPF (National Bank)"

with st.sidebar:
    st.markdown("### Your choices")
    refresh = st.toggle("Get the latest data from ENPF", value=True,
                        help="Turn off to use the data already saved on this computer.")

frame, infos, join = load(refresh)
manager_infos = [i for i in infos if i["key"] in data.MANAGERS]
offline = any(i["used_saved_file"] for i in manager_infos)

with st.sidebar:
    key = st.selectbox("Private manager to compare", CHOICES, format_func=lambda k: LABELS[k])
    amount = st.number_input("Your savings, ₸", min_value=10_000, value=1_000_000, step=100_000)

series = {
    "r": core.returns(frame[key].dropna()),
    "b": core.returns(frame["NBRK"].dropna()),
    "rf": core.monthly_rf(frame["deposit_rate_pct"].dropna()),
    "pi": core.inflation(frame["cpi_mom_index"].dropna()),
}
full, _ = core.align_window(series)
months = [str(p) for p in full.index]

with st.sidebar:
    start, end = st.select_slider("Period", options=months, value=(months[0], months[-1]))
    share = st.select_slider("Share to move to the manager", value=0.5, format_func=lambda v: f"{v:.0%}",
                             options=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    st.caption("Past results only. Not a forecast and not investment advice.")

win, dropped = core.align_window(series, start=start, end=end)
r, b, rf, pi = win["r"], win["b"], win["rf"], win["pi"]
s = core.saver_summary(r, b, rf, pi, amount)
first, last = win.index[0], win.index[-1]
name = LABELS[key]

# ---------------------------------------------------------------------
# Title and the story
# ---------------------------------------------------------------------
st.markdown("# Should I move my pension savings?")
st.markdown(f"<p class='lead'>Since 2021 you can move your ENPF savings to a private manager. "
            f"Here is what really happened to the money — after rising prices — compared with leaving it "
            f"in ENPF or putting it in an ordinary tenge bank deposit.</p>", unsafe_allow_html=True)

if offline:
    st.markdown(f"<div class='offline'><b>You are offline.</b> Showing data saved on "
                f"{manager_infos[0]['pull_date']}. Turn the internet on to get newer numbers.</div>",
                unsafe_allow_html=True)

more_enpf = "more" if s["more_than_enpf"] else "less"
more_dep = "more" if s["more_than_deposit"] else "less"
st.markdown(f"""
<div class='story'>
  <div class='if'>If you had put {tenge(amount)} with {name} at the start of {month(first)},
  by the end of {month(last)} you would have</div>
  <div class='amount'>{tenge(s['final']['manager'])}</div>
  <div class='then'>That is <b>{tenge(s['gap_enpf_kzt'])} {more_enpf}</b> than leaving it in ENPF and
  <b>{tenge(s['gap_deposit_kzt'])} {more_dep}</b> than a tenge bank deposit.
  Prices rose so much that you needed <b>{tenge(s['final']['prices'])}</b> just to buy what
  {tenge(amount)} bought at the start.</div>
</div>
""", unsafe_allow_html=True)

# Bars: what the same money became
bars = pd.DataFrame({
    "option": [name, "ENPF (National Bank)", "Tenge bank deposit", "Needed to keep up with prices"],
    "value": [s["final"]["manager"], s["final"]["enpf"], s["final"]["deposit"], s["final"]["prices"]],
    "colour": [MANAGER, ENPF, DEPOSIT, "#FFFFFF"],
    "pattern": ["", "", "", "/"],
})
fig = go.Figure(go.Bar(
    x=bars["value"], y=bars["option"], orientation="h",
    marker=dict(color=bars["colour"], line=dict(color=[MANAGER, ENPF, DEPOSIT, INK], width=1.5),
                pattern=dict(shape=bars["pattern"], fgcolor=INK, size=6)),
    text=[tenge(v) for v in bars["value"]], textposition="outside", cliponaxis=False,
    textfont=dict(family="Unbounded", size=13, color=INK),
    hovertemplate="%{y}: %{text}<extra></extra>"))
fig.update_layout(height=230, margin=dict(l=10, r=120, t=10, b=10), plot_bgcolor="white", paper_bgcolor="white",
                  font=dict(family="Golos Text", color=INK, size=13), bargap=0.35, showlegend=False,
                  xaxis=dict(visible=False), yaxis=dict(autorange="reversed", ticks="", showline=False))
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ---------------------------------------------------------------------
# Four plain verdicts
# ---------------------------------------------------------------------
st.markdown("## The short answer")


def verdict(question, yes, answer_yes, answer_no, why, main=False):
    colour = GOOD if yes else BAD
    word = answer_yes if yes else answer_no
    return (f"<div class='v{' main' if main else ''}'><div class='q'>{question}</div>"
            f"<div class='a' style='color:{colour}'>{'✓' if yes else '✗'} {word}</div>"
            f"<div class='why'>{why}</div></div>")


grew = "grew" if s["beat_prices"] else "shrank"
v1 = verdict("Did the savings beat rising prices?", s["beat_prices"], "Yes", "No",
             f"After inflation the money {grew} by {pct(s['real_abs']['manager'])} a year. "
             f"In ENPF it {'grew' if s['grew']['enpf'] else 'shrank'} by {pct(s['real_abs']['enpf'])} a year.")
v2 = verdict("Was it better than ENPF for the same risk?", s["beat_enpf_same_risk"], "Yes", "No",
             f"Taking the same ups and downs as ENPF, {name} would have earned "
             f"<b>{s['m2']:+.2%} a year</b> compared with ENPF. "
             f"<span class='badge'>main number · M²</span>", main=True)
v3 = verdict("Was it better than a bank deposit?", s["beat_deposit"], "Yes", "No",
             f"A tenge deposit {'grew' if s['grew']['deposit'] else 'shrank'} by "
             f"{pct(s['real_abs']['deposit'])} a year after inflation, with no ups and downs at all.")
gap_text = ("large enough to be unlikely to be pure luck." if s["reliable"] else
            "small compared with normal month-to-month swings, so it could be luck. "
            "A few more years of data could change the ranking.")
reliable_why = (f"With {s['months']} months of history the difference from ENPF is {gap_text} "
                f"<span class='badge'>t = {s['t']:.2f}, need about 2</span>")
v4 = (f"<div class='v'><div class='q'>Can we trust the difference from ENPF?</div>"
      f"<div class='a' style='color:{GOOD if s['reliable'] else UNSURE}'>"
      f"{'✓ Fairly' if s['reliable'] else '≈ Not yet'}</div><div class='why'>{reliable_why}</div></div>")
st.markdown(f"<div class='verdicts'>{v2}{v1}{v3}{v4}</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# How the money moved month by month
# ---------------------------------------------------------------------
st.markdown(f"## How {tenge(amount)} moved, month by month")
paths = {
    name: (core.wealth_path(r, amount), MANAGER, "solid"),
    "ENPF": (core.wealth_path(b, amount), ENPF, "solid"),
    "Bank deposit": (core.wealth_path(rf, amount), DEPOSIT, "solid"),
    "Prices": (core.wealth_path(pi, amount), INK, "dash"),
}
fig2 = go.Figure()
for label, (path, colour, dash) in paths.items():
    x = path.index.to_timestamp(how="end")
    fig2.add_trace(go.Scatter(x=x, y=path.values, name=label, mode="lines",
                              line=dict(color=colour, width=2.4 if label == name else 2, dash=dash),
                              hovertemplate=f"{label}: %{{y:,.0f}} ₸<extra></extra>"))
    fig2.add_annotation(x=x[-1], y=path.values[-1], text=label, showarrow=False, xanchor="left", xshift=8,
                        font=dict(color=colour, size=12))
fig2.update_layout(height=380, margin=dict(l=10, r=130, t=10, b=10), hovermode="x unified",
                   plot_bgcolor="white", paper_bgcolor="white", font=dict(family="Golos Text", color=INK),
                   legend=dict(orientation="h", y=-0.15),
                   yaxis=dict(gridcolor="#EEF2F5", tickformat=",.0f", ticksuffix=" ₸"),
                   xaxis=dict(showgrid=False))
st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

wf, wf_enpf = core.worst_fall(r), core.worst_fall(b)
since = "the start" if wf["peak_month"] is None else month(wf["peak_month"])
st.markdown(f"<p class='note'><b>The roughest patch:</b> from {since} to {month(wf['bottom_month'])} "
            f"the savings with {name} fell by {pct(wf['fall'])} from their earlier high. "
            f"In ENPF the worst fall was {pct(wf_enpf['fall'])}. A bank deposit never falls.</p>",
            unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Moving only part of the savings
# ---------------------------------------------------------------------
st.markdown("## What if you move only part?")
sp = core.split_transfer(r, b, share, amount)
st.markdown(f"<p class='note' style='color:{INK}'>Move <b>{share:.0%}</b> to {name} once and keep the rest in "
            f"ENPF: by {month(last)} you would have <b>{tenge(sp['one_off_kzt'])}</b>. "
            f"Splitting also makes the ride smoother — yearly ups and downs of {pct(sp['vol_mix'])} instead of "
            f"{pct(sp['vol_average'])} on average for the two parts, because they do not always move together.</p>"
            f"<p class='note'>Change the share in the panel on the left. If you instead reset the split back to "
            f"{share:.0%} every month, you would end with {tenge(sp['rebalanced_kzt'])}.</p>",
            unsafe_allow_html=True)

# ---------------------------------------------------------------------
# For specialists: all course measures (each is covered by a test)
# ---------------------------------------------------------------------
with st.expander("For specialists: all the numbers"):
    def row(ret):
        x = core.excess(ret, rf)
        sr = core.sharpe(x)
        return {
            "Return per year (CAGR)": pct(core.cagr(ret), 2),
            "Real return per year": f"{core.cagr(core.real_returns(ret, pi)):+.2%}",
            "Volatility per year": pct(core.annual_vol(ret), 2),
            "Maximum drawdown": pct(core.max_drawdown(ret), 2),
            "Sharpe vs deposit ± SE": f"{sr:+.2f} ± {core.sharpe_se(sr, len(ret)):.2f}",
            "Sortino": f"{core.sortino(x):+.2f}",
            "Months beating the deposit": pct(core.hit_rate(x), 0),
            "Lag-1 autocorrelation": f"{core.autocorr_lag1(ret):+.2f}",
        }
    st.dataframe(pd.DataFrame({name: row(r), "ENPF (National Bank)": row(b)}), use_container_width=True)
    reg = core.beta_alpha_r2(core.excess(r, rf), core.excess(b, rf))
    ir = core.information_ratio(r, b)
    st.markdown(
        f"**Versus ENPF:** M² {s['m2']:+.2%} per year · beta {reg['beta']:.2f} "
        f"(95% CI {reg['ci_low']:.2f} – {reg['ci_high']:.2f}) · alpha {reg['alpha_annual']:+.2%} per year · "
        f"R² {reg['r2']:.2f} · correlation {core.correlation(r, b):.2f} · tracking error "
        f"{core.tracking_error(r, b):.2%} · information ratio {'n/a' if ir is None else f'{ir:.2f}'} · "
        f"t-stat {s['t']:.2f}.  \n**Split {share:.0%}:** one-off (buy-and-hold) {tenge(sp['one_off_kzt'])}, "
        f"monthly rebalancing {tenge(sp['rebalanced_kzt'])}, diversification benefit {pct(sp['benefit'], 2)} "
        f"of volatility.")
    st.caption("M² = Sharpe of the manager × ENPF's volatility + deposit rate − ENPF return (all per year). "
               "Sharpe uses the deposit rate as the risk-free rate. Formulas: core.py; checks: annex Excel and tests.")

# ---------------------------------------------------------------------
# Honesty panel
# ---------------------------------------------------------------------
with st.expander("Where the numbers come from and what they cannot tell you", expanded=True):
    rows = []
    for i in infos:
        if i["key"] in data.MANAGERS and i["key"] not in (key, "NBRK"):
            continue
        rows.append({
            "Data": LABELS.get(i["key"], i["label"]),
            "Source": i.get("source", "ENPF JSC, invest.enpf.kz public API"),
            "File": i["file"],
            "Pulled on": i["pull_date"],
            "How loaded": ("saved file (offline)" if i.get("used_saved_file") else "downloaded now")
                          if "used_saved_file" in i else "file downloaded by hand",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    placeholder = next(i["placeholder_rows_dropped"] for i in manager_infos if i["key"] == key)
    st.markdown(f"""
- **Currency and frequency:** everything in tenge (KZT), monthly. A month's value is the ENPF unit value on the
  1st day of the next month.
- **Adjusted or not:** ENPF unit values are already after the managers' fees; nothing else to adjust.
  The deposit is the average rate banks paid on new tenge term deposits of individuals each month
  (National Bank), not the result of one specific deposit.
- **Period:** {month(first)} – {month(last)} ({s['months']} months). Months dropped because a series was
  missing: {", ".join(dropped) if dropped else "none"}.
- **Data problems we fixed:** before its first client money arrived, the ENPF data shows a placeholder value
  of 100 ({placeholder} daily rows removed for {name}). Inflation for 2021 was typed in by hand from two official
  Bureau of National Statistics press releases (see DATA.md).
- **Survivorship:** only managers that exist today are shown; managers that closed (e.g. Jusan Invest) are not.
- **Historical, not a forecast, not investment advice.**
""")
