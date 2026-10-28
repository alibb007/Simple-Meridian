import html

import streamlit as st

from app_pages.common import (
    cached_curves, cached_fit_series, cached_periods, cached_quality, cached_summary, get_model,
    model_download_button, require_model,
)
from utils import charts
from utils import mmm as M
from utils import ui


def show_insights():
    ui.page_header(2, "Insights", "What each channel brought back, how sure the model is, and where extra spend stops helping.",
                   "insights", "violet")
    if not require_model("Insights"):
        return
    st.session_state.visited_insights = True

    mmm, key = st.session_state.mmm, st.session_state.model_key
    with st.spinner("Reading the model…"):
        summary = cached_summary(mmm, key)
        series = cached_fit_series(mmm, key)
        quality = cached_quality(mmm, key)

    total = summary[summary.is_total].iloc[0]
    channels = summary[~summary.is_total]
    colors = charts.color_map(channels.channel)
    baseline = float(series.baseline.sum())
    best = channels.sort_values("roi", ascending=False).iloc[0]
    room = channels[channels.mroi > 1].sort_values("mroi", ascending=False)
    media_share = total.incremental / (total.incremental + baseline) * 100

    ui.tiles([
        dict(label="Media spend", value=ui.money(total.spend), detail=f"across {len(channels)} channels",
             icon="payments", accent="blue"),
        dict(label="Revenue driven by media", value=ui.money(total.incremental),
             detail=f"{media_share:.0f}% of modeled revenue", icon="trending_up", accent="green"),
        dict(label="Blended ROI", value=f"{total.roi:.2f}×",
             detail=f"90% range {total.roi_lo:.2f} – {total.roi_hi:.2f}", icon="percent", accent="violet"),
        dict(label="Top channel by ROI", value=best.channel, detail=f"{best.roi:.2f} revenue per $1",
             icon="workspace_premium", accent="amber"),
    ])

    if len(room):
        names = ", ".join(f"<b>{html.escape(c)}</b>" for c in room.channel.head(3))
        ui.callout(f"The next dollar still pays back in {names} (marginal ROI above 1). "
                   "These are the first places to test more budget.", "lightbulb")
    else:
        ui.callout("Every channel's next dollar returns less than $1 (marginal ROI below 1), so adding budget "
                   "would lose money. Step 3 can still shift spend between channels.", "info")

    ui.legend(colors)
    tabs = st.tabs([":material/bar_chart: ROI", ":material/donut_large: Contribution",
                    ":material/show_chart: Response curves", ":material/fact_check: Model fit",
                    ":material/description: Report"])

    with tabs[0]:
        with st.container(key="s2-roi"):
            st.markdown("### Return per dollar")
            st.caption("Average ROI over the full period. Whiskers show the 90% credible interval; "
                       "wide whiskers mean the data can't pin that channel down.")
            st.plotly_chart(charts.roi_bars(summary, colors), config=charts.CONFIG)
        st.markdown("### Average return vs. return on the next dollar")
        st.caption("A channel can have a high average ROI and still be full, so more money there buys little. Bubble size is spend.")
        st.plotly_chart(charts.roi_vs_mroi(summary, colors), config=charts.CONFIG)
        _summary_table(summary)

    with tabs[1]:
        c1, c2 = st.columns([1, 1.15], gap="medium")
        with c1:
            st.markdown("### Where revenue came from")
            st.caption("Baseline is what the model expects with zero media: brand, seasonality, controls.")
            st.plotly_chart(charts.contribution_donut(baseline, summary, colors), config=charts.CONFIG)
        with c2:
            st.markdown("### Incremental revenue by channel")
            st.caption("Bars are the model's best estimate; whiskers are the 90% interval.")
            st.plotly_chart(charts.contribution_bars(baseline, summary, colors), config=charts.CONFIG)
        st.markdown("### Share of spend vs. share of media revenue")
        st.caption("Light bar: share of spend. Solid bar: share of media revenue. Solid longer than light means the "
                   "channel earns more than its share of the budget.")
        st.plotly_chart(charts.share_bars(summary, colors), config=charts.CONFIG)

    with tabs[2]:
        st.markdown("### Response curves")
        st.caption("Incremental revenue at 0–200% of actual spend. The ringed dot is what you spent. "
                   "Where a curve flattens, more money buys little.")
        show_ci = st.toggle("Show 90% interval", value=True, key="curves_ci")
        with st.spinner("Computing curves…"):
            curves = cached_curves(mmm, key)
        st.plotly_chart(charts.response_grid(curves, colors, show_ci=show_ci), config=charts.CONFIG)

    with tabs[3]:
        st.markdown("### How well the model tracks reality")
        r = quality.get("max_rhat") or 0
        ok = r < 1.2
        ui.tiles([
            dict(label="R²", value=f"{quality['r2']:.3f}", detail="1.0 is a perfect fit", icon="target", accent="blue"),
            dict(label="MAPE", value=f"{quality['mape'] * 100:.1f}%", detail="average weekly error",
                 icon="straighten", accent="violet"),
            dict(label="wMAPE", value=f"{quality['wmape'] * 100:.1f}%", detail="weighted by revenue",
                 icon="balance", accent="teal"),
            dict(label="Max R-hat", value=f"{r:.2f}", chip="Converged" if ok else "Not converged",
                 direction="up" if ok else "down", detail="" if ok else "Fit again with more samples",
                 icon="check_circle" if ok else "error", accent="green" if ok else "rose"),
        ])
        st.plotly_chart(charts.model_fit(series), config=charts.CONFIG)
        st.caption("A good fit is necessary but not enough: a model can match history and still credit the wrong "
                   "channel. Check the ROI intervals and, where you can, compare with lift tests.")

    with tabs[4]:
        _report(mmm)

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
    if st.button("Next: plan the budget", type="primary", icon=":material/arrow_forward:"):
        ui.go_to("step3")


def _summary_table(summary):
    d = summary[~summary.is_total][["channel", "spend", "incremental", "roi", "roi_lo", "roi_hi", "mroi", "cpik"]]
    with st.expander("Table view", icon=":material/table_rows:"):
        st.dataframe(
            d, hide_index=True,
            column_config={
                "channel": "Channel",
                "spend": st.column_config.NumberColumn("Spend ($)", format="compact"),
                "incremental": st.column_config.NumberColumn("Incremental revenue ($)", format="compact"),
                "roi": st.column_config.NumberColumn("ROI", format="%.2f"),
                "roi_lo": st.column_config.NumberColumn("ROI low (90%)", format="%.2f"),
                "roi_hi": st.column_config.NumberColumn("ROI high (90%)", format="%.2f"),
                "mroi": st.column_config.NumberColumn("Marginal ROI", format="%.2f"),
                "cpik": st.column_config.NumberColumn("Cost per incremental $", format="%.2f"),
            },
        )
        st.download_button("Download CSV", d.to_csv(index=False), "channel_summary.csv", "text/csv",
                           icon=":material/download:", on_click="ignore", key="dl_summary_csv")


def _report(mmm):
    st.markdown("### Meridian HTML report")
    st.caption("Google's standard Meridian summary (fit, contribution, ROI, response curves) in one shareable file.")
    periods = cached_periods(mmm, st.session_state.model_key)
    start, end = st.select_slider("Period", options=periods, value=(periods[0], periods[-1]), key="report_range")
    with st.container(horizontal=True):
        if st.button("Build report", type="primary", icon=":material/description:"):
            with st.spinner("Building report…"):
                try:
                    st.session_state.model_report = (start, end, M.model_report_html(get_model(), start, end))
                except Exception as e:
                    st.error(f"Report failed: {e}")
        rep = st.session_state.get("model_report")
        if rep and rep[:2] == (start, end):
            st.download_button("Download report", rep[2], f"meridian_report_{start}_{end}.html", "text/html",
                               icon=":material/download:", on_click="ignore")
        model_download_button("dl_step2")
