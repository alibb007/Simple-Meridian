import time

import pandas as pd
import streamlit as st

from app_pages.common import (
    demo_available, has_model, load_demo, load_sample, model_download_button, model_loader, read_upload,
    set_data, set_model,
)
from utils import mmm as M
from utils import ui


def show_upload_and_run():
    ui.page_header(1, "Data & model", "Load data, check which column is which, then fit Meridian.",
                   "database", "blue")

    if st.session_state.data is None:
        _start_panel()
        return

    df = st.session_state.data
    _data_bar(df)

    if has_model():
        _model_ready()
        with st.expander("Change settings and fit again", icon=":material/settings:"):
            _configure_and_fit(df)
    else:
        _configure_and_fit(df)


# --------------------------------------------------------------------------- #
def _start_panel():
    st.markdown("### Choose a starting point")
    c1, c2, c3 = st.columns([1, 1, 1.25], gap="medium")
    with c1:
        with st.container(key="start-s1demo"):
            ui.start_card_header("bolt", "green", "Demo results",
                                 "Sample data with a model that is already fitted. Jumps straight to Insights.",
                                 ["No waiting"], hot="Instant")
            if st.button("Open demo results", type="primary", icon=":material/bolt:", width="stretch",
                         disabled=not demo_available(), key="s1_demo"):
                with st.spinner("Opening the demo model…"):
                    load_demo()
                ui.go_to("step2")
    with c2:
        with st.container(key="start-s1sample"):
            ui.start_card_header("science", "violet", "Sample data",
                                 "Three years of made-up weekly data for six channels. Fit it yourself to see each step.",
                                 ["156 weeks", "6 channels"])
            if st.button("Load sample data", icon=":material/table_view:", width="stretch", key="s1_sample"):
                load_sample()
                st.rerun()
    with c3:
        with st.container(key="start-s1upload"):
            ui.start_card_header("upload_file", "blue", "Your own data",
                                 "Weekly rows: a date, an outcome such as revenue, and spend per channel.",
                                 ["CSV", "XLSX", "XLS"])
            file = st.file_uploader("Upload weekly marketing data", type=["csv", "xlsx", "xls"],
                                    label_visibility="collapsed")
            if file is not None:
                try:
                    df = read_upload(file)
                except Exception as e:
                    st.error(f"Could not read {file.name}: {e}")
                    return
                set_data(df, file.name)
                st.rerun()

    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1], gap="medium")
    with c1:
        with st.expander("Already fitted a model? Open the file", icon=":material/folder_open:"):
            model_loader("loader_step1")
            if has_model():
                ui.go_to("step2")
    with c2:
        with st.expander("What should my file look like?", icon=":material/help:"):
            st.markdown(
                """
                <table style="font-size:.85rem;width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums">
                  <tr style="font-weight:600;border-bottom:1px solid var(--border)"><td>week</td><td>tv_spend</td><td>tv_impressions</td><td>price_index</td><td>sales</td></tr>
                  <tr><td>2024-01-07</td><td>81,200</td><td>9,100,000</td><td>1.02</td><td>612,400</td></tr>
                  <tr><td>2024-01-14</td><td>77,950</td><td>8,700,000</td><td>1.02</td><td>598,100</td></tr>
                </table>
                <p style="color:var(--muted);font-size:.9rem;margin-top:.6rem">One row per week with no gaps.
                Columns named like <code>tv_spend</code> and <code>tv_impressions</code> are paired automatically.
                Any common date format works.</p>
                """,
                unsafe_allow_html=True,
            )


def _data_bar(df: pd.DataFrame):
    suggestion = M.suggest_config(df)
    date_col = st.session_state.get("cfg_date", suggestion["date"])
    dates = M.parse_dates(df[date_col]) if date_col in df else None
    span = ""
    if dates is not None and dates.notna().all():
        span = f"{dates.min():%d %b %Y} → {dates.max():%d %b %Y}"

    c1, c2 = st.columns([5, 1], vertical_alignment="center")
    with c1:
        ui.pills([("description", st.session_state.data_name or "data"), ("table_rows", f"{len(df):,} rows"),
                  ("view_column", f"{df.shape[1]} columns")] + ([("date_range", span)] if span else []))
    with c2:
        if st.button("Change data", icon=":material/swap_horiz:", width="stretch"):
            st.session_state.data = None
            st.session_state.data_name = None
            st.rerun()
    with st.expander("Preview data", icon=":material/table_view:"):
        st.dataframe(df.head(50), hide_index=True, height=260)


def _model_ready():
    info = st.session_state.model_info or {}
    r2, rhat, mape, elapsed = info.get("r2"), info.get("max_rhat"), info.get("mape"), info.get("elapsed")
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
    with st.container(horizontal=True):
        if st.button("See insights", type="primary", icon=":material/arrow_forward:"):
            ui.go_to("step2")
        model_download_button("dl_step1")


def _section(n: int, icon_name: str, title: str, hint: str):
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:.7rem;margin:.2rem 0 .3rem">'
        f'<span class="sm-badge" style="width:30px;height:30px;background:#EEF3FF;color:var(--primary);'
        f'font-weight:800;font-size:.9rem;border-radius:9px">{n}</span>'
        f'<span style="font-family:var(--display);font-weight:700;font-size:1.12rem">{title}</span>'
        f'{ui.icon(icon_name, 20, "#98A2B3")}</div>'
        f'<p style="color:var(--muted);font-size:.9rem;margin:0 0 .6rem 2.6rem">{hint}</p>',
        unsafe_allow_html=True,
    )


def _configure_and_fit(df: pd.DataFrame):
    s = M.suggest_config(df)
    numeric = s["numeric"]
    if not numeric:
        st.error("No numeric columns found. Check that numbers don't contain currency symbols or text.")
        return

    left, right = st.columns([2.1, 1], gap="large")
    with left:
        with st.container(border=True):
            _section(1, "event", "Time and outcome", "Which column holds the week, and what you want to grow.")
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

        with st.container(border=True):
            _section(2, "campaign", "Paid channels",
                     "One row per channel: its spend, and its impressions or clicks. "
                     "No exposure data? Pick the spend column for both.")
            default_rows = pd.DataFrame(s["channels"] or [{"Channel": "", "Exposure column": None, "Spend column": None}])
            options = [c for c in numeric if c != kpi_col]
            channels_df = st.data_editor(
                default_rows, key="cfg_channels", num_rows="dynamic", hide_index=True,
                column_config={
                    "Channel": st.column_config.TextColumn("Channel", required=True, width="medium"),
                    "Exposure column": st.column_config.SelectboxColumn("Exposure column", options=options, required=True),
                    "Spend column": st.column_config.SelectboxColumn("Spend column", options=options, required=True),
                },
            )
            channels = [r for r in channels_df.to_dict("records") if r.get("Channel") or r.get("Spend column")]
            used = {kpi_col, *(r.get("Exposure column") for r in channels), *(r.get("Spend column") for r in channels)}

        with st.container(border=True):
            _section(3, "tune", "Controls (optional)",
                     "Things that move revenue but aren't paid media: price, discounts, seasonality, market trends.")
            control_opts = [c for c in numeric if c not in used]
            controls = st.multiselect("Control columns", control_opts,
                                      default=[c for c in s["controls"] if c in control_opts], key="cfg_controls",
                                      label_visibility="collapsed")

    with right:
        with st.container(border=True, key="runcard"):
            st.markdown(f'<div style="display:flex;gap:.6rem;align-items:center">{ui.badge("rocket_launch", "violet", 38)}'
                        '<span style="font-family:var(--display);font-weight:800;font-size:1.2rem">Ready to fit</span></div>',
                        unsafe_allow_html=True)
            preset = st.radio("Sampling", list(M.PRESETS), index=0, key="cfg_preset",
                              help="More samples give tighter estimates. Most of the time is a one-off compile, "
                                   "so Standard costs only a little more than Quick check.")
            st.caption(M.PRESET_NOTES[preset])
            with st.expander("Advanced"):
                max_lag = st.slider("Max carryover (weeks)", 1, 13, 8, key="cfg_lag",
                                    help="How many weeks an ad can keep influencing sales.")
                seed = st.number_input("Random seed", 0, 10_000, 1, key="cfg_seed",
                                       help="Same seed + same data = same result.")

            cfg = M.ModelConfig(
                date_col=date_col, kpi_col=kpi_col, kpi_type=kpi_type, channels=channels, controls=controls,
                revenue_per_kpi_col=rpk, preset=preset, max_lag=int(max_lag), seed=int(seed),
                roi_priors=dict(st.session_state.get("calibration") or {}),
            )
            errors, notes = M.validate(df, cfg)
            n_ch = len([r for r in channels if r.get("Channel") and r.get("Spend column")])
            checks = [
                (True, f"{len(df):,} weeks of data"),
                (bool(kpi_col), f"Outcome: {kpi_col}"),
                (n_ch > 0, f"{n_ch} paid channel{'s' if n_ch != 1 else ''}"),
                (True, f"{len(controls)} control{'s' if len(controls) != 1 else ''}"),
                (not errors, "Data checks passed" if not errors else f"{len(errors)} problem{'s' if len(errors) > 1 else ''} to fix"),
            ]
            names = {r.get("Channel", "").strip() for r in channels}
            for ch, (m, sd) in (cfg.roi_priors or {}).items():
                checks.append((ch in names, f"Lift-test prior for {ch}: ${m:.2f} ± {sd:.2f}"
                                            + ("" if ch in names else " (no such channel, ignored)")))
            st.markdown("".join(
                f'<div style="display:flex;gap:.5rem;align-items:center;font-size:.92rem;margin:.25rem 0">'
                f'{ui.icon("check_circle" if ok else "cancel", 18, ui.GOOD if ok else ui.BAD)}{text}</div>'
                for ok, text in checks), unsafe_allow_html=True)
            fit_clicked = st.button("Fit model", type="primary", width="stretch", icon=":material/model_training:",
                                    disabled=bool(errors) or M.MERIDIAN_VERSION is None)
        for n in notes:
            st.info(n, icon=":material/info:")
        for e in errors:
            st.error(e, icon=":material/error:")

    if fit_clicked:
        _run_fit(df, cfg)


def _run_fit(df: pd.DataFrame, cfg: M.ModelConfig):
    started = time.time()
    with st.status("Fitting Meridian…", expanded=True) as status:
        try:
            st.write("Loading Meridian")
            M.lib()
            st.write("Preparing data")
            input_data = M.build_input_data(df, cfg)
            with M.heavy_job(on_wait=lambda: st.write("Another fit is running on this server. Waiting for a free slot…")):
                mmm, elapsed = M.fit(input_data, cfg, on_stage=st.write)
            st.write("Computing fit quality")
            set_model(mmm, "fitted here", {"elapsed": elapsed, "preset": cfg.preset,
                                           "priors": sorted(cfg.roi_priors)})
        except Exception as e:
            status.update(label="Model fit failed", state="error")
            st.error(f"{type(e).__name__}: {e}")
            st.caption("Check that each channel has spend in most weeks and that controls are not copies of each other.")
            return
        status.update(label=f"Model fitted in {(time.time() - started) / 60:.1f} min", state="complete", expanded=False)
    st.rerun()
