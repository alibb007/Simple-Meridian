"""Run the GeoX sample exactly as the app's GeoX page does by default and save the numbers
the live demo's tour shows (data/demo/geox.json).

    .venv/bin/python scripts/build_geox_demo.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from utils import geox as G  # noqa: E402

# Same defaults as app_pages/lift_test.py: 28 days, 30% max share, $2 expected, split seed 2,
# a true return of $2.50 per $1 and campaign spend of 4% of test-region revenue.
TEST_DAYS, SHARE, EXPECTED, SEED, TRUE_IROAS, SPEND = 28, 0.3, 2.0, 2, 2.5, 0.04

df = G.sample_geo_data(pre_days=120, test_days=TEST_DAYS)
start = sorted(df["date"].unique())[120]
design, _ = G.design_test(df[df["date"] < start], TEST_DAYS, SHARE, EXPECTED, seed=SEED)
s = G.design_summary(design)
run = G.simulate_campaign(df, s["treatment"], start, TRUE_IROAS, SPEND)
r = G.analyze_test(run, design, start, run["date"].max())

cf = r["counterfactual"]
cum = r["cumulative"]
pre = df[df["date"] < start].copy()
pre["group"] = pre["location"].map(lambda g: "test" if g in s["treatment"] else ("control" if g in s["control"] else "out"))
groups = pre.groupby(["date", "group"])["conversions"].mean().unstack()
geo_size = df[df["date"] < start].groupby("location")["conversions"].mean()

out = {
    "test_days": TEST_DAYS, "true_iroas": TRUE_IROAS, "start": str(start)[:10],
    "n_geos": int(df["location"].nunique()),
    "treatment": s["treatment"], "control": s["control"], "excluded": s["excluded"],
    "mde": s["mde"], "budget": s["budget"],
    "iroas": r["iroas"], "lift": r["lift"], "pct": r["pct"],
    "geo_size": {g: round(float(v), 1) for g, v in geo_size.items()},
    "pre_groups": {"date": [str(d)[:10] for d in groups.index],
                   "test": [round(float(v), 1) for v in groups.get("test", [])],
                   "control": [round(float(v), 1) for v in groups.get("control", [])]},
    "counterfactual": json.loads(cf.to_json(orient="split", date_format="iso")),
    "cumulative": json.loads(cum.to_json(orient="split", date_format="iso")),
}
path = os.path.join(ROOT, "data", "demo", "geox.json")
with open(path, "w") as f:
    json.dump(out, f, separators=(",", ":"))
print("wrote", path, os.path.getsize(path), "bytes")
print({k: out[k] for k in ("n_geos", "mde", "budget", "iroas", "pct")}, len(out["treatment"]), len(out["control"]), out["excluded"])
print(out["counterfactual"]["columns"], len(out["counterfactual"]["data"]), out["cumulative"]["columns"])
