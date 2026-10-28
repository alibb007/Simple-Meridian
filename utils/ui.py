"""Shared look and feel: CSS, brand mark, sidebar navigation, small components."""
from __future__ import annotations

import base64
import functools
import html
import os

import streamlit as st

# Design tokens. Charts in utils/charts.py read the same values.
NAVY = "#0B1B3F"
NAVY_2 = "#132A5C"
BG = "#F4F6FB"
SURFACE = "#FFFFFF"
INK = "#101828"
MUTED = "#5B6475"
BORDER = "#E2E7F0"
GRID = "#EDF0F6"
PRIMARY = "#2459E8"
GOOD = "#0E9F6E"
BAD = "#D92D20"

# Channel palette: fixed order, one color per channel everywhere in the app.
PALETTE = ["#2A78D6", "#EB6834", "#1BAF7A", "#EDA100", "#E87BA4", "#008300", "#6250D6", "#E34948"]

# Accent colors for icon badges (not data).
ACCENTS = {
    "blue": ("#E8EFFE", "#2459E8"),
    "violet": ("#F0EBFE", "#6941C6"),
    "teal": ("#E3F7F3", "#0E8A78"),
    "amber": ("#FEF4E2", "#B54708"),
    "rose": ("#FDECEF", "#C01048"),
    "green": ("#E6F6EE", "#067647"),
}

FONT_DISPLAY = "'Red Hat Display', 'Segoe UI', system-ui, sans-serif"
FONT_BODY = "'Red Hat Text', 'Segoe UI', system-ui, -apple-system, sans-serif"
FONT_MONO = "'Red Hat Mono', ui-monospace, Menlo, monospace"

STEPS = [
    ("step1", "Data & model", ":material/database:", "Upload weekly data and fit Meridian"),
    ("step2", "Insights", ":material/insights:", "ROI, contribution, saturation"),
    ("step3", "Budget plan", ":material/savings:", "Reallocate spend for more return"),
]
TOUR_URL = "https://alibb007.github.io/simple-meridian-demo/"
EXTRA = [
    ("report", "Meridian charts", ":material/description:", "Every chart from Meridian's report, explained"),
    ("geox", "GeoX (Lift test)", ":material/science:", "Design and measure a geo experiment with Meridian GeoX"),
    ("help", "Help & glossary", ":material/help:", "Every term in plain words"),
    ("legal", "Privacy & terms", ":material/shield:", "How your data is handled, licenses, disclaimer"),
]


_PIC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pic")
_LOGO_PATH = os.path.join(_PIC, "Logo.png")
_AVATAR_PATH = os.path.join(_PIC, "ali.png")


@functools.lru_cache(maxsize=1)
def _logo_b64() -> str:
    with open(_LOGO_PATH, "rb") as f:
        return base64.b64encode(f.read()).decode()


@functools.lru_cache(maxsize=1)
def _avatar_b64() -> str:
    with open(_AVATAR_PATH, "rb") as f:
        return base64.b64encode(f.read()).decode()


def avatar(size: int = 36) -> str:
    """Ali's photo (from his LinkedIn profile), round."""
    return (f'<img class="sm-avatar" src="data:image/png;base64,{_avatar_b64()}" alt="Ali Barfi Bafghi" '
            f'width="{size}" height="{size}">')


def logo(size: int = 36) -> str:
    """Simple Meridian logo on a white tile (reads on the navy sidebar too)."""
    return (f'<span class="sm-logo" style="width:{size}px;height:{size}px">'
            f'<img src="data:image/png;base64,{_logo_b64()}" alt="Simple Meridian logo"></span>')


def icon(name: str, size: int = 20, color: str | None = None) -> str:
    style = f"font-size:{size}px;" + (f"color:{color};" if color else "")
    return f'<span class="msr" style="{style}" aria-hidden="true">{name}</span>'


def badge(name: str, accent: str = "blue", size: int = 40) -> str:
    bg, fg = ACCENTS[accent]
    return (f'<span class="sm-badge" style="width:{size}px;height:{size}px;background:{bg};color:{fg}">'
            f'{icon(name, int(size * 0.55))}</span>')


CSS = f"""
<style>
/* Fonts are served by the app itself (static/fonts, OFL-1.1), so the browser makes no outside requests. */
@font-face {{ font-family: 'Red Hat Display'; font-style: normal; font-weight: 500; font-display: swap; src: url('app/static/fonts/red-hat-display-latin-500-normal.woff2') format('woff2'); }}
@font-face {{ font-family: 'Red Hat Display'; font-style: normal; font-weight: 600; font-display: swap; src: url('app/static/fonts/red-hat-display-latin-600-normal.woff2') format('woff2'); }}
@font-face {{ font-family: 'Red Hat Display'; font-style: normal; font-weight: 700; font-display: swap; src: url('app/static/fonts/red-hat-display-latin-700-normal.woff2') format('woff2'); }}
@font-face {{ font-family: 'Red Hat Display'; font-style: normal; font-weight: 800; font-display: swap; src: url('app/static/fonts/red-hat-display-latin-800-normal.woff2') format('woff2'); }}
@font-face {{ font-family: 'Red Hat Text'; font-style: normal; font-weight: 400; font-display: swap; src: url('app/static/fonts/red-hat-text-latin-400-normal.woff2') format('woff2'); }}
@font-face {{ font-family: 'Red Hat Text'; font-style: normal; font-weight: 500; font-display: swap; src: url('app/static/fonts/red-hat-text-latin-500-normal.woff2') format('woff2'); }}
@font-face {{ font-family: 'Red Hat Text'; font-style: normal; font-weight: 600; font-display: swap; src: url('app/static/fonts/red-hat-text-latin-600-normal.woff2') format('woff2'); }}
@font-face {{ font-family: 'Red Hat Mono'; font-style: normal; font-weight: 400; font-display: swap; src: url('app/static/fonts/red-hat-mono-latin-400-normal.woff2') format('woff2'); }}
@font-face {{ font-family: 'Red Hat Mono'; font-style: normal; font-weight: 500; font-display: swap; src: url('app/static/fonts/red-hat-mono-latin-500-normal.woff2') format('woff2'); }}

:root {{
  --navy: {NAVY}; --bg: {BG}; --surface: {SURFACE}; --ink: {INK}; --muted: {MUTED};
  --border: {BORDER}; --primary: {PRIMARY}; --good: {GOOD}; --bad: {BAD};
  --display: {FONT_DISPLAY}; --body: {FONT_BODY}; --mono: {FONT_MONO};
  --shadow: 0 1px 2px rgba(16,24,40,.05), 0 1px 3px rgba(16,24,40,.06);
  --shadow-lg: 0 12px 32px -12px rgba(16,24,40,.18);
}}
html, body, [data-testid="stAppViewContainer"], .stMarkdown, p, li, label, input, textarea, button, [data-baseweb] {{
  font-family: var(--body);
}}
[data-testid="stAppViewContainer"] {{ background: var(--bg); }}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stMainBlockContainer"] {{ max-width: 1360px; padding-top: 1.6rem; padding-bottom: 2.5rem; }}
.sm-logo {{ display:inline-flex; align-items:center; justify-content:center; background:#fff; border-radius: 10px; flex:none; box-shadow: 0 1px 2px rgba(0,0,0,.15); }}
.sm-logo img {{ width: 82%; height: 82%; object-fit: contain; }}
h1, h2, h3, h4 {{ font-family: var(--display) !important; color: var(--ink); letter-spacing: -0.01em; }}
h1 {{ font-weight: 800 !important; font-size: 2.3rem !important; line-height: 1.1 !important; }}
h2 {{ font-weight: 700 !important; font-size: 1.45rem !important; }}
h3 {{ font-weight: 700 !important; font-size: 1.12rem !important; }}
.msr {{ font-family: 'Material Symbols Rounded'; font-weight: normal; font-style: normal; line-height: 1;
        display: inline-block; vertical-align: middle; font-feature-settings: 'liga'; -webkit-font-smoothing: antialiased; }}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {{ background: linear-gradient(180deg, {NAVY} 0%, {NAVY_2} 100%); border-right: 0; }}
[data-testid="stSidebar"] * {{ color: #DCE3F1; }}
[data-testid="stSidebarUserContent"] {{ padding-top: 1.1rem; }}
.sm-brand {{ display:flex; align-items:center; gap:.7rem; margin: 0 0 1.6rem; }}
.sm-brand b {{ font-family: var(--display); font-size: 1.12rem; font-weight: 800; color: #fff !important; display:block; }}
.sm-brand span {{ font-size: .75rem; color: #93A3C4 !important; }}
.sm-label {{ font-size: .72rem; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: #8193B8 !important; margin: 1rem 0 .4rem .2rem; }}
[data-testid="stSidebar"] .stButton button {{
  justify-content: flex-start !important; background: transparent !important; border: 0 !important;
  box-shadow: none !important; border-radius: 10px !important; padding: .55rem .75rem !important; min-height: 0 !important;
}}
[data-testid="stSidebar"] .stButton button div, [data-testid="stSidebar"] .stButton button span {{ justify-content: flex-start !important; }}
[data-testid="stSidebar"] .stButton button > div {{ width: 100%; }}
[data-testid="stSidebar"] .stButton button p {{ font-weight: 500; font-size: .95rem; text-align: left; color: #DCE3F1 !important; }}
[data-testid="stSidebar"] .stButton button:hover {{ background: rgba(255,255,255,.07) !important; }}
[data-testid="stSidebar"] .stButton button:focus-visible {{ outline: 2px solid #8AB4FF !important; }}
[data-testid="stSidebar"] [class*="st-key-nav-here"] .stButton button {{ background: rgba(255,255,255,.12) !important; box-shadow: inset 3px 0 0 #FFD166 !important; }}
[data-testid="stSidebar"] [class*="st-key-nav-here"] .stButton button p {{ color: #fff !important; font-weight: 600 !important; }}
[data-testid="stSidebar"] [class*="st-key-nav-done"] .stButton button [data-testid="stIconMaterial"] {{ color: #34D399 !important; }}
[data-testid="stSidebar"] [class*="st-key-nav-todo"] .stButton button p {{ color: #A9B6D3 !important; }}

.sm-status {{ margin-top: 1.4rem; padding: .9rem 1rem; border-radius: 12px; background: rgba(255,255,255,.06); font-size: .8rem; line-height: 1.55; }}
.sm-status div {{ display:flex; gap:.55rem; align-items:flex-start; margin: .35rem 0; }}
.sm-status b {{ color: #fff !important; font-weight: 600; }}
.sm-status small {{ color: #93A3C4 !important; font-size: .76rem; }}

/* ---------- Page furniture ---------- */
.sm-head {{ display:flex; gap: 1rem; align-items: center; margin-bottom: .2rem; }}
.sm-head h1 {{ margin: 0 !important; padding: 0 !important; }}
.sm-kicker {{ font-size: .85rem; font-weight: 600; color: var(--primary); margin-bottom: .15rem; }}
.sm-lede {{ font-size: 1.04rem; color: var(--muted); max-width: 70ch; margin: .5rem 0 1.4rem; }}
.sm-badge {{ display:inline-flex; align-items:center; justify-content:center; border-radius: 12px; flex: none; }}
.sm-steps {{ display:flex; gap:.35rem; margin: .2rem 0 1.4rem; }}
.sm-steps span {{ height: 5px; flex: 1; border-radius: 99px; background: var(--border); }}
.sm-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 1.25rem 1.3rem; box-shadow: var(--shadow); height: 100%; }}
.sm-card h4 {{ margin: .8rem 0 .35rem; font-size: 1.02rem; }}
.sm-card p, .sm-card li {{ color: var(--muted); font-size: .93rem; margin-bottom: .2rem; }}
.sm-callout {{ display:flex; gap:.8rem; align-items:flex-start; background: #EEF3FF; border: 1px solid #D5E0FD; color: #1D3A8A; border-radius: 14px; padding: .85rem 1rem; margin: .2rem 0 1.2rem; font-size: .95rem; }}
.sm-callout .msr {{ color: var(--primary); margin-top: 1px; }}

.sm-tiles {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: .9rem; margin: .4rem 0 1.3rem; }}
.sm-tile {{ background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 1rem 1.1rem; box-shadow: var(--shadow); display:flex; gap:.85rem; align-items:flex-start; }}
.sm-tile .k {{ font-size: .82rem; font-weight: 500; color: var(--muted); }}
.sm-tile .v {{ font-family: var(--display); font-weight: 800; font-size: 1.6rem; color: var(--ink); margin-top: .1rem; line-height: 1.15; font-variant-numeric: tabular-nums; }}
.sm-tile .d {{ font-size: .8rem; color: var(--muted); margin-top: .3rem; }}
.sm-chip {{ display:inline-flex; align-items:center; gap:.2rem; font-weight: 600; font-size: .78rem; padding: .08rem .45rem; border-radius: 99px; }}
.sm-chip.up {{ background: #E6F6EE; color: #067647; }}
.sm-chip.down {{ background: #FDECEC; color: #B42318; }}

.sm-pill {{ display:inline-flex; align-items:center; gap:.35rem; font-size: .8rem; font-weight: 500; padding: .28rem .7rem; border-radius: 999px; background: var(--surface); border: 1px solid var(--border); color: var(--muted); margin: 0 .4rem .4rem 0; }}
.sm-legend {{ display:flex; flex-wrap:wrap; gap:.4rem .9rem; font-size:.85rem; color: var(--muted); margin:.2rem 0 .6rem; }}
.sm-legend span {{ display:inline-flex; align-items:center; gap:.4rem; }}
.sm-legend i {{ width:10px; height:10px; border-radius:3px; display:inline-block; }}

/* ---------- Version banner ---------- */
.sm-version {{ display:flex; flex-wrap:wrap; align-items:center; gap:.5rem .9rem; background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; padding: .6rem .9rem; margin-bottom: 1rem; box-shadow: var(--shadow); font-size: .9rem; color: var(--muted); }}
.sm-version .tag {{ background: linear-gradient(135deg, #0E9F6E, #14B8A6); color: #fff; font-weight: 700; font-size: .75rem;
  border-radius: 99px; padding: .15rem .6rem; }}
.sm-version b {{ color: var(--ink); }}
.sm-version .sep {{ width: 1px; height: 18px; background: var(--border); }}

/* ---------- Start cards (a button inside a bordered card) ---------- */
[class*="st-key-start-"] {{ background: var(--surface); border: 1px solid var(--border) !important; border-radius: 18px !important;
  padding: 1.2rem 1.25rem 1.1rem !important; box-shadow: var(--shadow); height: 100%; transition: box-shadow .15s, transform .15s; }}
[class*="st-key-start-"]:hover {{ box-shadow: var(--shadow-lg); transform: translateY(-1px); }}
[class*="st-key-start-"] h4 {{ margin: .7rem 0 .25rem !important; font-size: 1.1rem !important; }}
[class*="st-key-start-"] p {{ color: var(--muted); font-size: .93rem; margin: 0 0 .4rem; }}
.sm-meta {{ display:flex; flex-wrap:wrap; gap:.35rem; margin: .2rem 0 .6rem; }}
.sm-meta span {{ font-size: .75rem; font-weight: 600; padding: .15rem .55rem; border-radius: 99px; background: #F2F4F7; color: #344054; }}
.sm-meta span.hot {{ background: #E6F6EE; color: #067647; }}

.st-key-runcard {{ position: sticky; top: 4rem; background: var(--surface); box-shadow: var(--shadow-lg); border-radius: 18px !important; }}
[data-testid="stVerticalBlockBorderWrapper"], [data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"][class*="st-key-"] {{ border-radius: 16px; }}

/* ---------- NEW badge ---------- */
.sm-new {{ display:inline-block; background: linear-gradient(135deg, #F04438, #F79009); color:#fff !important; font-weight:800;
  font-size:.68rem; letter-spacing:.06em; padding:.12rem .45rem; border-radius: 6px; margin-right:.35rem; vertical-align: 1px; }}
[data-testid="stSidebar"] [class*="st-key-nav-"][class*="-geox"] .stButton button p::after {{
  content: "NEW"; margin-left: .5rem; background: linear-gradient(135deg, #F04438, #F79009); color:#fff; font-weight:800;
  font-size:.62rem; letter-spacing:.06em; padding:.1rem .4rem; border-radius: 5px; vertical-align: 2px; }}
[data-testid="stSidebar"] .sm-tourlink {{ display:flex; align-items:center; gap:.5rem; margin-top:.8rem; padding:.55rem .75rem;
  border-radius:10px; color:#FFD166 !important; font-weight:600; font-size:.88rem; text-decoration:none; border:1px solid rgba(255,209,102,.35); }}
[data-testid="stSidebar"] .sm-tourlink:hover {{ background: rgba(255,209,102,.08); }}

.sm-explain {{ display:grid; grid-template-columns: 1fr 1fr; gap: .4rem 1.4rem; margin: .7rem 0 .4rem; }}
.sm-explain p {{ margin: 0; color: #344054; font-size: .95rem; line-height: 1.5; }}
@media (max-width: 900px) {{ .sm-explain {{ grid-template-columns: 1fr; }} }}
[class*="st-key-mr-"] {{ background: var(--surface); margin-bottom: .6rem; }}

/* ---------- Step 1 ---------- */
.sm-stepbar {{ display:flex; flex-wrap:wrap; gap:.4rem; margin: -.4rem 0 1.2rem; }}
.sm-step {{ display:inline-flex; align-items:center; gap:.45rem; font-size:.85rem; font-weight:600; color: var(--muted);
  background: var(--surface); border: 1px solid var(--border); border-radius: 99px; padding: .25rem .8rem .25rem .3rem; }}
.sm-step b {{ display:inline-flex; width:22px; height:22px; border-radius:50%; align-items:center; justify-content:center;
  background:#F2F4F7; color:#475467; font-size:.75rem; }}
.sm-step.on {{ color: var(--ink); border-color: #C7D7FE; }}
.sm-step.on b {{ background: var(--primary); color:#fff; }}
.sm-sec {{ display:flex; align-items:center; gap:.65rem; margin: 1.1rem 0 .15rem; }}
.sm-sec-n {{ display:inline-flex; width:30px; height:30px; border-radius:9px; align-items:center; justify-content:center;
  background:#EEF3FF; color: var(--primary); font-weight:800; font-size:.92rem; }}
.sm-sec-t {{ font-family: var(--display); font-weight: 700; font-size: 1.15rem; color: var(--ink); }}
.sm-sec-h {{ color: var(--muted); font-size: .9rem; margin: 0 0 .55rem 2.6rem; }}
[class*="st-key-chcard-"] {{ background: var(--surface); border-radius: 14px !important; box-shadow: var(--shadow);
  transition: box-shadow .15s, border-color .15s; }}
[class*="st-key-chcard-"]:hover {{ box-shadow: var(--shadow-lg); border-color: #C7D7FE !important; }}
[class*="st-key-chcard-"] [data-testid="stTextInput"] input {{ font-weight: 700; font-size: 1rem; }}
.sm-chfoot {{ display:flex; align-items:center; gap:.45rem; font-size:.82rem; color: var(--muted); }}
.sm-chfoot i {{ width:10px; height:10px; border-radius:3px; display:inline-block; }}
[class*="st-key-s1-"]:not(.st-key-s1-channels), [class*="st-key-s3-"], .st-key-runcard, .st-key-gx-plan {{ background: var(--surface); }}
.st-key-s1-channels {{ padding: .2rem 0 !important; }}
.sm-avatar {{ border-radius: 50%; object-fit: cover; box-shadow: 0 0 0 2px rgba(255,255,255,.7); flex: none; }}

/* Cards in a row: same height, action at the bottom. */
[data-testid="stHorizontalBlock"]:has([class*="st-key-start-"]) {{ align-items: stretch !important; }}
[data-testid="stHorizontalBlock"]:has([class*="st-key-start-"]) > [data-testid="stColumn"] > [data-testid="stVerticalBlock"],
[data-testid="stLayoutWrapper"]:has(> [class*="st-key-start-"]) {{ height: 100%; }}
[class*="st-key-start-"] {{ display: flex !important; flex-direction: column; }}
[class*="st-key-start-"] > [data-testid="stElementContainer"]:last-child,
[class*="st-key-start-"] > [data-testid="stLayoutWrapper"]:last-child {{ margin-top: auto; }}
.sm-cardtop {{ display:flex; justify-content: space-between; align-items: flex-start; }}

/* ---------- Hero ---------- */
.st-key-hero {{
  background: radial-gradient(1200px 400px at 85% -10%, rgba(109,74,232,.55), transparent 60%),
              radial-gradient(800px 380px at 10% 120%, rgba(20,184,166,.35), transparent 60%),
              linear-gradient(135deg, {NAVY} 0%, #15306B 100%);
  border-radius: 22px; padding: 2rem 2.2rem 1.8rem !important; box-shadow: var(--shadow-lg);
}}
.st-key-hero h1, .st-key-hero p, .st-key-hero li {{ color: #fff !important; }}
.st-key-hero h1 {{ font-size: 2.5rem !important; }}
.st-key-hero .sm-sign {{ display:flex; align-items:center; gap:.6rem; color:#C9D4EC; font-size:.88rem; margin:.2rem 0 1rem; }}
.st-key-hero .sm-lede {{ color: #C9D4EC !important; }}
.st-key-hero .sm-kicker {{ color: #FFD166; }}
.st-key-hero .sm-pill {{ background: rgba(255,255,255,.08); border-color: rgba(255,255,255,.16); color: #DCE3F1; }}
.st-key-hero [data-testid="stBaseButton-secondary"] {{ background: rgba(255,255,255,.1) !important; border-color: rgba(255,255,255,.28) !important; }}
.st-key-hero [data-testid="stBaseButton-secondary"] p, .st-key-hero [data-testid="stBaseButton-secondary"] span {{ color: #fff !important; }}
.st-key-hero [data-testid="stBaseButton-primary"] {{ background: #FFD166 !important; border-color: #FFD166 !important; }}
.st-key-hero [data-testid="stBaseButton-primary"] p, .st-key-hero [data-testid="stBaseButton-primary"] span {{ color: {NAVY} !important; font-weight: 700; }}

/* ---------- Widgets ---------- */
.stButton button, .stDownloadButton button, .stFormSubmitButton button {{ border-radius: 10px; font-weight: 600; }}
[data-testid="stBaseButton-primary"] {{ background: var(--primary) !important; border-color: var(--primary) !important; box-shadow: 0 1px 2px rgba(36,89,232,.3); }}
[data-testid="stBaseButton-primary"]:hover {{ background: #1C47C4 !important; }}
[data-testid="stBaseButton-primary"] p, [data-testid="stBaseButton-primary"] span {{ color: #fff !important; }}
/* Tabs as a segmented pill bar; the active tab is filled. */
[data-testid="stTabs"] [role="tablist"] {{ gap: .3rem; background: var(--surface); border: 1px solid var(--border); border-radius: 14px;
  padding: .3rem; box-shadow: var(--shadow); width: fit-content; max-width: 100%; flex-wrap: wrap; height: auto; }}
[data-testid="stTabs"] [role="tablist"]::before, [data-testid="stTabs"] [role="tablist"]::after,
[data-testid="stTab"]::before, [data-testid="stTab"]::after {{ display: none !important; }}
[data-testid="stTab"] {{ font-weight: 600; padding: .5rem 1rem !important; border-radius: 10px !important; color: var(--muted) !important;
  background: transparent; border: 0 !important; box-shadow: none !important; height: auto !important; transition: background .15s, color .15s; }}
[data-testid="stTab"] p, [data-testid="stTab"] span {{ color: inherit !important; font-weight: 600; }}
[data-testid="stTab"]:hover {{ background: #EEF3FF; color: var(--primary) !important; }}
[data-testid="stTab"][aria-selected="true"] {{ background: linear-gradient(135deg, #2459E8, #5B4BDB) !important; color: #fff !important;
  box-shadow: 0 4px 12px -4px rgba(36,89,232,.55) !important; }}
[data-testid="stTab"]:focus-visible {{ outline: 2px solid #8AB4FF; outline-offset: 2px; }}
[data-testid="stTabPanel"] {{ padding-top: 1rem; }}
[data-testid="stFileUploaderDropzone"] {{ background: var(--surface); border: 2px dashed #C6D2EA; border-radius: 16px; padding: 1.6rem; }}
[data-testid="stExpander"] details {{ background: var(--surface); border-radius: 14px; border-color: var(--border); box-shadow: var(--shadow); }}
[data-testid="stPlotlyChart"] {{ background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: .6rem .4rem .2rem; box-shadow: var(--shadow); }}
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {{ border-radius: 12px; overflow: hidden; }}

.sm-footer {{ margin-top: 3rem; padding-top: 1.1rem; border-top: 1px solid var(--border); font-size: .83rem; color: var(--muted); display:flex; flex-wrap: wrap; gap: .5rem 1.2rem; justify-content: space-between; align-items:center; }}
.sm-footer a {{ color: var(--ink); text-decoration: none; font-weight: 500; display:inline-flex; align-items:center; gap:.25rem; }}
.sm-footer a:hover {{ color: var(--primary); }}

@media (max-width: 640px) {{
  h1, .st-key-hero h1 {{ font-size: 1.9rem !important; }}
  .st-key-hero {{ padding: 1.5rem 1.2rem !important; }}
}}
@media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; animation: none !important; }} }}
</style>
"""


def inject_css():
    st.html(CSS)


def page_header(step: int, title: str, lede: str | None = None, icon_name: str = "database", accent: str = "blue"):
    bars = "".join(f'<span style="background:{PRIMARY if i <= step else BORDER}"></span>' for i in range(1, 4))
    st.markdown(
        f'<div class="sm-head">{badge(icon_name, accent, 52)}<div>'
        f'<div class="sm-kicker">Step {step} of 3</div><h1>{html.escape(title)}</h1></div></div>'
        f'<div class="sm-steps" style="max-width:260px;margin-top:.9rem">{bars}</div>',
        unsafe_allow_html=True,
    )
    if lede:
        st.markdown(f'<p class="sm-lede">{lede}</p>', unsafe_allow_html=True)


def start_card_header(icon_name: str, accent: str, title: str, body: str, meta: list[str], hot: str | None = None):
    chips = (f'<span class="hot">{html.escape(hot)}</span>' if hot else "") + "".join(
        f"<span>{html.escape(m)}</span>" for m in meta)
    st.markdown(f'{badge(icon_name, accent, 44)}<h4>{html.escape(title)}</h4><p>{body}</p>'
                f'<div class="sm-meta">{chips}</div>', unsafe_allow_html=True)


def callout(text: str, icon_name: str = "lightbulb"):
    st.markdown(f'<div class="sm-callout">{icon(icon_name, 22)}<div>{text}</div></div>', unsafe_allow_html=True)


def card(title: str, body_html: str, icon_name: str | None = None, accent: str = "blue"):
    top = badge(icon_name, accent) if icon_name else ""
    st.markdown(f'<div class="sm-card">{top}<h4>{html.escape(title)}</h4>{body_html}</div>', unsafe_allow_html=True)


def tiles(items: list[dict]):
    """items: dicts with label, value, and optional detail, chip, direction ('up'/'down'), icon, accent."""
    out = []
    for it in items:
        chip = ""
        if it.get("chip"):
            arrow = "arrow_upward" if it.get("direction") == "up" else "arrow_downward"
            chip = (f'<span class="sm-chip {html.escape(it.get("direction", ""))}">{icon(arrow, 14)}'
                    f'{html.escape(str(it["chip"]))}</span> ')
        # Values can come from uploaded files (channel names), so escape everything.
        detail = f'<div class="d">{chip}{html.escape(str(it.get("detail", "")))}</div>' if (chip or it.get("detail")) else ""
        b = badge(it["icon"], it.get("accent", "blue")) if it.get("icon") else ""
        out.append(f'<div class="sm-tile">{b}<div><div class="k">{html.escape(str(it["label"]))}</div>'
                   f'<div class="v">{html.escape(str(it["value"]))}</div>{detail}</div></div>')
    st.markdown(f'<div class="sm-tiles">{"".join(out)}</div>', unsafe_allow_html=True)


def pills(items: list[tuple[str, str]]):
    """items: (icon name, text)."""
    st.markdown("".join(f'<span class="sm-pill">{icon(i, 16)}{html.escape(t)}</span>' for i, t in items),
                unsafe_allow_html=True)


def legend(colors: dict[str, str]):
    st.markdown('<div class="sm-legend">' + "".join(
        f'<span><i style="background:{c}"></i>{html.escape(n)}</span>' for n, c in colors.items()) + "</div>",
        unsafe_allow_html=True)


def go_to(page: str):
    st.session_state.page = page
    st.rerun()


def step_state(page: str) -> str:
    if page == st.session_state.get("page"):
        return "here"
    done = {
        "step1": st.session_state.get("mmm") is not None,
        "step2": st.session_state.get("visited_insights", False) and st.session_state.get("mmm") is not None,
        "step3": st.session_state.get("optimization") is not None,
    }
    return "done" if done.get(page) else "todo"


def sidebar(meridian_version: str | None):
    with st.sidebar:
        st.markdown(f'<div class="sm-brand">{logo(40)}<div><b>Simple Meridian</b>'
                    f'<span>Google Meridian, made simple</span></div></div>', unsafe_allow_html=True)
        st.markdown('<div class="sm-label">Workflow</div>', unsafe_allow_html=True)
        for page, label, ic, desc in STEPS:
            state = step_state(page)
            with st.container(key=f"nav-{state}-{page}"):
                if st.button(label, key=f"btn_{page}", help=desc, width="stretch",
                             icon=":material/check_circle:" if state == "done" else ic):
                    go_to(page)
        st.markdown('<div class="sm-label">More</div>', unsafe_allow_html=True)
        for page, label, ic, desc in EXTRA:
            here = "here" if st.session_state.get("page") == page else "todo"
            with st.container(key=f"nav-{here}-{page}"):
                if st.button(label, key=f"btn_{page}", help=desc, width="stretch", icon=ic):
                    go_to(page)

        data = st.session_state.get("data")
        info = st.session_state.get("model_info")
        rows = []
        if data is not None:
            name = html.escape(st.session_state.get("data_name") or "uploaded data")
            rows.append(f'<div>{icon("table_chart", 18, "#60A5FA")}<span><b>{name}</b><br>'
                        f'<small>{len(data):,} rows · {data.shape[1]} columns</small></span></div>')
        else:
            rows.append(f'<div>{icon("table_chart", 18, "#5B6E96")}<small>No data loaded</small></div>')
        if info:
            r2 = info.get("r2")
            r2s = f" · R² {r2:.2f}" if r2 is not None else ""
            rows.append(f'<div>{icon("model_training", 18, "#34D399")}<span><b>Model ready</b><br>'
                        f'<small>{html.escape(info.get("source", ""))}{r2s}</small></span></div>')
        else:
            rows.append(f'<div>{icon("model_training", 18, "#5B6E96")}<small>No model yet</small></div>')
        cal = st.session_state.get("calibration") or {}
        if cal:
            rows.append(f'<div>{icon("tune", 18, "#C4B5FD")}<span><b>GeoX priors</b><br>'
                        f'<small>{html.escape(", ".join(cal))}</small></span></div>')
        rows.append(f'<div>{icon("verified", 18, "#FFD166" if meridian_version else "#F87171")}'
                    f'<small>google-meridian {meridian_version or "not installed"}</small></div>')
        st.markdown(f'<div class="sm-status">{"".join(rows)}</div>', unsafe_allow_html=True)
        st.markdown(f'<a class="sm-tourlink" href="{TOUR_URL}" target="_blank" rel="noopener noreferrer">'
                    f'{icon("play_circle", 18)}New to this? Watch the guided tour</a>', unsafe_allow_html=True)


def footer():
    st.markdown(
        f"""
        <div class="sm-footer">
          <span>Built by Ali Barfi Bafghi on the open-source
          <a href="https://developers.google.com/meridian" target="_blank" rel="noopener">Google Meridian</a> and
          <a href="https://developers.google.com/meridian/geox" target="_blank" rel="noopener">Meridian GeoX</a> libraries.
          Not affiliated with or endorsed by Google. Results are statistical estimates, not financial advice.</span>
          <span style="display:flex;gap:1rem;flex-wrap:wrap">
            <a href="https://developers.google.com/meridian" target="_blank" rel="noopener">{icon("open_in_new", 17)}Meridian docs</a>
            <a href="https://github.com/alibb007/Simple-Meridian" target="_blank" rel="noopener">{icon("code", 17)}GitHub</a>
            <a href="https://www.linkedin.com/in/alibarfibafghi/" target="_blank" rel="noopener">{icon("person", 17)}LinkedIn</a>
            <a href="mailto:ali.barfib@gmail.com">{icon("mail", 17)}Email</a>
          </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def money(x: float, decimals: int = 1) -> str:
    """$1.2M / $3.4B / $560K."""
    if x is None:
        return "–"
    sign = "-" if x < 0 else ""
    a = abs(x)
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if a >= div:
            return f"{sign}${a / div:,.{decimals}f}{suf}"
    return f"{sign}${a:,.0f}"
