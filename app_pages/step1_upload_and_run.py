import time

import pandas as pd
import streamlit as st

from app_pages.common import (
    has_model, load_sample, model_download_button, model_loader, read_upload, set_data, set_model,
)
from utils import mmm as M
from utils import ui


def show_upload_and_run():
    ui.page_header(1, "Data & model", "Tell the model which columns hold dates, revenue and spend. Then fit it.",
                   "database", "blue")

    if st.session_state.data is None:
        _upload_panel()
        return

    df = st.session_state.data
    _data_summary(df)

    if has_model():
        _model_ready()
        with st.expander("Change settings and fit again", icon=":material/settings:"):
            _configure_and_fit(df)
    else:
        _configure_and_fit(df)


# --------------------------------------------------------------------------- #
def _upload_panel():
    c1, c2 = st.columns([1.3, 1], gap="large")
    with c1:
        file = st.file_uploader("Upload weekly marketing data", type=["csv", "xlsx", "xls"])
        if file is not None:
            try:
                df = read_upload(file)
            except Exception as e:
                st.error(f"Could not read {file.name}: {e}")
                return
            set_data(df, file.name)
            st.rerun()
        st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
        if st.button("Use the sample dataset instead", icon=":material/table_view:"):
            load_sample()
            st.rerun()
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        with st.expander("Already fitted a model? Open it", icon=":material/folder_open:"):
            model_loader("loader_step1")
            if has_model():
                ui.go_to("step2")
    with c2:
        ui.card(
            "Expected format",
            """
            <p>One row per week, one column per measure. For example:</p>
            <table style="font-size:.82rem;width:100%;border-collapse:collapse;margin:.5rem 0 .7rem;font-variant-numeric:tabular-nums">
              <tr style="color:var(--ink);font-weight:600;border-bottom:1px solid var(--border)"><td>week</td><td>tv_spend</td><td>tv_impr</td><td>sales</td></tr>
              <tr><td>2024-01-07</td><td>81,200</td><td>9.1M</td><td>612,400</td></tr>
              <tr><td>2024-01-14</td><td>77,950</td><td>8.7M</td><td>598,100</td></tr>
            </table>
            <p>Columns named like <code>*_spend</code> and <code>*_impression</code> are paired automatically.
            Dates can be in any common format.</p>
            """,
            "table_view",
            "teal",
        )


def _data_summary(df: pd.DataFrame):
    suggestion = M.suggest_config(df)
    date_col = st.session_state.get("cfg_date", suggestion["date"])
    dates = M.parse_dates(df[date_col]) if date_col in df else None
    span = ""
    if dates is not None and dates.notna().all():
        span = f"{dates.min():%d %b %Y} → {dates.max():%d %b %Y}"

    c1, c2 = st.columns([4, 1], vertical_alignment="center")
    with c1:
        ui.pills([("description", st.session_state.data_name or "data"), ("table_rows", f"{len(df):,} rows"),
                  ("view_column", f"{df.shape[1]} columns")] + ([("date_range", span)] if span else []))
    with c2:
        if st.button("Replace data", icon=":material/swap_horiz:", width="stretch"):
            st.session_state.data = None
            st.session_state.data_name = None
            st.rerun()
    with st.expander("Preview data", icon=":material/table_view:"):
        st.dataframe(df.head(50), hide_index=True, height=260)


def _model_ready():
    info = st.session_state.model_info or {}
    r2 = info.get("r2")
    rhat = info.get("max_rhat")
    mape = info.get("mape")
    elapsed = info.get("elapsed")
    st.markdown("### :material/task_alt: Model ready")
    ok = (rhat or 0) < 1.2
    ui.tiles([
        dict(label="Fit (R²)", value=f"{r2:.2f}" if r2 is not None else "–", icon="target", accent="blue",
             detail="share of weekly variation explained"),
        dict(label="Error (MAPE)", value=f"{mape * 100:.1f}%" if mape is not None else "–", icon="straighten",
             accent="violet", detail="average miss per week"),
        dict(label="Convergence (R-hat)", value=f"{rhat:.2f}" if rhat is not None else "–",
             icon="check_circle" if ok else "error", accent="green" if ok else "rose",
             chip="Converged" if ok else "Fit again", direction="up" if ok else "down"),
        dict(label="Fit time", value=f"{elapsed / 60:.1f} min" if elapsed else "Loaded", icon="timer", accent="amber",
             detail=info.get("preset") or info.get("source", "")),
    ])
    c1, c2, _ = st.columns([1, 1, 2])
    with c1:
        if st.button("See insights", type="primary", icon=":material/arrow_forward:", width="stretch"):
            ui.go_to("step2")
    with c2:
        model_download_button("dl_step1")


def _configure_and_fit(df: pd.DataFrame):
    s = M.suggest_config(df)
    numeric = s["numeric"]
    if not numeric:
        st.error("No numeric columns found. Check that numbers don't contain currency symbols or text.")
        return

    st.markdown("### :material/event: Time and outcome")
    c1, c2, c3 = st.columns(3)
    with c1:
        date_col = st.selectbox("Date column", s["date_options"], key="cfg_date",
                                index=s["date_options"].index(s["date"]) if s["date"] in s["date_options"] else 0)
    with c2:
        kpi_col = st.selectbox("Outcome column", numeric, key="cfg_kpi",
                               index=numeric.index(s["kpi"]) if s["kpi"] in numeric else 0,
                               help="The number you want to grow: revenue, sales, sign-ups…")
    with c3:
        kpi_kind = st.selectbox("Outcome is", ["Revenue", "Conversions / units"], key="cfg_kpi_kind")
    kpi_type = "revenue" if kpi_kind == "Revenue" else "non_revenue"
    rpk = None
    if kpi_type == "non_revenue":
        rpk_opt = st.selectbox("Revenue per conversion column (optional)", ["None"] + numeric, key="cfg_rpk")
        rpk = None if rpk_opt == "None" else rpk_opt

    st.markdown("### :material/campaign: Paid channels")
    st.caption("One row per channel. Exposure is impressions, clicks or GRPs. "
               "If a channel only has spend, pick the spend column for both.")
    default_rows = pd.DataFrame(s["channels"] or [{"Channel": "", "Exposure column": None, "Spend column": None}])
    options = [c for c in numeric if c != kpi_col]
    channels_df = st.data_editor(
        default_rows,
        key="cfg_channels",
        num_rows="dynamic",
        hide_index=True,
        column_config={
            "Channel": st.column_config.TextColumn("Channel", required=True, width="medium"),
            "Exposure column": st.column_config.SelectboxColumn("Exposure column", options=options, required=True),
            "Spend column": st.column_config.SelectboxColumn("Spend column", options=options, required=True),
        },
    )
    channels = [r for r in channels_df.to_dict("records") if r.get("Channel") or r.get("Spend column")]
    used = {kpi_col, *(r.get("Exposure column") for r in channels), *(r.get("Spend column") for r in channels)}

    st.markdown("### :material/tune: Controls")
    control_opts = [c for c in numeric if c not in used]
    controls = st.multiselect(
        "Things that move revenue but aren't paid media",
        control_opts,
        default=[c for c in s["controls"] if c in control_opts],
        key="cfg_controls",
        help="Price, discounts, seasonality, competitor activity, market trends.",
    )

    st.markdown("### :material/model_training: Sampling")
    c1, c2 = st.columns([1.4, 1], gap="large")
    with c1:
        preset = st.radio("How long to sample", list(M.PRESETS), index=1, horizontal=True, key="cfg_preset")
        st.caption(M.PRESET_NOTES[preset])
    with c2:
        with st.expander("Advanced"):
            max_lag = st.slider("Max carryover (weeks)", 1, 13, 8, key="cfg_lag",
                                help="How many weeks an ad can keep influencing sales.")
            seed = st.number_input("Random seed", 0, 10_000, 1, key="cfg_seed",
                                   help="Same seed + same data = same result.")

    cfg = M.ModelConfig(
        date_col=date_col, kpi_col=kpi_col, kpi_type=kpi_type, channels=channels, controls=controls,
        revenue_per_kpi_col=rpk, preset=preset, max_lag=int(max_lag), seed=int(seed),
    )
    errors, notes = M.validate(df, cfg)
    for n in notes:
        st.info(n, icon=":material/info:")
    for e in errors:
        st.error(e, icon=":material/error:")

    if st.button("Fit model", type="primary", disabled=bool(errors) or M.MERIDIAN_VERSION is None,
                 icon=":material/model_training:"):
        _run_fit(df, cfg)


def _run_fit(df: pd.DataFrame, cfg: M.ModelConfig):
    started = time.time()
    with st.status("Fitting Meridian…", expanded=True) as status:
        try:
            st.write("Preparing data")
            input_data = M.build_input_data(df, cfg)
            mmm, elapsed = M.fit(input_data, cfg, on_stage=st.write)
            st.write("Computing fit quality")
            set_model(mmm, "fitted here", {"elapsed": elapsed, "preset": cfg.preset})
        except Exception as e:
            status.update(label="Model fit failed", state="error")
            st.error(f"{type(e).__name__}: {e}")
            st.caption("Check that each channel has spend in most weeks and that controls are not copies of each other.")
            return
        status.update(label=f"Model fitted in {(time.time() - started) / 60:.1f} min", state="complete", expanded=False)
    st.rerun()
