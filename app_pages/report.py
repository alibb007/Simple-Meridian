"""Meridian's own report charts, one by one, each with a plain-words explanation."""
import html
import json
import os

import pandas as pd
import streamlit as st

from app_pages.common import DEMO_DIR, _is_demo, get_model, require_model
from utils import mmm as M
from utils import ui
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


def facet_panels(spec: dict) -> list[tuple[str, dict]] | None:
    """Split a wrapped facet chart (`columns` set) into one chart per panel.

    Vega-Lite can't stretch a facet to its container, so Meridian's 3-across curves (400 px panels)
    overflow the card. One chart per panel, each `width: container`, fits any screen. The color
    scale keeps every channel in its domain so each panel keeps Meridian's color for it.
    """
    facet = spec.get("facet") or {}
    field = facet.get("field")
    if not field or "columns" not in spec or "spec" not in spec:
        return None
    name = (spec.get("data") or {}).get("name")
    rows = (spec.get("datasets") or {}).get(name)
    if rows is None:
        return None
    values = sorted({str(r[field]) for r in rows if r.get(field) is not None})
    inner = json.loads(json.dumps(spec["spec"]))
    for layer in inner.get("layer", [inner]):
        enc = layer.get("encoding", {})
        color = enc.get("color")
        if color and color.get("field") == field:
            color["scale"] = {**color.get("scale", {}), "domain": values}
        # Per-panel legends would squeeze each narrow plot; the card's caption explains the marks instead.
        for ch in ("color", "strokeDash", "shape", "size", "opacity"):
            if isinstance(enc.get(ch), dict):
                enc[ch]["legend"] = None
    panels = []
    for v in values:
        sub = {k: val for k, val in spec.items() if k not in ("facet", "spec", "columns", "resolve", "title", "datasets")}
        sub.update(json.loads(json.dumps(inner)))
        sub["datasets"] = {name: [r for r in rows if str(r.get(field)) == v]}
        sub["title"] = {"text": v, "anchor": "start", "fontSize": 14}
        sub["width"], sub["height"] = "container", 260
        panels.append((v, sub))
    return panels


def _chart_card(c: dict, spec: dict | None):
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
        elif (panels := facet_panels(spec)) is not None:
            cols = st.columns(2, gap="medium")
            for i, (v, sub) in enumerate(panels):
                with cols[i % 2]:
                    st.vega_lite_chart(sub, width="stretch", key=f"mrchart-{c['id']}-{i}")
            if c.get("legend"):
                st.caption(c["legend"])
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
