import html
import itertools
import time

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app_pages.common import (
    demo_available, has_model, load_demo, load_sample, model_download_button, model_loader, read_upload,
    set_data, set_model,
)
from utils import charts
from utils import mmm as M
from utils import ui

_ids = itertools.count(1)


def show_upload_and_run():
    ui.page_header(1, "Data & model", "Upload your data, tell the app which column is which, then fit Meridian.",
                   "database", "blue")
    df = st.session_state.data
    _progress(df)

    _section(1, "upload_file", "Your data", "One row per week: a date, your sales, and spend for each channel.")
    if df is None:
        _start_panel()
        return
    _data_card(df)
    cfg, errors, notes, fit_clicked = _configure(df)
    if fit_clicked:
        _run_fit(df, cfg)
    if has_model():
        _model_ready()


# --------------------------------------------------------------------------- #
def _progress(df):
    done = [df is not None, df is not None, df is not None, df is not None, has_model()]
    labels = ["Data", "Time & outcome", "Paid channels", "Controls", "Fit"]
    chips = "".join(
        f'<span class="sm-step {"on" if d else ""}"><b>{i}</b>{lab}</span>'
        for i, (lab, d) in enumerate(zip(labels, done), start=1)
    )
    st.markdown(f'<div class="sm-stepbar">{chips}</div>', unsafe_allow_html=True)


def _section(n: int, icon_name: str, title: str, hint: str):
    st.markdown(
        f'<div class="sm-sec"><span class="sm-sec-n">{n}</span>'
        f'<span class="sm-sec-t">{html.escape(title)}</span>{ui.icon(icon_name, 20, "#98A2B3")}</div>'
        f'<p class="sm-sec-h">{html.escape(hint)}</p>',
        unsafe_allow_html=True,
    )


def _start_panel():
    c1, c2, c3 = st.columns([1.25, 1, 1], gap="medium")
    with c1:
        with st.container(key="start-s1upload"):
            ui.start_card_header("upload_file", "blue", "Upload your file",
                                 "CSV or Excel. Date, outcome and channel columns are detected for you.",
                                 ["CSV", "XLSX", "XLS"], hot="Start here")
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
    with c2:
        with st.container(key="start-s1sample"):
            ui.start_card_header("science", "violet", "Or use the sample",
                                 "Three years of made-up weekly data for six channels.", ["156 weeks", "6 channels"])
            if st.button("Load sample data", icon=":material/table_view:", width="stretch", key="s1_sample"):
                load_sample()
                st.rerun()
    with c3:
        with st.container(key="start-s1demo"):
            ui.start_card_header("bolt", "green", "Just look around",
                                 "Skip fitting: open a model already fitted on the sample.", ["No waiting"])
            if st.button("Open demo results", icon=":material/bolt:", width="stretch",
                         disabled=not demo_available(), key="s1_demo"):
                with st.spinner("Opening the demo model…"):
                    load_demo()
                ui.go_to("step2")

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        with st.expander("What should my file look like?", icon=":material/help:"):
            st.markdown(
                """
                <table style="font-size:.85rem;width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums">
                  <tr style="font-weight:600;border-bottom:1px solid var(--border)"><td>week</td><td>tv_spend</td><td>tv_impressions</td><td>price_index</td><td>sales</td></tr>
                  <tr><td>2024-01-07</td><td>81,200</td><td>9,100,000</td><td>1.02</td><td>612,400</td></tr>
                  <tr><td>2024-01-14</td><td>77,950</td><td>8,700,000</td><td>1.02</td><td>598,100</td></tr>
                </table>
                <p style="color:var(--muted);font-size:.9rem;margin-top:.6rem">One row per week with no gaps.
                Columns named like <code>tv_spend</code> and <code>tv_impressions</code> are paired automatically.</p>
                """,
                unsafe_allow_html=True,
            )
    with c2:
        with st.expander("Already fitted a model? Open the file", icon=":material/folder_open:"):
            model_loader("loader_step1")
            if has_model():
                ui.go_to("step2")


def _data_card(df: pd.DataFrame):
    suggestion = M.suggest_config(df)
    date_col = st.session_state.get("cfg_date", suggestion["date"])
    dates = M.parse_dates(df[date_col]) if date_col in df else None
    span = ""
    if dates is not None and dates.notna().all():
        span = f"{dates.min():%d %b %Y} → {dates.max():%d %b %Y}"
    with st.container(border=True, key="s1-data"):
        c1, c2 = st.columns([5, 1], vertical_alignment="center")
        with c1:
            ui.pills([("description", st.session_state.data_name or "data"), ("table_rows", f"{len(df):,} rows"),
                      ("view_column", f"{df.shape[1]} columns")] + ([("date_range", span)] if span else []))
        with c2:
            if st.button("Change data", icon=":material/swap_horiz:", width="stretch"):
                st.session_state.data = None
                st.session_state.data_name = None
                st.rerun()
        with st.expander("Preview the table", icon=":material/table_view:"):
            st.dataframe(df.head(50), hide_index=True, height=260)


# --------------------------------------------------------------------------- #
def _default_rows(s: dict) -> list[dict]:
    return [{"id": next(_ids), "name": r["Channel"], "exposure": r["Exposure column"], "spend": r["Spend column"]}
            for r in s["channels"]]


def _channel_cards(df: pd.DataFrame, s: dict, kpi_col: str) -> list[dict]:
    """Interactive channel editor: one card per channel, add and remove freely."""
    numeric = [c for c in s["numeric"] if c != kpi_col]
    if "cfg_rows" not in st.session_state:
        st.session_state.cfg_rows = _default_rows(s)
    rows = st.session_state.cfg_rows
    colors = charts.color_map([r["name"] or f"Channel {i + 1}" for i, r in enumerate(rows)])

    found = len(s["channels"])
    with st.container(horizontal=True, vertical_alignment="center", horizontal_alignment="distribute"):
        st.markdown(
            f'<span class="sm-pill" style="margin:0">{ui.icon("auto_awesome", 16, "#6941C6")}'
            f'{found} channel{"s" if found != 1 else ""} found in your data</span>',
            unsafe_allow_html=True,
        )
        with st.container(horizontal=True, width="content"):
            add = st.button("Add channel", icon=":material/add:", key="ch_add")
            reset = st.button("Reset", icon=":material/restart_alt:", key="ch_reset", type="tertiary")
        if add:
            used = {r["spend"] for r in rows}
            free = next((c for c in numeric if c not in used), numeric[0] if numeric else None)
            rows.append({"id": next(_ids), "name": f"Channel {len(rows) + 1}", "exposure": free, "spend": free})
            st.rerun()
        if reset:
            st.session_state.cfg_rows = _default_rows(s)
            st.rerun()

    cols = st.columns(3, gap="small")
    for i, r in enumerate(rows):
        with cols[i % 3]:
            with st.container(border=True, key=f"chcard-{r['id']}"):
                color = colors.get(r["name"] or f"Channel {i + 1}", ui.PRIMARY)
                top = st.columns([6, 1], vertical_alignment="bottom")
                r["name"] = top[0].text_input("Channel name", value=r["name"], key=f"ch_name_{r['id']}",
                                              placeholder="e.g. TV")
                if top[1].button(":material/delete:", key=f"ch_del_{r['id']}", help="Remove this channel",
                                 type="tertiary"):
                    st.session_state.cfg_rows = [x for x in rows if x["id"] != r["id"]]
                    st.rerun()
                idx = lambda v: numeric.index(v) if v in numeric else 0  # noqa: E731
                r["spend"] = st.selectbox("Spend column", numeric, index=idx(r["spend"]), key=f"ch_spend_{r['id']}")
                r["exposure"] = st.selectbox("Impressions / clicks column", numeric,
                                             index=idx(r["exposure"]), key=f"ch_exp_{r['id']}",
                                             help="No exposure data? Pick the spend column again.")
                total = float(df[r["spend"]].sum()) if r["spend"] in df else 0.0
                st.markdown(f'<div class="sm-chfoot"><i style="background:{color}"></i>'
                            f"{ui.money(total)} spent in this data</div>", unsafe_allow_html=True)
    return [{"Channel": r["name"], "Exposure column": r["exposure"], "Spend column": r["spend"]} for r in rows]


def _outcome_chart(df: pd.DataFrame, date_col: str, kpi_col: str):
    dates = M.parse_dates(df[date_col])
    if dates.isna().any() or kpi_col not in df:
        return
    d = pd.DataFrame({"t": dates, "y": df[kpi_col]}).sort_values("t")
    fig = go.Figure(go.Scatter(x=d.t, y=d.y, line=dict(color=ui.PRIMARY, width=2), fill="tozeroy",
                               fillcolor="rgba(36,89,232,.08)", hovertemplate="%{x|%d %b %Y}<br>%{y:,.0f}<extra></extra>"))
    fig.update_layout(height=170, margin=dict(l=0, r=0, t=4, b=24), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", showlegend=False, font=dict(family=ui.FONT_BODY, size=11))
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor=ui.GRID, tickformat="~s")
    st.plotly_chart(fig, config={"displayModeBar": False}, key="s1_outcome_chart")


def _configure(df: pd.DataFrame):
    s = M.suggest_config(df)
    numeric = s["numeric"]
    if not numeric:
        st.error("No numeric columns found. Check that numbers don't contain currency symbols or text.")
        return None, ["no numeric columns"], [], False

    left, right = st.columns([2.2, 1], gap="large")
    with left:
        _section(2, "event", "Time and outcome", "Which column holds the week, and what you want to grow.")
        with st.container(border=True, key="s1-time"):
            c1, c2, c3 = st.columns(3)
            date_col = c1.selectbox("Date column", s["date_options"], key="cfg_date",
                                    index=s["date_options"].index(s["date"]) if s["date"] in s["date_options"] else 0)
            kpi_col = c2.selectbox("Outcome column", numeric, key="cfg_kpi",
                                   index=numeric.index(s["kpi"]) if s["kpi"] in numeric else 0,
                                   help="The number you want to grow: revenue, sales, sign-ups…")
            kpi_kind = c3.selectbox("Outcome is", ["Revenue", "Conversions / units"], key="cfg_kpi_kind")
            kpi_type = "revenue" if kpi_kind == "Revenue" else "non_revenue"
            rpk = None
            if kpi_type == "non_revenue":
                rpk_opt = st.selectbox("Revenue per conversion column (optional)", ["None"] + numeric, key="cfg_rpk")
                rpk = None if rpk_opt == "None" else rpk_opt
            _outcome_chart(df, date_col, kpi_col)

        _section(3, "campaign", "Paid channels", "Each channel needs its spend and, if you have it, its impressions.")
        with st.container(key="s1-channels"):
            channels = _channel_cards(df, s, kpi_col)
        used = {kpi_col, *(r["Exposure column"] for r in channels), *(r["Spend column"] for r in channels)}

        _section(4, "tune", "Controls (optional)",
                 "Things that move sales but aren't paid media: price, discounts, seasonality, market trends.")
        with st.container(border=True, key="s1-controls"):
            control_opts = [c for c in numeric if c not in used]
            controls = st.multiselect("Control columns", control_opts,
                                      default=[c for c in s["controls"] if c in control_opts], key="cfg_controls",
                                      label_visibility="collapsed", placeholder="Pick any columns that apply")

    with right:
        _section(5, "rocket_launch", "Fit", "Check the list, then fit.")
        with st.container(border=True, key="runcard"):
            preset = st.radio("Sampling", list(M.PRESETS), index=0, key="cfg_preset",
                              help="More samples give tighter estimates. Most of the time is a one-off compile, "
                                   "so Standard costs only a little more than Quick check.")
            st.caption(M.PRESET_NOTES[preset])
            cfg = M.ModelConfig(date_col=date_col, kpi_col=kpi_col, kpi_type=kpi_type, channels=channels,
                                controls=controls, revenue_per_kpi_col=rpk, preset=preset,
                                roi_priors=dict(st.session_state.get("calibration") or {}))
            errors, notes = M.validate(df, cfg)
            n_ch = len([r for r in channels if r.get("Channel") and r.get("Spend column")])
            checks = [
                (True, f"{len(df):,} weeks of data"),
                (bool(kpi_col), f"Outcome: {kpi_col}"),
                (n_ch > 0, f"{n_ch} paid channel{'s' if n_ch != 1 else ''}"),
                (True, f"{len(controls)} control{'s' if len(controls) != 1 else ''}"),
                (not errors, "Data checks passed" if not errors
                 else f"{len(errors)} problem{'s' if len(errors) > 1 else ''} to fix"),
            ]
            names = {(r.get("Channel") or "").strip() for r in channels}
            for ch, (m, sd) in (cfg.roi_priors or {}).items():
                checks.append((ch in names, f"GeoX prior for {ch}: ${m:.2f} ± {sd:.2f}"
                               + ("" if ch in names else " (no such channel, ignored)")))
            st.markdown("".join(
                f'<div style="display:flex;gap:.5rem;align-items:center;font-size:.92rem;margin:.25rem 0">'
                f'{ui.icon("check_circle" if ok else "cancel", 18, ui.GOOD if ok else ui.BAD)}{html.escape(text)}</div>'
                for ok, text in checks), unsafe_allow_html=True)
            fit_clicked = st.button("Refit model" if has_model() else "Fit model", type="primary", width="stretch",
                                    icon=":material/model_training:",
                                    disabled=bool(errors) or M.MERIDIAN_VERSION is None)
        for n in notes:
            st.info(n, icon=":material/info:")
        for e in errors:
            st.error(e, icon=":material/error:")
    return cfg, errors, notes, fit_clicked


def _model_ready():
    info = st.session_state.model_info or {}
    r2, rhat, mape, elapsed = info.get("r2"), info.get("max_rhat"), info.get("mape"), info.get("elapsed")
    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
    with st.container(border=True, key="s1-ready"):
        st.markdown(f'<div style="display:flex;gap:.7rem;align-items:center">{ui.badge("task_alt", "green", 40)}'
                    '<span style="font-family:var(--display);font-weight:800;font-size:1.25rem">Model ready</span></div>',
                    unsafe_allow_html=True)
        ok = (rhat or 0) < 1.2
        ui.tiles([
            dict(label="Fit (R²)", value=f"{r2:.2f}" if r2 is not None else "–", icon="target", accent="blue",
                 detail="share of weekly variation explained"),
            dict(label="Error (MAPE)", value=f"{mape * 100:.1f}%" if mape is not None else "–", icon="straighten",
                 accent="violet", detail="average miss per week"),
            dict(label="Convergence (R-hat)", value=f"{rhat:.2f}" if rhat is not None else "–",
                 icon="check_circle" if ok else "error", accent="green" if ok else "rose",
                 chip="Converged" if ok else "Fit again", direction="up" if ok else "down"),
            dict(label="Fit time", value=f"{elapsed / 60:.1f} min" if elapsed else "Loaded", icon="timer",
                 accent="amber", detail=info.get("preset") or info.get("source", "")),
        ])
        with st.container(horizontal=True):
            if st.button("See insights", type="primary", icon=":material/arrow_forward:"):
                ui.go_to("step2")
            model_download_button("dl_step1")


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
            set_model(mmm, "fitted here", {"elapsed": elapsed, "preset": cfg.preset, "priors": sorted(cfg.roi_priors)})
        except Exception as e:
            status.update(label="Model fit failed", state="error")
            st.error(f"{type(e).__name__}: {e}")
            st.caption("Check that each channel has spend in most weeks and that controls are not copies of each other.")
            return
        status.update(label=f"Model fitted in {(time.time() - started) / 60:.1f} min", state="complete", expanded=False)
    st.rerun()
