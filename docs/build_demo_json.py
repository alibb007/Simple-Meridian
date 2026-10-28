"""Pack the precomputed demo results (data/demo/) into docs/assets/demo.json.

Run from the repo root after `python scripts/build_demo.py`:

    python docs/build_demo_json.py
"""
import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO = os.path.join(ROOT, "data", "demo")
OUT = os.path.join(ROOT, "docs", "assets", "demo.json")


def rows(name):
    with open(os.path.join(DEMO, name), newline="") as f:
        return list(csv.DictReader(f))


def num(v):
    try:
        return round(float(v), 4)
    except (TypeError, ValueError):
        return v


summary = [{k: num(v) for k, v in r.items()} for r in rows("summary.csv")]
for r in summary:
    r["is_total"] = str(r["is_total"]).lower() == "true"
fit = [{"time": r["time"][:10], "actual": num(r["actual"]), "expected": num(r["expected"]),
        "baseline": num(r["baseline"])} for r in rows("fit_series.csv")]
curves = [{k: num(v) for k, v in r.items() if k in ("channel", "multiplier", "spend", "mean")} for r in rows("curves.csv")]
plan = [{k: num(v) for k, v in r.items() if k in ("channel", "current_spend", "optimized_spend", "spend_change_pct")}
        for r in rows("plan.csv")]
with open(os.path.join(DEMO, "plan.json")) as f:
    plan_totals = json.load(f)
with open(os.path.join(DEMO, "quality.json")) as f:
    quality = json.load(f)

with open(os.path.join(ROOT, "data", "simple_dataset.csv"), newline="") as f:
    sample = [{"week": r["time"], "TV": round(float(r["TV_spend"])), "Radio": round(float(r["Radio_spend"])),
               "Search": round(float(r["Search_spend"])), "Email": round(float(r["Email_spend"])),
               "Sales": round(float(r["Sales"]))} for _, r in zip(range(6), csv.DictReader(f))]

data = {"sample_rows": sample, "summary": summary, "fit": fit, "curves": curves, "plan": plan, "plan_totals": plan_totals,
        "quality": quality, "geox_sample": {"true_iroas": 2.5, "estimate": 2.53, "lo": 2.36, "hi": 2.67,
                                            "test_regions": 11, "control_regions": 29, "mde": 0.008}}
with open(OUT, "w") as f:
    json.dump(data, f, separators=(",", ":"))
# The same data as a script, so index.html also works when opened from disk (file://).
js = OUT[:-5] + ".js"
with open(js, "w") as f:
    f.write("window.SM_DEMO = " + json.dumps(data, separators=(",", ":")) + ";\n")
print("wrote", OUT, os.path.getsize(OUT), "bytes and", js, os.path.getsize(js), "bytes")
