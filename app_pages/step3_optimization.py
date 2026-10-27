import io

import pandas as pd
import streamlit as st

from app_pages.common import cached_summary, require_model
from utils import charts
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
    periods = M.time_periods(mmm)
    default_start = periods[max(0, len(periods) - 52)]

    with st.form("opt_form", border=False):
        c1, c2 = st.columns([1.6, 1], gap="large")
        with c1:
            start, end = st.select_slider(
                "Plan based on spend in", options=periods, value=(default_start, periods[-1]), key="opt_range",
                help="The optimizer starts from what you actually spent in this window. The last 52 weeks is a good default.",
            )
            limit = st.slider("Max change per channel", 5, 100, 30, step=5, format="±%d%%", key="opt_limit",
                              help="Keeps the plan realistic. ±30% is Meridian's default.")
        with c2:
            mode = st.radio("Budget", ["Same total as before", "Set a new total"], key="opt_mode")
            budget = None
            if mode == "Set a new total":
                hist = _historical_budget(mmm, start, end)
                budget = st.number_input("New total budget ($)", min_value=0.0, value=float(round(hist, -3)),
                                         step=max(1000.0, round(hist * 0.05, -3)), format="%.0f", key="opt_budget")
        submitted = st.form_submit_button("Optimize budget", type="primary", icon=":material/tune:")

    if submitted:
        with st.spinner("Optimizing… usually under a minute"):
            try:
                hist = _historical_budget(mmm, start, end)
                res = M.optimize(mmm, start, end, budget, limit)
                st.session_state.optimization = {
                    "res": res,
                    "table": M.optimization_table(res),
                    "totals": M.optimization_totals(res),
                    "curves": None,
                    "report": None,
                    "params": (start, end, budget, limit),
                    "historical_budget": hist,
                }
            except Exception as e:
                st.error(f"Optimization failed: {e}")
                return

    opt = st.session_state.optimization
    if opt is None:
        ui.callout("Pick a period and limits, then press <b>Optimize budget</b>.", "tune")
        return
    _results(opt)


def _historical_budget(mmm, start, end) -> float:
    try:
        from meridian.analysis import analyzer
        spend = analyzer.Analyzer(mmm).get_historical_spend(selected_times=[p for p in M.time_periods(mmm) if start <= p <= end])
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
            parts.append("Move money into " + " and ".join(f"<b>{c}</b> ({p:+.0f}%)" for c, p in zip(add.channel, add.spend_change_pct)))
        if len(cut):
            parts.append("out of " + " and ".join(f"<b>{c}</b> ({p:+.0f}%)" for c, p in zip(cut.channel, cut.spend_change_pct)))
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
