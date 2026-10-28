import json
import os

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from app_pages.common import DEMO_DIR, demo_available, load_demo, load_sample
from utils import charts, tour, ui
from utils.geox import GEOX_VERSION
from utils.mmm import MERIDIAN_VERSION


@st.cache_data(show_spinner=False)
def _demo_numbers():
    try:
        summary = pd.read_csv(os.path.join(DEMO_DIR, "summary.csv"))
        with open(os.path.join(DEMO_DIR, "plan.json")) as f:
            plan = json.load(f)
        return summary[~summary.is_total].sort_values("roi", ascending=False), plan
    except Exception:
        return None, None


_MOTION = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "motion",
                       "how-it-works.html")


@st.cache_data(show_spinner=False)
def _motion_html() -> str:
    with open(_MOTION, encoding="utf-8") as f:
        return f.read()


# Three small pictures of how Meridian reasons, for people new to MMM.
def _svg(body: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 120" role="img">'
            f'<rect width="240" height="120" rx="14" fill="#F4F6FB"/>{body}</svg>')


CARRYOVER = _svg("".join(
    f'<rect x="{24 + i * 26}" y="{100 - h}" width="18" height="{h}" rx="4" fill="{"#2A78D6" if i == 0 else "#9EC5F4"}"/>'
    for i, h in enumerate([70, 52, 38, 27, 19, 13, 9, 6])
) + '<text x="24" y="20" font-size="11" fill="#475467" font-family="sans-serif">ad week</text>'
    '<text x="140" y="20" font-size="11" fill="#475467" font-family="sans-serif">weeks after</text>')

SATURATION = _svg(
    '<path d="M20 104 C 60 100, 70 40, 120 30 S 200 18, 222 16" fill="none" stroke="#1BAF7A" stroke-width="4" stroke-linecap="round"/>'
    '<circle cx="70" cy="62" r="6" fill="#fff" stroke="#1BAF7A" stroke-width="3"/>'
    '<circle cx="190" cy="19" r="6" fill="#fff" stroke="#E34948" stroke-width="3"/>'
    '<text x="78" y="80" font-size="11" fill="#475467" font-family="sans-serif">still steep</text>'
    '<text x="150" y="40" font-size="11" fill="#475467" font-family="sans-serif">saturated</text>')

BASELINE = _svg(
    '<rect x="30" y="20" width="56" height="84" rx="6" fill="#B8C2D6"/>'
    '<rect x="100" y="64" width="22" height="40" rx="5" fill="#2A78D6"/>'
    '<rect x="128" y="78" width="22" height="26" rx="5" fill="#EB6834"/>'
    '<rect x="156" y="86" width="22" height="18" rx="5" fill="#1BAF7A"/>'
    '<rect x="184" y="92" width="22" height="12" rx="5" fill="#EDA100"/>'
    '<text x="30" y="14" font-size="11" fill="#475467" font-family="sans-serif">baseline</text>'
    '<text x="100" y="56" font-size="11" fill="#475467" font-family="sans-serif">added by ads</text>')


def show_home():
    ui.version_banner()
    summary, plan = _demo_numbers()

    # ---- Hero: the promise, three ways in, and real demo numbers ------------
    tour.here("home-hero")
    with st.container(key="hero"):
        left, right = st.columns([1.2, 1], gap="large", vertical_alignment="center")
        with left:
            st.markdown('<div class="sm-kicker">Free and open source · built on Google Meridian</div>',
                        unsafe_allow_html=True)
            st.markdown("# Find out which ads really bring in your sales")
            st.markdown(
                '<p class="sm-lede"><a href="https://developers.google.com/meridian" target="_blank" rel="noopener" '
                'style="color:#FFD166">Google Meridian</a> can tell a business what each marketing channel earns and where '
                "the next dollar should go, but it normally needs a data scientist and a lot of Python. I built "
                "Simple Meridian so anyone can run a quick test, watch how Meridian works, and see what it can tell "
                "them, without writing a line of code.</p>",
                unsafe_allow_html=True,
            )
            st.markdown(f'<div class="sm-sign">{ui.logo(28)}<span><b style="color:#fff">Ali Barfi Bafghi</b>'
                        f" · creator of Simple Meridian</span></div>", unsafe_allow_html=True)
            with st.container(horizontal=True):
                if st.button("Take the 2-minute tour", type="primary", icon=":material/tour:", key="home_tour"):
                    tour.start()
                if st.button("Open the demo", icon=":material/bolt:", key="home_demo", disabled=not demo_available()):
                    with st.spinner("Opening the demo…"):
                        load_demo()
                    ui.go_to("step2")
                if st.button("Use my data", icon=":material/upload_file:", key="home_upload"):
                    st.session_state.data = None
                    ui.go_to("step1")
        with right:
            _demo_preview(summary, plan)

    # ---- Motion graphic: the whole idea in 16 seconds ------------------------
    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)
    st.markdown("## Watch it in 16 seconds")
    st.markdown('<p class="sm-lede" style="margin-top:-.2rem">From weekly ad spend to a better budget, using the demo '
                "company's real results. Click a dot to jump to a scene.</p>", unsafe_allow_html=True)
    components.html(_motion_html(), height=400)

    # ---- How Meridian thinks -------------------------------------------------
    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)
    st.markdown("## How Meridian thinks, in three pictures")
    st.markdown('<p class="sm-lede" style="margin-top:-.2rem">No statistics needed. These three ideas are the whole '
                "trick behind a marketing mix model.</p>", unsafe_allow_html=True)
    cols = st.columns(3, gap="medium")
    ideas = [
        (CARRYOVER, "Ads keep working after they run",
         "Someone sees a TV ad today and buys next week. Meridian spreads each week's ad effect over the weeks "
         "after it."),
        (SATURATION, "More money, smaller gains",
         "The first $10K on a channel reaches new people. The tenth $10K mostly reaches the same people again."),
        (BASELINE, "Some sales happen anyway",
         "Loyal customers and the season bring sales with no ads at all. Meridian separates that baseline from "
         "what each channel added."),
    ]
    for col, (svg, title, body) in zip(cols, ideas):
        with col:
            with st.container(key=f"start-idea-{title[:4]}"):
                st.image(svg, width="stretch")
                st.markdown(f"<h4>{title}</h4><p>{body}</p>", unsafe_allow_html=True)

    # ---- What you can do -----------------------------------------------------
    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)
    st.markdown("## What you can do here")
    features = [
        ("database", "blue", "Fit a model", "Upload weekly spend and sales; columns are detected for you.", "step1", None),
        ("bar_chart", "violet", "See what each $1 returns", "ROI per channel with an honest uncertainty range.",
         "step2", None),
        ("savings", "teal", "Plan a better budget", "Same total, moved to where the next dollar earns most.",
         "step3", None),
        ("science", "rose", "GeoX (Lift test)", f"Design and measure a geo experiment with Meridian GeoX "
                                                f"{GEOX_VERSION or ''}, then feed it back into the model.", "geox", "NEW"),
        ("description", "amber", "Share the results", "Download Meridian's HTML reports, Excel tables and the model.",
         "step2", None),
    ]
    cols = st.columns(5, gap="small")
    for col, (ic, accent, title, body, page, tag) in zip(cols, features):
        with col:
            with st.container(key=f"start-feat-{page}-{ic}"):
                badge = f'<span class="sm-new">{tag}</span>' if tag else ""
                st.markdown(f'{ui.badge(ic, accent, 40)}<h4>{badge}{title}</h4><p>{body}</p>', unsafe_allow_html=True)
                if st.button("Open", key=f"feat_{page}_{ic}", icon=":material/arrow_forward:", type="tertiary"):
                    if page in ("step2", "step3") and st.session_state.get("mmm") is None and demo_available():
                        load_demo()
                    ui.go_to(page)

    # ---- About ---------------------------------------------------------------
    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1.3, 1], gap="large")
    with c1:
        st.markdown("## About the demo company")
        st.markdown(
            "The demo is a made-up online retailer with three years of weekly data (Jan 2022 – Dec 2024): sales, "
            "spend and impressions on six channels (TV, Radio, Display, Search, Social, Email), plus an industry "
            "trend and a discount flag. A model is already fitted on it, so the tour and the demo open instantly. "
            "You can also fit it yourself from **Data & model** in about a minute."
        )
        with st.expander("Preview the demo data", icon=":material/table_view:"):
            from app_pages.common import SAMPLE_PATH
            st.dataframe(pd.read_csv(SAMPLE_PATH).head(8), hide_index=True)
        if st.button("Load the sample data and fit it myself", icon=":material/science:", key="home_sample"):
            load_sample()
            ui.go_to("step1")
    with c2:
        st.markdown("## Version history")
        st.markdown(
            f"""
            <div class="sm-tile" style="margin-bottom:.6rem">{ui.badge("new_releases", "green", 36)}<div>
              <div style="font-weight:700">27 Oct 2026 · Meridian {MERIDIAN_VERSION or "2.1.0"}</div>
              <div class="d" style="font-size:.88rem">Guided tour, demo model, GeoX (Lift test), new design,
              budget scenarios, smaller Docker image.</div></div></div>
            <div class="sm-tile">{ui.badge("history", "blue", 36)}<div>
              <div style="font-weight:700">April 2025 · Meridian 1.0.6</div>
              <div class="d" style="font-size:.88rem">First release: upload, fit, Meridian charts, budget optimizer.</div>
            </div></div>
            """,
            unsafe_allow_html=True,
        )


def _demo_preview(summary, plan):
    """Glass card with the demo's real results: ROI per channel and the budget-plan gain."""
    if summary is None:
        return
    colors = charts.color_map(pd.read_csv(os.path.join(DEMO_DIR, "summary.csv")).query("~is_total").channel)
    top = summary.roi.max()
    bars = "".join(
        f'<div style="display:flex;align-items:center;gap:.6rem;margin:.32rem 0">'
        f'<span style="width:62px;color:#DCE3F1;font-size:.86rem">{r.channel}</span>'
        f'<span style="flex:1;background:rgba(255,255,255,.08);border-radius:6px;height:14px">'
        f'<span style="display:block;width:{r.roi / top * 100:.0f}%;height:14px;border-radius:6px;'
        f'background:{colors[r.channel]}"></span></span>'
        f'<span style="width:52px;text-align:right;color:#fff;font-weight:700;font-size:.9rem">${r.roi:.2f}</span></div>'
        for r in summary.itertuples()
    )
    gain = plan["outcome_after"] - plan["outcome_before"]
    pct = gain / plan["outcome_before"] * 100
    st.markdown(
        '<div style="background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.14);border-radius:18px;'
        'padding:1.1rem 1.3rem 1rem">'
        '<div style="color:#FFD166;font-weight:700;font-size:.82rem;letter-spacing:.04em">DEMO RESULT · REVENUE PER $1</div>'
        f'{bars}'
        '<div style="border-top:1px solid rgba(255,255,255,.12);margin-top:.7rem;padding-top:.7rem;display:flex;'
        'gap:.8rem;align-items:center">'
        f'{ui.icon("savings", 26, "#86EFAC")}<div style="color:#fff;font-size:.95rem">Same budget, better split: '
        f'<b style="color:#86EFAC">+{ui.money(gain)} (+{pct:.1f}%)</b> revenue over the last year</div></div></div>',
        unsafe_allow_html=True,
    )
