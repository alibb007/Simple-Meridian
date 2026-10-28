import html
import io

import pandas as pd
import streamlit as st

from app_pages.common import cached_periods, cached_summary, get_model, require_model
from utils import charts, tour
from utils import mmm as M
from utils import ui


def show_optimization():
    ui.page_header(
        3,
        "Budget plan",
        "Meridian searches for the split that earns the most incremental revenue, keeping each channel "
        "within the limits you set.",
        "savings",
        "teal",
    )
    if not require_model("Budget plan"):
        return

    mmm = st.session_state.mmm
    periods = cached_periods(mmm, st.session_state.model_key)

    start, end = _period_picker(periods)
    tour.here("s3-settings")
    with st.container(border=True, key="s3-settings"):
        c1, c2 = st.columns([1.6, 1], gap="large")
        with c1:
            limit = st.slider("Max change per channel", 5, 100, 30, step=5, format="±%d%%", key="opt_limit",
                              help="Keeps the plan realistic. ±30% is Meridian's default.")
        with c2:
            mode = st.segmented_control("Budget", ["Same total", "New total"], default="Same total", key="opt_mode")
            budget = None
            if mode == "New total":
                hist = _historical_budget(get_model(), start, end)
                budget = st.number_input("New total budget ($)", min_value=0.0, value=float(round(hist, -3)),
                                         step=max(1000.0, round(hist * 0.05, -3)), format="%.0f", key="opt_budget")
        submitted = st.button("Optimize budget", type="primary", icon=":material/tune:", key="opt_go")

    if submitted:
        with st.spinner("Optimizing… usually under a minute"):
            try:
                cached = _optimize(st.session_state.model_key, start, end, budget, limit)
                st.session_state.optimization = {
                    **cached, "curves": None, "report": None, "params": (start, end, budget, limit),
                }
            except Exception as e:
                st.error(f"Optimization failed: {e}")
                return

    opt = st.session_state.optimization
    if opt is None:
        ui.callout("Pick a period and limits, then press <b>Optimize budget</b>.", "tune")
        return
    _results(opt)


def _period_picker(periods: list[str]) -> tuple[str, str]:
    """Quick choices plus an in-app calendar; dates snap to the model's weeks."""
    weeks = pd.to_datetime(pd.Series(periods))
    first, last = weeks.iloc[0], weeks.iloc[-1]
    # Latest calendar year the data covers (at least 50 of its weeks).
    per_year = weeks.dt.year.value_counts()
    full_years = sorted(y for y, n in per_year.items() if n >= 50)
    last_full_year = full_years[-1] if full_years else last.year
    choices = {
        "Latest 52 weeks": (weeks.iloc[max(0, len(weeks) - 52)], last),
        f"Calendar year {last_full_year}": (pd.Timestamp(last_full_year, 1, 1), pd.Timestamp(last_full_year, 12, 31)),
        "Full history": (first, last),
        "Custom dates": None,
    }
    with st.container(border=True, key="s3-period"):
        st.markdown(f'<div style="display:flex;gap:.55rem;align-items:center;font-weight:700">'
                    f'{ui.icon("date_range", 20, ui.PRIMARY)}Plan based on spend in</div>', unsafe_allow_html=True)
        pick = st.segmented_control("Period", list(choices), default="Latest 52 weeks", key="opt_period",
                                    label_visibility="collapsed")
        pick = pick or "Latest 52 weeks"
        if pick == "Custom dates":
            d = st.date_input("From – to", value=(choices["Latest 52 weeks"][0].date(), last.date()),
                              min_value=first.date(), max_value=last.date(), format="DD/MM/YYYY", key="opt_dates")
            lo, hi = (pd.Timestamp(d[0]), pd.Timestamp(d[1])) if isinstance(d, (tuple, list)) and len(d) == 2 \
                else choices["Latest 52 weeks"]
        else:
            lo, hi = choices[pick]
        inside = weeks[(weeks >= lo) & (weeks <= hi)]
        if inside.empty:
            st.warning("No model weeks fall in that range; using the latest 52 weeks.")
            lo, hi = choices["Latest 52 weeks"]
            inside = weeks[(weeks >= lo) & (weeks <= hi)]
        start, end = inside.iloc[0].strftime("%Y-%m-%d"), inside.iloc[-1].strftime("%Y-%m-%d")
        st.caption(f"{len(inside)} weeks: {inside.iloc[0]:%d %b %Y} to {inside.iloc[-1]:%d %b %Y}")
    return start, end


@st.cache_resource(show_spinner=False, max_entries=16, ttl=3600)
def _optimize(model_key: str, start: str, end: str, budget, limit: int) -> dict:
    """Shared across sessions: the same model + settings always give the same plan."""
    model = get_model()
    res = M.optimize(model, start, end, budget, limit)
    return {
        "res": res,
        "table": M.optimization_table(res),
        "totals": M.optimization_totals(res),
        "historical_budget": _historical_budget(model, start, end),
    }


def _historical_budget(mmm, start, end) -> float:
    try:
        spend = M.lib().analyzer.Analyzer(mmm).get_historical_spend(selected_times=[p for p in M.time_periods(mmm) if start <= p <= end])
        return float(spend.values.sum())
    except Exception:
        summary = cached_summary(mmm, st.session_state.model_key)
        return float(summary[summary.is_total].spend.iloc[0])


def _results(opt):
    t, table = opt["totals"], opt["table"]
    start, end, _, limit = opt["params"]
    gain = t["outcome_after"] - t["outcome_before"]
    gain_pct = gain / t["outcome_before"] * 100 if t["outcome_before"] else 0
    # With a new total, Meridian scales the historical mix to that total, so
    # "before" means "old mix at the new budget". Compare budget to actuals.
    hist = opt.get("historical_budget") or t["budget_before"]
    budget_delta = t["budget_after"] - hist

    st.markdown("### The plan")
    st.caption(f"Based on spend from {start} to {end} · each channel limited to ±{limit}%")
    same = abs(budget_delta) < 0.005 * hist
    roi_up = t["roi_after"] >= t["roi_before"]
    ui.tiles([
        dict(label="Budget", value=ui.money(t["budget_after"]), icon="account_balance_wallet", accent="blue",
             detail="same total as actual" if same else f"{'+' if budget_delta > 0 else ''}{ui.money(budget_delta)} vs. actual {ui.money(hist)}"),
        dict(label="Incremental revenue", value=ui.money(t["outcome_after"]), icon="trending_up", accent="green",
             chip=f"{gain_pct:+.1f}%", direction="up" if gain >= 0 else "down",
             detail=f"{'+' if gain >= 0 else ''}{ui.money(gain)} vs. current mix"),
        dict(label="ROI", value=f"{t['roi_after']:.2f}×", icon="percent", accent="violet",
             chip=f"{t['roi_after'] - t['roi_before']:+.2f}", direction="up" if roi_up else "down",
             detail=f"was {t['roi_before']:.2f}×"),
    ])

    moves = table.sort_values("spend_change")
    cut = moves[moves.spend_change_pct < -1].head(2)
    add = moves[moves.spend_change_pct > 1].tail(2).iloc[::-1]
    if len(add) or len(cut):
        parts = []
        if len(add):
            parts.append("Move money into " + " and ".join(f"<b>{html.escape(c)}</b> ({p:+.0f}%)" for c, p in zip(add.channel, add.spend_change_pct)))
        if len(cut):
            parts.append("out of " + " and ".join(f"<b>{html.escape(c)}</b> ({p:+.0f}%)" for c, p in zip(cut.channel, cut.spend_change_pct)))
        ui.callout("; ".join(parts) + ". Make big shifts in stages and watch results, since the model is an estimate.",
                   "swap_horiz")

    colors = charts.color_map(table.channel)
    tabs = st.tabs([":material/swap_vert: Spend changes", ":material/show_chart: On the curves",
                    ":material/download: Table & export"])
    with tabs[0]:
        st.markdown("### Budget mix: actual vs. plan")
        st.plotly_chart(charts.allocation_bars(table, colors), config=charts.CONFIG)
        st.markdown("### Change in spend by channel")
        st.caption("Blue: spend more. Red: spend less. Labels are % change against the period's actual spend.")
        st.plotly_chart(charts.spend_change(table), config=charts.CONFIG)

    with tabs[1]:
        st.markdown("### Today vs. the plan on each response curve")
        st.caption("Ringed dot: actual spend. Diamond: the plan. The plan moves budget toward curves that are still steep.")
        if opt["curves"] is None:
            with st.spinner("Computing curves…"):
                opt["curves"] = M.optimization_curves(opt["res"])
        st.plotly_chart(charts.response_grid(opt["curves"], colors, show_ci=False, optimized=table), config=charts.CONFIG)

    with tabs[2]:
        view = table[["channel", "current_spend", "optimized_spend", "spend_change_pct",
                      "current_outcome", "optimized_outcome", "optimized_mroi"]]
        st.dataframe(
            view, hide_index=True,
            column_config={
                "channel": "Channel",
                "current_spend": st.column_config.NumberColumn("Actual spend ($)", format="compact"),
                "optimized_spend": st.column_config.NumberColumn("Planned spend ($)", format="compact"),
                "spend_change_pct": st.column_config.NumberColumn("Change", format="%+.1f%%"),
                "current_outcome": st.column_config.NumberColumn("Revenue now ($)", format="compact"),
                "optimized_outcome": st.column_config.NumberColumn("Revenue with plan ($)", format="compact"),
                "optimized_mroi": st.column_config.NumberColumn("Marginal ROI after", format="%.2f"),
            },
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button("CSV", table.to_csv(index=False), "budget_plan.csv", "text/csv",
                               icon=":material/download:", on_click="ignore", width="stretch")
        with c2:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="xlsxwriter") as xw:
                table.to_excel(xw, index=False, sheet_name="Plan")
                pd.DataFrame([t]).to_excel(xw, index=False, sheet_name="Totals")
            st.download_button("Excel", buf.getvalue(), "budget_plan.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               icon=":material/download:", on_click="ignore", width="stretch")
        with c3:
            if opt["report"] is None:
                if st.button("Build Meridian report", icon=":material/description:", width="stretch"):
                    with st.spinner("Building report…"):
                        opt["report"] = M.optimization_report_html(opt["res"])
                    st.rerun()
            else:
                st.download_button("Meridian HTML report", opt["report"], "budget_optimization.html", "text/html",
                                   icon=":material/download:", on_click="ignore", width="stretch")
