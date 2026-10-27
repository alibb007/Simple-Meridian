import streamlit as st

from app_pages.common import load_sample
from utils import ui
from utils.mmm import MERIDIAN_VERSION

# Four channel response curves on the dark hero: each flattens at a different
# point, which is the whole idea of the app. Dots mark current spend.
_CURVES = [
    ("TV", ui.PALETTE[0], "M30 250 C 90 238, 130 120, 220 92 S 380 62, 470 56", (250, 84)),
    ("Search", ui.PALETTE[1], "M30 250 C 70 220, 110 150, 180 128 S 330 108, 470 104", (330, 110)),
    ("Social", ui.PALETTE[2], "M30 250 C 120 246, 190 170, 270 150 S 420 136, 470 134", (180, 186)),
    ("Email", ui.PALETTE[3], "M30 250 C 60 200, 90 182, 150 176 S 330 170, 470 168", (390, 169)),
]


def _hero_svg() -> str:
    grid = "".join(f'<line x1="30" x2="470" y1="{y}" y2="{y}" stroke="#ffffff" stroke-opacity=".08"/>' for y in range(50, 260, 40))
    paths, dots, legend = [], [], []
    for i, (name, color, d, (cx, cy)) in enumerate(_CURVES):
        paths.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="3.2" stroke-linecap="round"/>')
        dots.append(f'<circle cx="{cx}" cy="{cy}" r="6.5" fill="#0B1B3F" stroke="{color}" stroke-width="3"/>')
        x = 34 + i * 92
        legend.append(f'<rect x="{x}" y="282" width="10" height="10" rx="3" fill="{color}"/>'
                      f'<text x="{x + 16}" y="291" fill="#C9D4EC" font-size="12" font-family="Red Hat Text, sans-serif">{name}</text>')
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 310" role="img"
     aria-label="Response curves for four channels, each flattening at a different spend level">
  <rect x="0" y="0" width="500" height="310" rx="18" fill="#ffffff" fill-opacity=".06" stroke="#ffffff" stroke-opacity=".12"/>
  <text x="30" y="32" fill="#ffffff" font-size="14" font-weight="700" font-family="Red Hat Display, sans-serif">Response curves</text>
  <text x="470" y="32" fill="#93A3C4" font-size="12" text-anchor="end" font-family="Red Hat Text, sans-serif">incremental revenue vs. spend</text>
  {grid}
  <line x1="30" x2="470" y1="250" y2="250" stroke="#ffffff" stroke-opacity=".25"/>
  {''.join(paths)}{''.join(dots)}{''.join(legend)}
</svg>"""


def show_home():
    with st.container(key="hero"):
        left, right = st.columns([1.05, 1], gap="large", vertical_alignment="center")
        with left:
            st.markdown('<div class="sm-kicker">Marketing mix modeling, no code</div>', unsafe_allow_html=True)
            st.markdown("# See which channels drive revenue, and where to spend next")
            st.markdown(
                '<p class="sm-lede">Upload weekly spend and sales. Simple Meridian fits Google\'s Bayesian '
                "Meridian model, measures ROI and saturation for every channel, and builds a better split "
                "of your budget.</p>",
                unsafe_allow_html=True,
            )
            with st.container(horizontal=True):
                if st.button("Try the sample data", type="primary", icon=":material/play_circle:"):
                    load_sample()
                    ui.go_to("step1")
                if st.button("Upload my data", icon=":material/upload_file:"):
                    ui.go_to("step1")
            ui.pills([("verified", f"google-meridian {MERIDIAN_VERSION or '—'}"),
                      ("lock", "Runs on your machine"), ("description", "CSV or Excel")])
        with right:
            st.image(_hero_svg(), width="stretch")

    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
    st.markdown("## How it works")
    cols = st.columns(3, gap="medium")
    steps = [
        ("database", "blue", "1. Data & model",
         "Pick your date, revenue and channel columns. Spend and impressions are paired for you, "
         "and Meridian is fitted locally."),
        ("insights", "violet", "2. Insights",
         "ROI with uncertainty ranges, share of revenue against share of spend, and response curves "
         "that show where returns flatten."),
        ("savings", "teal", "3. Budget plan",
         "Keep the same budget or set a new one. Money moves toward the channels whose next dollar "
         "earns the most, within limits you choose."),
    ]
    for col, (ic, accent, title, body) in zip(cols, steps):
        with col:
            ui.card(title, f"<p>{body}</p>", ic, accent)

    st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
    st.markdown("## What your data needs")
    cols = st.columns(4, gap="medium")
    needs = [
        ("calendar_month", "amber", "Weekly rows", "One row per week with no gaps. Two to three years is ideal."),
        ("payments", "green", "An outcome", "Revenue, or conversions with an optional revenue-per-conversion column."),
        ("campaign", "rose", "Channel spend", "Spend per channel, plus impressions or clicks when you have them."),
        ("tune", "blue", "Controls", "Optional: price, promotions, seasonality, market trends."),
    ]
    for col, (ic, accent, title, body) in zip(cols, needs):
        with col:
            ui.card(title, f"<p>{body}</p>", ic, accent)

    st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
    ui.callout(
        "<b>What is marketing mix modeling?</b> It estimates how much revenue each channel caused, using "
        "only weekly totals: no user tracking, no cookies. Meridian, Google's open-source MMM, accounts for "
        "carryover (an ad keeps working for weeks) and saturation (each extra dollar buys less than the last).",
        "school",
    )
