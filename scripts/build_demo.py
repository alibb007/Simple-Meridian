"""Rebuild the demo model and its precomputed insights.

Run after changing the sample data or upgrading google-meridian:

    python scripts/build_demo.py

Writes data/sample_model.binpb (Standard preset) and data/demo/*.csv|json,
which the app reads instead of recomputing when the demo is opened.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402

from utils import mmm as M  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "demo")


def main(refit: bool):
    os.makedirs(OUT, exist_ok=True)
    model_path = os.path.join(DATA, "sample_model.binpb")
    if refit or not os.path.exists(model_path):
        df = pd.read_csv(os.path.join(DATA, "simple_dataset.csv"))
        s = M.suggest_config(df)
        cfg = M.ModelConfig(date_col=s["date"], kpi_col=s["kpi"], kpi_type="revenue",
                            channels=s["channels"], controls=s["controls"], preset="Standard")
        mmm, secs = M.fit(M.build_input_data(df, cfg), cfg)
        print(f"fitted in {secs:.0f}s")
        data, _ = M.model_to_bytes(mmm)
        with open(model_path, "wb") as f:
            f.write(data)
    else:
        with open(model_path, "rb") as f:
            mmm = M.model_from_bytes(f.read(), model_path)

    t = time.time()
    M.channel_summary(mmm).to_csv(os.path.join(OUT, "summary.csv"), index=False)
    M.fit_series(mmm).to_csv(os.path.join(OUT, "fit_series.csv"), index=False)
    M.response_curves(mmm).to_csv(os.path.join(OUT, "curves.csv"), index=False)
    with open(os.path.join(OUT, "quality.json"), "w") as f:
        json.dump(M.fit_quality(mmm), f, indent=2)
    with open(os.path.join(OUT, "meta.json"), "w") as f:
        json.dump({"google_meridian": M.MERIDIAN_VERSION, "model_bytes": os.path.getsize(model_path)}, f, indent=2)
    print(f"insights written to {OUT} in {time.time() - t:.0f}s")


if __name__ == "__main__":
    main(refit="--refit" in sys.argv)
