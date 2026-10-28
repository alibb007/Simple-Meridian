"""Thin service layer around Meridian GeoX (geo lift tests).

A lift test turns a campaign on in some regions (treatment) and keeps it off
in others (control). GeoX picks well-matched groups, then measures how far
treatment revenue rose above what the control regions predict. Its iROAS
(incremental revenue per $1, "ICPD" in GeoX) can be fed into Meridian as an
ROI prior for that channel.
"""
from __future__ import annotations

import datetime as dt
from importlib import metadata

import numpy as np
import pandas as pd

try:
    GEOX_VERSION = metadata.version("meridian-geox")
except metadata.PackageNotFoundError:
    GEOX_VERSION = None


def _gx():
    import jax
    import meridian_geox as gx  # imports JAX; keep it off the page-load path

    # Meridian switches JAX to 64-bit floats when it loads, and GeoX's region
    # search gives different splits in 32- vs 64-bit. Pin 64-bit so results
    # don't depend on whether Meridian happened to load first.
    jax.config.update("jax_enable_x64", True)
    return gx


# --------------------------------------------------------------------------- #
# Sample data
# --------------------------------------------------------------------------- #
def sample_geo_data(n_geo: int = 40, pre_days: int = 120, test_days: int = 28, seed: int = 7) -> pd.DataFrame:
    """Daily revenue for `n_geo` regions with weekly and yearly seasonality and no campaign yet."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2025-01-01", periods=pre_days + test_days, freq="D")
    t = np.arange(len(dates))
    season = 1 + 0.15 * np.sin(t / 7 * 2 * np.pi) + 0.1 * np.sin(t / 365 * 2 * np.pi)
    size = rng.lognormal(10, 0.6, n_geo)
    frames = []
    for g in range(n_geo):
        revenue = size[g] * season * (1 + rng.normal(0, 0.05, len(dates)))
        frames.append(pd.DataFrame({"date": dates, "location": f"Region {g + 1:02d}",
                                    "conversions": revenue, "spend": 0.0}))
    return pd.concat(frames, ignore_index=True)


def simulate_campaign(df: pd.DataFrame, treatment_geos, start, true_iroas: float,
                      spend_pct: float = 0.04, seed: int = 11) -> pd.DataFrame:
    """Run a pretend campaign: treatment regions get spend from `start`, and revenue rises by true_iroas x spend."""
    rng = np.random.default_rng(seed)
    out = df.copy()
    mask = (out["date"] >= pd.Timestamp(start)) & out["location"].isin(set(treatment_geos))
    spend = out.loc[mask, "conversions"].to_numpy() * spend_pct * rng.uniform(0.8, 1.2, mask.sum())
    out.loc[mask, "spend"] = spend
    out.loc[mask, "conversions"] += true_iroas * spend
    return out


# --------------------------------------------------------------------------- #
# Design and analysis
# --------------------------------------------------------------------------- #
def design_test(pre_df: pd.DataFrame, test_days: int, max_share: float = 0.3, expected_iroas: float = 2.0,
                seed: int = 42):
    """Pick treatment and control regions. Returns (Design, metrics DataFrame of the top options)."""
    gx = _gx()
    cfg = gx.DesignConfig(
        experiment_duration=dt.timedelta(days=int(test_days)),
        experiment_types=gx.ExperimentType.HOLDBACK,
        n_candidates=4096, n_ranked_candidates=32, design_output_count=3,
        cost_per_incremental_conversion=1.0 / max(expected_iroas, 1e-6), seed=seed,
    )
    ds = gx.run_design(pre_df, cfg, gx.Constraints(max_conversions_percent=max_share))
    best = ds.design_metrics.iloc[0]["design_id"]
    return ds.designs[best], ds.design_metrics


def manual_design(df: pd.DataFrame, treatment_geos, start, test_days: int):
    """A Design for a test someone already ran with their own choice of regions.

    GeoX checks the result against placebo tests drawn from the pre-test data,
    so that data is attached. Random placebo assignment is used because the
    regions were not picked by GeoX's stratified search.
    """
    gx = _gx()
    from meridian_geox.api import PerCellDesign
    treatment = set(treatment_geos)
    control = set(df["location"].unique()) - treatment
    cfg = gx.DesignConfig(experiment_duration=dt.timedelta(days=int(test_days)),
                          experiment_types=gx.ExperimentType.HOLDBACK,
                          geo_assignment_rule=gx.GeoAssignmentRule.RANDOM)
    cell = PerCellDesign(treatment_geos=treatment, minimum_detectable_effect=0.0, design_implied_cpic=0.0,
                         p_value=1.0, budget=0.0)
    return gx.Design(designs={"cell_1": cell}, control_geos=control, excluded_geos=set(),
                     design_config=cfg, constraints=gx.Constraints(),
                     data=df[df["date"] < pd.Timestamp(start)].copy())


def design_summary(design) -> dict:
    cell = design.designs["cell_1"]
    return {
        "treatment": sorted(cell.treatment_geos),
        "control": sorted(design.control_geos),
        "excluded": sorted(design.excluded_geos),
        "mde": float(cell.minimum_detectable_effect),
        "budget": float(cell.budget),
    }


def analyze_test(df: pd.DataFrame, design, start, end) -> dict:
    gx = _gx()
    res = gx.analyze(df, gx.AnalysisConfig(design=design, analysis_start_date=pd.Timestamp(start),
                                           analysis_end_date=pd.Timestamp(end),
                                           n_placebo_candidates=4096, n_top_placebos=256))
    m = res.results["cell_1"]

    def est(e):
        return None if e is None else {"mean": float(e.point_estimate), "lo": float(e.lower_bound),
                                       "hi": float(e.upper_bound), "sd": float(e.standard_deviation),
                                       "p": float(e.p_value)}

    return {
        "lift": est(m.lift),
        "pct": est(m.percent_lift),
        "iroas": est(m.icpd),
        "counterfactual": m.counterfactual_conversions.reset_index(),
        "cumulative": m.cumulative_lift.reset_index(),
        "excluded_geos": sorted(res.excluded_geos),
        "spend": float(df.loc[(df["date"] >= pd.Timestamp(start)) & (df["date"] <= pd.Timestamp(end))
                              & df["location"].isin(design.designs["cell_1"].treatment_geos), "spend"].sum()),
    }


def validate_geo_data(df: pd.DataFrame) -> list[str]:
    errors = []
    need = {"date", "location", "conversions", "spend"}
    missing = need - set(c.lower() for c in df.columns)
    if missing:
        errors.append("Missing columns: " + ", ".join(sorted(missing)) + ". Expected date, location, conversions, spend.")
        return errors
    if df["location"].nunique() < 10:
        errors.append("GeoX needs at least 10 regions to build matched groups.")
    return errors


def prior_from_iroas(mean: float, sd: float) -> tuple[float, float]:
    """Lift-test estimate -> (mean, sd) for an ROI prior. The sd is floored at 10% of the mean."""
    return float(mean), float(max(sd, 0.1 * abs(mean)))
