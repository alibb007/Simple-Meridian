"""Meridian's own report charts, one by one, each with a plain-words explanation."""
import html
import json
import os

import pandas as pd
import streamlit as st

from app_pages.common import DEMO_DIR, _is_demo, get_model, require_model
from utils import mmm as M
from utils import tour, ui
from utils.report_charts import MODEL_CHARTS, PLAN_CHARTS


@st.cache_data(show_spinner=False, max_entries=8, ttl=3600)
def _model_specs(_mmm, model_key: str) -> dict:
    if _is_demo(model_key):
        with open(os.path.join(DEMO_DIR, "report_charts.json")) as f:
            return json.load(f)
    return M.report_chart_specs(_mmm)


@st.cache_data(show_spinner=False, max_entries=8, ttl=3600)
def _demo_plan_specs(model_key: str) -> dict:
    with open(os.path.join(DEMO_DIR, "plan_charts.json")) as f:
        return json.load(f)


def _plan_specs() -> tuple[dict | None, str]:
    opt = st.session_state.get("optimization")
    if opt is not None:
        if opt.get("plan_specs") is None:
            opt["plan_specs"] = M.plan_chart_specs(opt["res"])
        return opt["plan_specs"], "your latest budget plan"
    if _is_demo(st.session_state.model_key):
        return _demo_plan_specs(st.session_state.model_key), "the demo's default plan (last 52 weeks, ±30%)"
    return None, ""


def _chart_card(c: dict, spec: dict | None):
    tour.here(f"mr-{c['id']}")
    with st.container(border=True, key=f"mr-{c['id']}"):
        st.markdown(
            f'<div style="display:flex;gap:.7rem;align-items:center">{ui.badge(c["icon"], "violet", 40)}'
            f'<span style="font-family:var(--display);font-weight:700;font-size:1.15rem">{html.escape(c["title"])}</span>'
            f"</div>"
            f'<div class="sm-explain"><p><b>What it shows.</b> {html.escape(c["what"])}</p>'
            f'<p><b>How to read it.</b> {html.escape(c["read"])}</p></div>',
            unsafe_allow_html=True,
        )
        if spec is None:
            ui.callout("Run a budget plan in step 3 to see this chart.", "tune")
        elif "table" in spec:
            t = spec["table"]
            st.dataframe(pd.DataFrame(t["data"], columns=t["columns"]), hide_index=True)
        else:
            st.vega_lite_chart(spec, width="stretch", key=f"mrchart-{c['id']}")


def show_report():
    st.markdown(f'<div class="sm-head">{ui.badge("description", "violet", 52)}<div>'
                f'<div class="sm-kicker">Inside Meridian\'s own report</div>'
                f"<h1>Meridian charts, explained</h1></div></div>", unsafe_allow_html=True)
    st.markdown('<p class="sm-lede">These are the charts Google\'s Meridian puts in its HTML report, drawn by '
                "Meridian itself. Under each title you'll find what it shows and how to read it, in plain words.</p>",
                unsafe_allow_html=True)
    if not require_model("Meridian charts"):
        return

    key = st.session_state.model_key
    with st.spinner("Drawing Meridian's charts…"):
        specs = _model_specs(None if _is_demo(key) else get_model(), key)

    group = None
    for c in MODEL_CHARTS:
        if c["group"] != group:
            group = c["group"]
            st.markdown(f"## {html.escape(group)}")
        _chart_card(c, specs.get(c["id"]))

    plan, source = _plan_specs()
    st.markdown("## Budget plan")
    if source:
        st.caption(f"Charts for {source}.")
    for c in PLAN_CHARTS:
        _chart_card(c, None if plan is None else plan.get(c["id"]))
