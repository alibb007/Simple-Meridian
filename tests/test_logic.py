"""Checks for the data rules and helpers behind the pages (no model fit needed).

    python -m pytest tests -q        # or: python tests/test_logic.py
"""
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from utils import charts  # noqa: E402
from utils import geox as G  # noqa: E402
from utils import mmm as M  # noqa: E402

SPACING = "Dates are not evenly spaced"


def _sample_cfg(df):
    s = M.suggest_config(df)
    return M.ModelConfig(date_col=s["date"], kpi_col=s["kpi"], kpi_type="revenue",
                         channels=s["channels"], controls=s["controls"])


def _spacing_errors(df):
    errors, _ = M.validate(df, _sample_cfg(df))
    return [e for e in errors if SPACING in e]


def test_weekly_sample_passes_spacing():
    df = pd.read_csv(os.path.join(ROOT, "data", "simple_dataset.csv"))
    assert _spacing_errors(df) == []


def test_monthly_dates_pass_spacing():
    df = pd.read_csv(os.path.join(ROOT, "data", "simple_dataset.csv")).head(36).copy()
    df[_sample_cfg(df).date_col] = pd.date_range("2022-01-01", periods=36, freq="MS").strftime("%Y-%m-%d")
    errors, notes = M.validate(df, _sample_cfg(df))
    assert not [e for e in errors if SPACING in e], errors
    assert any("not weekly" in n for n in notes), notes


def test_missing_week_fails_spacing():
    df = pd.read_csv(os.path.join(ROOT, "data", "simple_dataset.csv")).drop(index=10).reset_index(drop=True)
    assert _spacing_errors(df)


def test_usable_priors_drop_non_positive():
    priors = {"TV": (2.5, 0.25), "Radio": (-0.05, 0.1), "Email": (0.0, 0.1), "Search": (1.2, 0.0), "Gone": (3.0, 0.3)}
    assert M.usable_priors(priors, ["TV", "Radio", "Email", "Search"]) == {"TV": (2.5, 0.25)}


def test_prior_from_iroas():
    assert G.prior_from_iroas(-0.05, 0.1) is None
    assert G.prior_from_iroas(0.0, 0.1) is None
    assert G.prior_from_iroas(2.5, 0.1) == (2.5, 0.25)  # sd floored at 10% of the mean
    assert G.prior_from_iroas(2.53, 0.4) == (2.53, 0.4)


def test_geo_validation_reports_bad_values():
    df = G.sample_geo_data(pre_days=10, test_days=5)
    assert G.validate_geo_data(df) == []
    bad = df.astype({"date": str, "spend": object}).copy()
    bad.loc[0, "date"] = "week 3"
    bad.loc[1, "spend"] = "$950"
    errors = G.validate_geo_data(bad)
    assert any("`date`" in e for e in errors), errors
    assert any("`spend`" in e for e in errors), errors


def test_donut_label_for_small_totals():
    summary = pd.DataFrame({"channel": ["TV", "Email", "All Channels"], "incremental": [60_000.0, 40_000.0, 100_000.0],
                            "is_total": [False, False, True]})
    fig = charts.contribution_donut(300_000.0, summary, charts.color_map(["TV", "Email"]))
    assert fig.layout.annotations[0].text.startswith("<b>$400.0K</b>"), fig.layout.annotations[0].text


if __name__ == "__main__":
    for name, t in list(globals().items()):
        if name.startswith("test_") and callable(t):
            t()
            print("ok", name)
