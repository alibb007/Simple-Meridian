"""Thin service layer around Google Meridian 2.x.

Every function here takes plain Python / pandas inputs and returns plain
pandas outputs, so the Streamlit pages never touch xarray or Meridian
internals directly.
"""
from __future__ import annotations

import os
import re
import tempfile
import time
import warnings
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
# Meridian and ArviZ emit informational UserWarnings on every national fit.
warnings.filterwarnings("ignore", category=UserWarning, module=r"(meridian|arviz)(\.|$)")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

try:
    import meridian
    from meridian.analysis import analyzer, optimizer, summarizer
    from meridian.data import load
    from meridian.model import model, spec

    MERIDIAN_VERSION = meridian.__version__
except ImportError:  # pragma: no cover - surfaced in the UI
    MERIDIAN_VERSION = None

try:
    from meridian.schema.serde import meridian_serde

    SERDE_AVAILABLE = True
except ImportError:
    SERDE_AVAILABLE = False


# Sampling presets. "Standard" matches the settings the app has always used.
PRESETS = {
    "Quick check": dict(n_chains=2, n_adapt=300, n_burnin=300, n_keep=250, n_prior=250),
    "Standard": dict(n_chains=4, n_adapt=500, n_burnin=500, n_keep=500, n_prior=500),
    "Thorough": dict(n_chains=4, n_adapt=1000, n_burnin=1000, n_keep=1000, n_prior=500),
}
PRESET_NOTES = {
    "Quick check": "About 1 minute on a laptop. Good for checking your setup.",
    "Standard": "A few minutes. Use this for numbers you plan to act on.",
    "Thorough": "10+ minutes. Tighter intervals and more reliable convergence.",
}


# --------------------------------------------------------------------------- #
# Column detection
# --------------------------------------------------------------------------- #
_EXPOSURE_WORDS = ("impression", "impr", "view", "click", "grp", "trp", "exposure", "reach", "traffic", "media")
_SPEND_WORDS = ("spend", "cost", "budget", "investment", "expense")
_KPI_WORDS = ("revenue", "sales", "conversion", "kpi", "target", "outcome", "income", "orders")
_CONTROL_WORDS = (
    "control", "season", "holiday", "price", "competitor", "weather", "promo", "trend",
    "gdp", "unemployment", "cpi", "inflation", "discount", "industry", "sentiment",
    "covid", "event", "index",
)
_SUFFIX = re.compile(
    r"[_\s\-]*(impressions?|impr|views?|clicks?|grps?|trps?|exposures?|reach|traffic|media|"
    r"spend|cost|budget|investment|expense)s?$",
    re.IGNORECASE,
)


def channel_stem(column: str) -> str:
    """'TV_impression' -> 'TV', 'paid_search_spend' -> 'paid_search'."""
    stem = _SUFFIX.sub("", column).strip("_ -")
    return stem or column


def _has(col: str, words) -> bool:
    low = col.lower()
    return any(w in low for w in words)


def detect_date_columns(df: pd.DataFrame) -> list[str]:
    found = []
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            found.append(col)
            continue
        if df[col].dtype == object:
            sample = df[col].dropna().head(20)
            if len(sample) and pd.to_datetime(sample, errors="coerce", format="mixed").notna().all():
                found.append(col)
    named = [c for c in df.columns if _has(c, ("date", "time", "week", "period", "day")) and c not in found]
    return found + named


def suggest_config(df: pd.DataFrame) -> dict:
    """Best-guess column roles for a freshly uploaded dataset."""
    numeric = df.select_dtypes(include="number").columns.tolist()
    dates = detect_date_columns(df)

    kpi = next((c for c in numeric if _has(c, _KPI_WORDS)), numeric[-1] if numeric else None)

    spend_cols = [c for c in numeric if _has(c, _SPEND_WORDS) and c != kpi]
    exposure_cols = [c for c in numeric if _has(c, _EXPOSURE_WORDS) and c not in spend_cols and c != kpi]

    exposure_by_stem = {channel_stem(c).lower(): c for c in exposure_cols}
    channels = []
    for s in spend_cols:
        stem = channel_stem(s)
        exposure = exposure_by_stem.get(stem.lower())
        channels.append({"Channel": stem.replace("_", " "), "Exposure column": exposure or s, "Spend column": s})

    used = {kpi, *spend_cols, *exposure_cols}
    controls = [c for c in numeric if c not in used and _has(c, _CONTROL_WORDS)]

    return {
        "date": dates[0] if dates else None,
        "date_options": dates or df.columns.tolist(),
        "kpi": kpi,
        "numeric": numeric,
        "channels": channels,
        "controls": controls,
    }


# --------------------------------------------------------------------------- #
# Validation and data preparation
# --------------------------------------------------------------------------- #
@dataclass
class ModelConfig:
    date_col: str
    kpi_col: str
    kpi_type: str  # "revenue" | "non_revenue"
    channels: list[dict]  # [{"Channel", "Exposure column", "Spend column"}]
    controls: list[str] = field(default_factory=list)
    revenue_per_kpi_col: str | None = None
    preset: str = "Standard"
    max_lag: int = 8
    seed: int = 1


def parse_dates(series: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(series):
        return series
    return pd.to_datetime(series, errors="coerce", format="mixed")


def validate(df: pd.DataFrame, cfg: ModelConfig) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). Errors block the model run."""
    errors, notes = [], []

    dates = parse_dates(df[cfg.date_col]) if cfg.date_col in df else None
    if dates is None or dates.isna().any():
        bad = "every row" if dates is None else f"{int(dates.isna().sum())} rows"
        errors.append(f"`{cfg.date_col}` could not be read as dates in {bad}. Use a format like 2024-01-31.")
    else:
        if dates.duplicated().any():
            errors.append(f"`{cfg.date_col}` has repeated dates. This app models national data: one row per period.")
        gaps = dates.sort_values().diff().dropna().dt.days
        if len(gaps) and gaps.nunique() > 1:
            errors.append("Dates are not evenly spaced. Meridian needs one row per week (or other fixed interval) with no gaps.")
        elif len(gaps) and gaps.iloc[0] != 7:
            notes.append(f"Rows are {int(gaps.iloc[0])} days apart. Meridian is designed for weekly data.")
        if len(dates) < 52:
            notes.append(f"Only {len(dates)} periods. Two to three years of weekly data gives far more stable results.")

    rows = [r for r in cfg.channels if r.get("Channel") and r.get("Spend column")]
    if not rows:
        errors.append("Add at least one paid channel with a spend column.")
    names = [r["Channel"].strip() for r in rows]
    if len(set(names)) != len(names):
        errors.append("Channel names must be unique.")
    for r in rows:
        if not r.get("Exposure column"):
            errors.append(f"Channel **{r['Channel']}** needs an exposure column (impressions, clicks…). Use the spend column if you have nothing else.")

    used = [cfg.kpi_col] + [r["Spend column"] for r in rows] + [r["Exposure column"] for r in rows if r.get("Exposure column")] + list(cfg.controls)
    for col in dict.fromkeys(used):
        if col not in df.columns:
            errors.append(f"Column `{col}` is not in the data.")
            continue
        if not pd.api.types.is_numeric_dtype(df[col]):
            errors.append(f"`{col}` must be numeric.")
        elif df[col].isna().any():
            errors.append(f"`{col}` has {int(df[col].isna().sum())} empty cells. Fill or drop them first.")
        elif (df[col] < 0).any() and col not in cfg.controls:
            errors.append(f"`{col}` has negative values.")
    if cfg.kpi_col in cfg.controls:
        errors.append("The outcome column cannot also be a control.")
    for c in cfg.controls:
        if c in df and pd.api.types.is_numeric_dtype(df[c]) and df[c].std() == 0:
            errors.append(f"Control `{c}` never changes, so the model cannot learn from it. Remove it.")
    if cfg.kpi_type == "non_revenue" and not cfg.revenue_per_kpi_col:
        notes.append("Without a revenue-per-conversion column, ROI is reported per conversion rather than in currency.")
    return errors, notes


def prepare_frame(df: pd.DataFrame, cfg: ModelConfig) -> pd.DataFrame:
    out = df.copy()
    out[cfg.date_col] = parse_dates(out[cfg.date_col]).dt.strftime("%Y-%m-%d")
    return out.sort_values(cfg.date_col).reset_index(drop=True)


def build_input_data(df: pd.DataFrame, cfg: ModelConfig):
    rows = [r for r in cfg.channels if r.get("Channel") and r.get("Spend column")]
    frame = prepare_frame(df, cfg)

    # Meridian keys channels by column, so a channel that reuses its spend
    # column as exposure needs a separate copy.
    media_cols, spend_cols, media_map, spend_map = [], [], {}, {}
    for r in rows:
        name, exp, spd = r["Channel"].strip(), r["Exposure column"], r["Spend column"]
        if exp == spd:
            exp = f"{spd}__exposure"
            frame[exp] = frame[spd]
        media_cols.append(exp)
        spend_cols.append(spd)
        media_map[exp] = name
        spend_map[spd] = name

    coords = dict(time=cfg.date_col, kpi=cfg.kpi_col, controls=list(cfg.controls),
                  media=media_cols, media_spend=spend_cols)
    if cfg.kpi_type == "non_revenue" and cfg.revenue_per_kpi_col:
        coords["revenue_per_kpi"] = cfg.revenue_per_kpi_col

    loader = load.DataFrameDataLoader(
        df=frame,
        coord_to_columns=load.CoordToColumns(**coords),
        kpi_type=cfg.kpi_type,
        media_to_channel=media_map,
        media_spend_to_channel=spend_map,
    )
    return loader.load()


def fit(input_data, cfg: ModelConfig, on_stage=None):
    """Build and sample a Meridian model. Returns (mmm, seconds)."""
    p = PRESETS[cfg.preset]
    stage = on_stage or (lambda *_: None)
    started = time.time()

    stage("Building model")
    mmm = model.Meridian(input_data=input_data, model_spec=spec.ModelSpec(max_lag=cfg.max_lag))

    stage("Sampling prior")
    mmm.sample_prior(p["n_prior"], seed=cfg.seed)

    stage(f"Sampling posterior ({p['n_chains']} chains × {p['n_adapt'] + p['n_burnin'] + p['n_keep']} steps)")
    mmm.sample_posterior(
        n_chains=p["n_chains"], n_adapt=p["n_adapt"], n_burnin=p["n_burnin"], n_keep=p["n_keep"], seed=cfg.seed
    )
    return mmm, time.time() - started


# --------------------------------------------------------------------------- #
# Save / load
# --------------------------------------------------------------------------- #
def model_to_bytes(mmm) -> tuple[bytes, str]:
    """Serialize with Meridian's protobuf format (falls back to joblib pickle)."""
    with tempfile.TemporaryDirectory() as tmp:
        if SERDE_AVAILABLE:
            path = os.path.join(tmp, "model.binpb")
            meridian_serde.save_meridian(mmm, path)
            ext = "binpb"
        else:
            path = os.path.join(tmp, "model.pkl")
            model.save_mmm(mmm, path)
            ext = "pkl"
        with open(path, "rb") as f:
            return f.read(), ext


def model_from_bytes(data: bytes, filename: str):
    ext = os.path.splitext(filename)[1].lower()
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, f"model{ext}")
        with open(path, "wb") as f:
            f.write(data)
        if ext in (".binpb", ".txtpb", ".textproto"):
            if not SERDE_AVAILABLE:
                raise RuntimeError("Install google-meridian[schema] to open .binpb model files.")
            return meridian_serde.load_meridian(path)
        return model.load_mmm(path)


# --------------------------------------------------------------------------- #
# Analysis → tidy DataFrames
# --------------------------------------------------------------------------- #
def time_periods(mmm) -> list[str]:
    return [str(t) for t in mmm.input_data.time.values]


def channel_summary(mmm, confidence_level: float = 0.9) -> pd.DataFrame:
    sm = analyzer.Analyzer(mmm).summary_metrics(confidence_level=confidence_level, use_kpi=False)
    post = sm.sel(distribution="posterior")
    rows = []
    for ch in sm.channel.values:
        p = post.sel(channel=ch)
        rows.append({
            "channel": str(ch),
            "spend": float(sm.spend.sel(channel=ch)),
            "pct_spend": float(sm.pct_of_spend.sel(channel=ch)),
            "impressions": float(sm.impressions.sel(channel=ch)),
            "incremental": float(p.incremental_outcome.sel(metric="mean")),
            "incremental_lo": float(p.incremental_outcome.sel(metric="ci_lo")),
            "incremental_hi": float(p.incremental_outcome.sel(metric="ci_hi")),
            "pct_contribution": float(p.pct_of_contribution.sel(metric="mean")),
            "roi": float(p.roi.sel(metric="mean")),
            "roi_lo": float(p.roi.sel(metric="ci_lo")),
            "roi_hi": float(p.roi.sel(metric="ci_hi")),
            "mroi": float(p.mroi.sel(metric="mean")),
            "effectiveness": float(p.effectiveness.sel(metric="mean")),
            "cpik": float(p.cpik.sel(metric="mean")),
        })
    df = pd.DataFrame(rows)
    df["is_total"] = df["channel"] == "All Channels"
    return df


def fit_quality(mmm) -> dict:
    a = analyzer.Analyzer(mmm)
    acc = a.predictive_accuracy()["value"]
    vals = {str(m): float(acc.sel(metric=m).values.ravel()[0]) for m in acc.metric.values}
    rhat = a.get_rhat()
    # Some parameters (e.g. fixed ones) have all-NaN R-hat; skip them.
    values = np.concatenate([np.asarray(v, dtype=float).ravel() for v in rhat.values()])
    max_rhat = float(np.nanmax(values)) if np.isfinite(values).any() else float("nan")
    return {"r2": vals.get("R_Squared"), "mape": vals.get("MAPE"), "wmape": vals.get("wMAPE"), "max_rhat": max_rhat}


def fit_series(mmm, confidence_level: float = 0.9) -> pd.DataFrame:
    d = analyzer.Analyzer(mmm).expected_vs_actual_data(confidence_level=confidence_level, aggregate_geos=True)
    exp, base = d.expected, d.baseline
    return pd.DataFrame({
        "time": pd.to_datetime([str(t) for t in d.time.values]),
        "actual": np.asarray(d.actual).ravel(),
        "expected": np.asarray(exp.sel(metric="mean")).ravel(),
        "expected_lo": np.asarray(exp.sel(metric="ci_lo")).ravel(),
        "expected_hi": np.asarray(exp.sel(metric="ci_hi")).ravel(),
        "baseline": np.asarray(base.sel(metric="mean")).ravel(),
    })


def baseline_total(mmm) -> float:
    s = fit_series(mmm)
    return float(s["baseline"].sum())


def response_curves(mmm, confidence_level: float = 0.9) -> pd.DataFrame:
    rc = analyzer.Analyzer(mmm).response_curves(
        spend_multipliers=list(np.round(np.arange(0, 2.01, 0.05), 2)),
        confidence_level=confidence_level,
        use_kpi=False,
    )
    return _curves_frame(rc)


def _curves_frame(rc) -> pd.DataFrame:
    rows = []
    for ch in rc.channel.values:
        for m in rc.spend_multiplier.values:
            io = rc.incremental_outcome.sel(channel=ch, spend_multiplier=m)
            rows.append({
                "channel": str(ch),
                "multiplier": float(m),
                "spend": float(rc.spend.sel(channel=ch, spend_multiplier=m)),
                "mean": float(io.sel(metric="mean")),
                "lo": float(io.sel(metric="ci_lo")),
                "hi": float(io.sel(metric="ci_hi")),
            })
    return pd.DataFrame(rows)


def model_report_html(mmm, start_date: str, end_date: str) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        summarizer.Summarizer(mmm).output_model_results_summary(
            "report.html", tmp, start_date=start_date, end_date=end_date
        )
        with open(os.path.join(tmp, "report.html"), encoding="utf-8") as f:
            return f.read()


# --------------------------------------------------------------------------- #
# Budget optimization
# --------------------------------------------------------------------------- #
def optimize(mmm, start_date: str, end_date: str, budget: float | None, constraint_pct: float):
    """Fixed-budget optimization. `budget=None` keeps the historical budget."""
    c = constraint_pct / 100.0
    return optimizer.BudgetOptimizer(mmm).optimize(
        start_date=start_date,
        end_date=end_date,
        fixed_budget=True,
        budget=budget,
        spend_constraint_lower=c,
        spend_constraint_upper=c,
        use_kpi=False,
    )


def optimization_table(res) -> pd.DataFrame:
    before, after = res.nonoptimized_data, res.optimized_data
    df = pd.DataFrame({
        "channel": [str(c) for c in after.channel.values],
        "current_spend": before.spend.values,
        "optimized_spend": after.spend.values,
        "current_outcome": before.incremental_outcome.sel(metric="mean").values,
        "optimized_outcome": after.incremental_outcome.sel(metric="mean").values,
        "current_roi": before.roi.sel(metric="mean").values,
        "optimized_roi": after.roi.sel(metric="mean").values,
        "optimized_mroi": after.mroi.sel(metric="mean").values,
    })
    df["spend_change"] = df["optimized_spend"] - df["current_spend"]
    df["spend_change_pct"] = np.where(df["current_spend"] > 0, df["spend_change"] / df["current_spend"] * 100, 0.0)
    df["outcome_change"] = df["optimized_outcome"] - df["current_outcome"]
    return df


def optimization_totals(res) -> dict:
    b, a = res.nonoptimized_data.attrs, res.optimized_data.attrs
    return {
        "start": b.get("start_date"),
        "end": b.get("end_date"),
        "budget_before": float(b["budget"]),
        "budget_after": float(a["budget"]),
        "outcome_before": float(b["total_incremental_outcome"]),
        "outcome_after": float(a["total_incremental_outcome"]),
        "roi_before": float(b["total_roi"]),
        "roi_after": float(a["total_roi"]),
        "is_revenue": bool(b.get("is_revenue_kpi", True)),
    }


def optimization_curves(res) -> pd.DataFrame:
    return _curves_frame(res.get_response_curves())


def optimization_report_html(res) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        res.output_optimization_summary("optimization.html", tmp)
        with open(os.path.join(tmp, "optimization.html"), encoding="utf-8") as f:
            return f.read()
