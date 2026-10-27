import pandas as pd
import streamlit as st

from app_pages.common import SAMPLE_PATH, demo_available, load_demo, load_sample
from utils import ui
from utils.mmm import MERIDIAN_VERSION

LEARN = [
    ("workspace_premium", "#FFD166", "Which channel returns the most for each $1"),
    ("donut_large", "#7DD3FC", "How much revenue each channel actually drove"),
    ("show_chart", "#86EFAC", "Where extra spend stops paying back"),
    ("savings", "#F9A8D4", "How to split the same budget for more revenue"),
]


def show_home():
    ui.version_banner()

    with st.container(key="hero"):
        left, right = st.columns([1.25, 1], gap="large", vertical_alignment="center")
        with left:
            st.markdown('<div class="sm-kicker">Google Meridian, made simple</div>', unsafe_allow_html=True)
            st.markdown("# Run a real marketing mix model in a few clicks")
            st.markdown(
                '<p class="sm-lede">Google Meridian is one of the best open-source tools for measuring marketing, '
                "but running it takes notebooks, Python and a lot of setup. I built Simple Meridian so anyone can "
                "run a quick test, see how Meridian works, and find out what it can tell them about their "
                "marketing, without writing code.</p>",
                unsafe_allow_html=True,
            )
            st.markdown(f'<div class="sm-sign">{ui.logo(28)}<span><b style="color:#fff">Ali Barfi Bafghi</b>'
                        f" · creator of Simple Meridian</span></div>", unsafe_allow_html=True)
            ui.pills([("verified", f"google-meridian {MERIDIAN_VERSION or '—'}"),
                      ("lock", "Runs on your machine"), ("code_off", "No code")])
        with right:
            rows = "".join(
                f'<div style="display:flex;gap:.8rem;align-items:center;padding:.7rem 0;'
                f'border-top:1px solid rgba(255,255,255,.1)">{ui.icon(ic, 24, color)}'
                f'<span style="color:#fff;font-size:1rem">{text}</span></div>'
                for ic, color, text in LEARN
            )
            st.markdown(
                '<div style="background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.14);'
                'border-radius:18px;padding:1.1rem 1.3rem .6rem">'
                '<div style="color:#FFD166;font-weight:700;font-size:.85rem;margin-bottom:.4rem">'
                "WHAT ONE TEST TELLS YOU</div>" + rows + "</div>",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)
    st.markdown("## Start here: pick one")
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        with st.container(key="start-demo"):
            ui.start_card_header(
                "bolt", "green", "See the demo results",
                "Open a model already fitted on the sample data and go straight to ROI, curves and the budget plan.",
                ["Sample data", "Pre-fitted model"], hot="Instant",
            )
            if st.button("Open demo results", type="primary", icon=":material/bolt:", width="stretch",
                         disabled=not demo_available(), key="home_demo"):
                with st.spinner("Opening the demo model…"):
                    load_demo()
                ui.go_to("step2")
    with c2:
        with st.container(key="start-sample"):
            ui.start_card_header(
                "science", "violet", "Fit the sample data yourself",
                "Load the sample dataset, see how its columns are mapped to channels, and fit Meridian on your machine.",
                ["About a minute", "See every step"],
            )
            if st.button("Start with sample data", icon=":material/play_arrow:", width="stretch", key="home_sample"):
                load_sample()
                ui.go_to("step1")
    with c3:
        with st.container(key="start-upload"):
            ui.start_card_header(
                "upload_file", "blue", "Use your own data",
                "Upload weekly spend and sales. Date, outcome and channel columns are detected for you.",
                ["CSV or Excel", "One row per week"],
            )
            if st.button("Upload my data", icon=":material/upload:", width="stretch", key="home_upload"):
                st.session_state.data = None
                ui.go_to("step1")

    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)
    left, right = st.columns([1, 1], gap="large")
    with left:
        st.markdown("## How it works")
        for n, (ic, accent, title, body) in enumerate([
            ("database", "blue", "Data & model",
             "Confirm which columns are dates, revenue, spend and impressions, then fit Meridian."),
            ("insights", "violet", "Insights",
             "ROI per channel with uncertainty, revenue contribution, response curves and model fit."),
            ("savings", "teal", "Budget plan",
             "Meridian moves money toward channels whose next dollar earns the most, within your limits."),
        ], start=1):
            st.markdown(
                f'<div class="sm-tile" style="margin-bottom:.7rem">{ui.badge(ic, accent)}<div>'
                f'<div class="k">Step {n}</div><div style="font-weight:700;font-size:1.05rem">{title}</div>'
                f'<div class="d" style="font-size:.9rem">{body}</div></div></div>',
                unsafe_allow_html=True,
            )
    with right:
        st.markdown("## About the sample data")
        df = pd.read_csv(SAMPLE_PATH)
        dates = pd.to_datetime(df["time"], format="%m/%d/%y")
        ui.tiles([
            dict(label="Weeks", value=f"{len(df)}", detail=f"{dates.min():%b %Y} – {dates.max():%b %Y}",
                 icon="calendar_month", accent="amber"),
            dict(label="Paid channels", value="6", detail="TV, Radio, Display, Search, Social, Email",
                 icon="campaign", accent="rose"),
        ])
        st.markdown(
            '<p style="color:var(--muted);font-size:.93rem;margin-top:-.4rem">A synthetic dataset: weekly '
            "<b>Sales</b>, spend and impressions for each channel, plus two controls (industry trend and "
            "discount). It is made up, so use it to learn the app, not to judge real channels.</p>",
            unsafe_allow_html=True,
        )
        with st.expander("Preview the first rows", icon=":material/table_view:"):
            st.dataframe(df.head(8), hide_index=True)
