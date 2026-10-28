"""Guided tour text for the live demo site (docs/). Read by docs/build_demo_json.py.

The Streamlit app has no tour of its own; it links to the site instead. Step
anchors match the data-t regions of the simulated screens in docs/assets/site.js.
"""
from __future__ import annotations

import json
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

_DEMO_DIR = os.path.join(ROOT, "data", "demo")


def _demo_facts() -> dict:
    """Real numbers from the demo model, so the tour text matches the charts."""
    try:
        s = pd.read_csv(os.path.join(_DEMO_DIR, "summary.csv"))
        ch = s[~s.is_total].sort_values("roi", ascending=False)
        with open(os.path.join(_DEMO_DIR, "quality.json")) as fh:
            q = json.load(fh)
        return {"best": ch.iloc[0].channel, "best_roi": ch.iloc[0].roi,
                "worst": ch.iloc[-1].channel, "worst_roi": ch.iloc[-1].roi, "n": len(ch),
                "r2": q["r2"], "mape": q["mape"]}
    except Exception:
        return {"best": "Email", "best_roi": 10.6, "worst": "Display", "worst_roi": 1.6, "n": 6, "r2": 0.97, "mape": 0.038}


def steps() -> list[dict]:
    from utils.report_charts import MODEL_CHARTS, PLAN_CHARTS

    f = _demo_facts()
    out = [
        dict(chapter="Welcome", page="home", icon="waving_hand",
             title="Welcome! Here is what this app does",
             body="Every business that advertises asks the same question: <b>which ads really bring in sales, and "
                  "where should the next dollar go?</b> Google built a free tool called <b>Meridian</b> that answers "
                  "it with statistics. This tour shows you the answers for a made-up company that advertises on "
                  f"{f['n']} channels. You only click Next; there is nothing to type.", anchor="home-hero"),

        dict(chapter="Step 1 · Data & model", page="upload", icon="upload_file", title="Upload your data",
             body="Everything starts here. Upload a CSV or Excel file with one row per week: the date, your sales "
                  "and what you spent on each channel. No file yet? Load the sample data, or open the demo results "
                  "to look around first.",
             anchor="s1-upload"),
        dict(chapter="Step 1 · Data & model", page="step1", icon="table_view", title="Your data",
             body="This is the file you uploaded, one row per week. It says how much the company spent on each "
                  "channel (TV, Radio, Search…) and how much it sold that week. In the app, <b>Preview the "
                  "table</b> opens the rows.",
             anchor="s1-data"),
        dict(chapter="Step 1 · Data & model", page="step1", icon="event", title="Which column is the date, and which is sales",
             body="Here you tell the app which column holds the week and which number you want to grow, such as "
                  "sales. The small chart shows that number over time, so you can check it looks right before "
                  "going on.",
             anchor="s1-time"),
        dict(chapter="Step 1 · Data & model", page="step1", icon="campaign", title="Your ad channels",
             body="Each card is one place the company spends on ads. A card needs the column with that channel's "
                  "spend and, if you have it, the column with its impressions or clicks. The app found all six on "
                  "its own. You can rename a card, change its columns, add one or delete one.",
             anchor="s1-channels"),
        dict(chapter="Step 1 · Data & model", page="step1", icon="tune", title="Other things that move sales",
             body="Discounts, price changes or the season also push sales up and down. Pick those columns here, so "
                  "the model doesn't give your ads credit for a sale that a discount caused.",
             anchor="s1-controls"),
        dict(chapter="Step 1 · Data & model", page="step1", icon="rocket_launch", title="Run the model",
             body="Once every column is set, choose how long Meridian should spend learning and press <b>Run "
                  "model</b>. <b>Quick check</b> takes about 30 seconds and <b>Standard</b> about a minute.",
             anchor="s1-run"),
        dict(chapter="Step 1 · Data & model", page="ready", icon="task_alt", title="Model ready: how good is it?",
             body=f"When the run finishes, this page grades the model. <b>{f['r2']:.2f}</b> means it explains "
                  f"{f['r2'] * 100:.0f}% of the week-to-week ups and downs. <b>{f['mape'] * 100:.1f}%</b> is how "
                  "far off it is in an average week. <b>Converged</b> means it finished learning properly.",
             anchor="s1-ready"),

        dict(chapter="Step 2 · Insights", page="step2", icon="bar_chart", title="What each $1 brought back",
             body=f"Each bar is a channel's <b>ROI</b>: the sales it brought back for every $1 spent. "
                  f"<b>{f['best']}</b> returned about <b>${f['best_roi']:.2f}</b>; <b>{f['worst']}</b> about "
                  f"<b>${f['worst_roi']:.2f}</b>. Bars to the right of the red dashed line paid for themselves. "
                  "The thin line through each bar shows how sure the model is: the longer it is, the less sure.",
             anchor="s2-roi"),
    ]
    for c in MODEL_CHARTS:
        out.append(dict(chapter="Meridian's own charts", page="report", icon=c["icon"], title=c["title"],
                        body=f"{c['what']} {c['read']}", anchor=f"mr-{c['id']}"))
    out.append(dict(chapter="Step 3 · Budget plan", page="step3", icon="savings", title="A better budget",
                    body="In the app, <b>Optimize budget</b> keeps the same total and moves money from channels "
                         "that are full to ones that still pay back, never changing a channel by more than ±30%. "
                         "Blue bars mean spend more; red bars mean spend less.",
                    anchor="s3-settings"))
    for c in PLAN_CHARTS:
        out.append(dict(chapter="Budget plan charts", page="report", icon=c["icon"], title=c["title"],
                        body=f"{c['what']} {c['read']}", anchor=f"mr-{c['id']}"))
    out += [
        dict(chapter="GeoX (Lift test)", page="geox", icon="science", title="New: GeoX (Lift test), a real experiment",
             body="A model learns from the past, so it can be fooled. A <b>lift test</b> is an experiment: run ads in "
                  "some regions, keep them off in similar ones, and measure the gap. In the app, you press "
                  "<b>Pick test regions</b>, then <b>Run the test and measure</b>. GeoX has to find a number we hid in the data.",
             anchor="gx-plan"),
        dict(chapter="Your turn", page="step1", icon="rocket_launch", title="You're ready for your own data",
             body="Click <b>Change data</b>, then upload a spreadsheet with one row per week: a date, your sales and "
                  "the spend on each channel. The app finds the columns for you. Stuck on a word? Open "
                  "<b>Help &amp; glossary</b> in the sidebar.", anchor="s1-data"),
    ]
    return out
