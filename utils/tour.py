"""Guided tour: a card at the top of each page that explains it in plain words."""
from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from utils import ui

_DEMO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "demo")


def _demo_facts() -> dict:
    """Real numbers from the demo model, so the tour text matches the charts."""
    try:
        s = pd.read_csv(os.path.join(_DEMO_DIR, "summary.csv"))
        ch = s[~s.is_total].sort_values("roi", ascending=False)
        return {"best": ch.iloc[0].channel, "best_roi": ch.iloc[0].roi,
                "worst": ch.iloc[-1].channel, "worst_roi": ch.iloc[-1].roi, "n": len(ch)}
    except Exception:
        return {"best": "Email", "best_roi": 10.6, "worst": "Display", "worst_roi": 1.6, "n": 6}


def steps() -> list[dict]:
    f = _demo_facts()
    return [
        dict(page="home", icon="waving_hand", title="Welcome! Here is what this app does",
             body="Every business that advertises asks the same question: <b>which ads actually bring in sales, and "
                  "where should the next dollar go?</b> Google built a free tool called <b>Meridian</b> that answers "
                  "it with statistics. This tour shows you the answers on a demo company that advertises on "
                  f"{f['n']} channels. It takes about two minutes, and there is nothing to type.",
             next_label="Start with the demo company"),
        dict(page="step1", icon="table_view", title="Step 1: the data",
             body="Everything starts with one simple table: one row per week, with what the company spent on each "
                  "channel (TV, Radio, Search…) and what it sold. Click <b>Preview data</b> to see it. The four boxes "
                  "below say how well the model fits. <b>0.97</b> means it explains 97% of the ups and downs in "
                  "weekly sales, which is very good.",
             highlight='[data-testid="stExpander"] summary'),
        dict(page="step2", icon="bar_chart", title="Step 2: what each $1 brought back",
             body=f"Each bar is a channel's <b>ROI</b>: the sales it brought back for every $1 spent. "
                  f"<b>{f['best']}</b> returned about <b>${f['best_roi']:.2f}</b>; <b>{f['worst']}</b> about "
                  f"<b>${f['worst_roi']:.2f}</b>. Bars to the right of the red dashed line paid for themselves. "
                  "The thin line through each bar shows how sure the model is: longer means less sure."),
        dict(page="step2", icon="donut_large", title="Where the sales came from",
             body="Click the <b>Contribution</b> tab. The donut splits all sales into <b>Baseline</b> (sales that "
                  "would happen with no ads at all: loyal customers, brand, season) and the extra each channel "
                  "added on top.",
             highlight='[data-testid="stTab"]:nth-child(2)'),
        dict(page="step2", icon="show_chart", title="When more money stops helping",
             body="Click the <b>Response curves</b> tab. Each curve shows what happens to sales if you spend more or "
                  "less on one channel. The ringed dot is what was actually spent. <b>Steep</b> means extra budget "
                  "still pays; <b>flat</b> means the channel is saturated.",
             highlight='[data-testid="stTab"]:nth-child(3)'),
        dict(page="step3", icon="savings", title="Step 3: a better budget",
             body="Press <b>Optimize budget</b>. Meridian keeps the same total and moves money from saturated "
                  "channels to ones that still pay back, never changing any channel by more than ±30%. "
                  "Blue bars mean spend more, red bars mean spend less.",
             highlight='[data-testid="stFormSubmitButton"] button'),
        dict(page="geox", icon="science", title="New: check it with a real experiment",
             body="A model learns from history, so it can be fooled. A <b>lift test</b> is an experiment: run ads in "
                  "some regions, keep them off in similar ones, and measure the gap. Press <b>Pick test regions</b>, "
                  "then <b>Run the test and measure</b>. GeoX has to find a number we hid in the data.",
             highlight='.st-key-gx_design_btn button, .st-key-gx_run_btn button'),
        dict(page="step1", icon="rocket_launch", title="You're ready for your own data",
             body="Click <b>Change data</b>, then upload a spreadsheet with one row per week: a date, your sales, and "
                  "spend for each channel. The app finds the columns for you. Stuck on a word? Open "
                  "<b>Help &amp; glossary</b> in the sidebar.",
             next_label="Finish the tour"),
    ]


def start():
    st.session_state.tour = 0
    ui.go_to("home")


def end():
    st.session_state.tour = None
    st.rerun()


def _go(i: int):
    from app_pages.common import demo_available, has_model, load_demo

    all_steps = steps()
    if i >= len(all_steps):
        st.session_state.tour = None
        st.rerun()
    st.session_state.tour = i
    if all_steps[i]["page"] != "home" and not has_model() and demo_available():
        load_demo()
    ui.go_to(all_steps[i]["page"])


def card(page: str):
    """Render the tour card if the tour is running. Call once per page, near the top."""
    i = st.session_state.get("tour")
    if i is None:
        return
    all_steps = steps()
    step = all_steps[i]
    dots = "".join(f'<span class="{"on" if j <= i else ""}"></span>' for j in range(len(all_steps)))
    with st.container(key="tour"):
        if step["page"] != page:
            st.markdown(f'<div class="sm-tour-top">{ui.icon("tour", 18)} Guided tour paused · step {i + 1} of '
                        f'{len(all_steps)} is on another page</div>', unsafe_allow_html=True)
            with st.container(horizontal=True):
                if st.button("Back to the tour", type="primary", icon=":material/play_arrow:", key="tour_resume"):
                    _go(i)
                if st.button("End tour", key="tour_end_p", type="tertiary"):
                    end()
            return
        if step.get("highlight"):
            # Pulse whatever the step asks the visitor to click.
            st.html(f"<style>{step['highlight']} {{ animation: sm-pulse 1.6s ease-in-out infinite; "
                    "position: relative; z-index: 1; }}</style>")
        st.markdown(
            f'<div class="sm-tour-top">{ui.icon("tour", 18)} Guided tour · step {i + 1} of {len(all_steps)}'
            f'<span class="sm-dots">{dots}</span></div>'
            f'<div class="sm-tour-body">{ui.badge(step["icon"], "violet", 46)}<div><h3>{step["title"]}</h3>'
            f'<p>{step["body"]}</p></div></div>',
            unsafe_allow_html=True,
        )
        with st.container(horizontal=True):
            if i > 0 and st.button("Back", icon=":material/arrow_back:", key="tour_back"):
                _go(i - 1)
            if st.button(step.get("next_label", "Next"), type="primary", icon=":material/arrow_forward:",
                         key="tour_next"):
                _go(i + 1)
            if st.button("End tour", key="tour_end", type="tertiary"):
                end()
