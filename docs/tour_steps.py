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
                "r2": q["r2"], "mape": q["mape"], "wmape": q["wmape"]}
    except Exception:
        return {"best": "Email", "best_roi": 10.6, "worst": "Display", "worst_roi": 1.6, "n": 6, "r2": 0.97, "mape": 0.038, "wmape": 0.035}


def _geox_facts() -> dict:
    """The GeoX sample's real results (scripts/build_geox_demo.py)."""
    with open(os.path.join(_DEMO_DIR, "geox.json")) as fh:
        x = json.load(fh)
    return {"n_geos": x["n_geos"], "n_test": len(x["treatment"]), "n_control": len(x["control"]),
            "pre_days": len(x["pre_groups"]["date"]), "test_days": x["test_days"], "true": x["true_iroas"],
            "iroas": x["iroas"]["mean"], "lo": x["iroas"]["lo"], "hi": x["iroas"]["hi"], "pct": x["pct"]["mean"]}


def steps() -> list[dict]:
    from utils.report_charts import MODEL_CHARTS, PLAN_CHARTS

    f = _demo_facts()
    g = _geox_facts()
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
             body=f"When the run finishes, this page grades the model. <b>R-squared {f['r2']:.2f}</b> means it "
                  f"explains {f['r2'] * 100:.0f}% of the week-to-week ups and downs; close to 1 is good. "
                  f"<b>MAPE {f['mape'] * 100:.1f}%</b> is how far off it is in an average week, and <b>wMAPE "
                  f"{f['wmape'] * 100:.1f}%</b> is the same with big weeks counting more; under 10% is good for "
                  "weekly sales. <b>Converged</b> means it finished learning properly.",
             anchor="s1-ready"),

        dict(chapter="Step 2 · Insights", page="step2", icon="bar_chart", title="What each $1 brought back",
             body=f"Each bar is a channel's <b>ROI</b>: the sales it brought back for every $1 spent. "
                  f"<b>{f['best']}</b> returned about <b>${f['best_roi']:.2f}</b>; <b>{f['worst']}</b> about "
                  f"<b>${f['worst_roi']:.2f}</b>. Bars to the right of the red dashed line paid for themselves. "
                  "The thin line through each bar shows how sure the model is: the longer it is, the less sure.",
             anchor="s2-roi"),
    ]
    for c in MODEL_CHARTS:
        if c["id"] == "fit_table":  # its three scores are on the Model ready step
            continue
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
        dict(chapter="GeoX (Lift test)", page="geox", icon="science", title="Why run a lift test?",
             body="Meridian learns from the past, so it can mix up cause and effect. If TV spend went up in the same "
                  "weeks that sales rose for another reason, TV gets the credit. A <b>lift test</b> settles it with a "
                  "real experiment: run the ads in some regions, keep them off in similar ones, and compare.",
             anchor="gx-why"),
        dict(chapter="GeoX (Lift test)", page="geox", icon="map", title="1. Pick the test regions",
             body=f"GeoX looks at {g['pre_days']} days of daily sales in {g['n_geos']} made-up regions and picks "
                  f"<b>{g['n_test']} test regions</b> whose sales move like the other <b>{g['n_control']}</b>. "
                  "On the chart the two groups move together before the test, so a gap later comes from the ads.",
             anchor="gx-plan"),
        dict(chapter="GeoX (Lift test)", page="geox", icon="campaign", title=f"2. Run the ads for {g['test_days']} days",
             body=f"The campaign runs only in the {g['n_test']} test regions. GeoX uses the control regions to work "
                  "out what the test regions would have sold without it (the dashed line). The gap between the "
                  "two lines is the extra sales the ads brought in.",
             anchor="gx-run"),
        dict(chapter="GeoX (Lift test)", page="geox", icon="verified", title="3. Read the result",
             body=f"GeoX measured <b>${g['iroas']:.2f}</b> back for every $1, with a 90% range of "
                  f"${g['lo']:.2f} to ${g['hi']:.2f}. We hid the true value, <b>${g['true']:.2f}</b>, in the "
                  f"made-up data, and it sits inside that range. Sales in the test regions were {g['pct'] * 100:.1f}% higher than they would have been without the ads.",
             anchor="gx-result"),
        dict(chapter="GeoX (Lift test)", page="geox", icon="tune", title="4. Teach the model",
             body=f"A test result can become Meridian's starting belief for that channel. Used for TV in the demo, "
                  "it narrowed TV's likely ROI from <b>$1.42–$3.86</b> to <b>$2.23–$2.95</b>, so the budget plan "
                  "works from a firmer number for TV.",
             anchor="gx-prior"),
        dict(chapter="Your turn", page="step1", icon="rocket_launch", title="You're ready for your own data",
             body="Click <b>Change data</b>, then upload a spreadsheet with one row per week: a date, your sales and "
                  "the spend on each channel. The app finds the columns for you. Stuck on a word? Open "
                  "<b>Help &amp; glossary</b> in the sidebar.", anchor="s1-data"),
    ]
    return out
