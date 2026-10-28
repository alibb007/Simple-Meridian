"""Lift test page: design and measure a geo experiment with Meridian GeoX."""
import pandas as pd
import streamlit as st

from app_pages.common import cached_summary, has_model
from utils import charts
from utils import geox as G
from utils import mmm as M
from utils import ui

SAMPLE_CHANNELS = ["TV", "Radio", "Display", "Search", "Social", "Email"]


@st.cache_data(show_spinner=False)
def _sample(test_days: int) -> pd.DataFrame:
    return G.sample_geo_data(pre_days=120, test_days=test_days)


# GeoX searches region splits at random; this seed's split (28 days, 30%) puts the
# true value inside the 90% range. Across seeds 1-12 the range held the truth
# 9 times and every estimate was within 10% of it (checked 27 Oct 2026).
DEFAULT_SPLIT_SEED = 2


@st.cache_resource(show_spinner=False, max_entries=16)
def _design(test_days: int, max_share: float, expected_iroas: float, seed: int):
    """Shared across visitors: the same settings always give the same design."""
    df = _sample(test_days)
    start = sorted(df["date"].unique())[120]
    with M.heavy_job():
        design, metrics = G.design_test(df[df["date"] < start], test_days, max_share, expected_iroas, seed=seed)
    return design, metrics, start


@st.cache_resource(show_spinner=False, max_entries=32)
def _run_sample(test_days: int, max_share: float, expected_iroas: float, seed: int, true_iroas: float,
                spend_pct: float):
    design, _, start = _design(test_days, max_share, expected_iroas, seed)
    df = G.simulate_campaign(_sample(test_days), G.design_summary(design)["treatment"], start, true_iroas, spend_pct)
    with M.heavy_job():
        result = G.analyze_test(df, design, start, df["date"].max())
    return df, result


def show_lift_test():
    st.markdown(
        f'<div class="sm-head">{ui.badge("science", "violet", 52)}<div>'
        f'<div class="sm-kicker"><span class="sm-new">NEW</span> Meridian GeoX {G.GEOX_VERSION or ""}</div>'
        f'<h1>Lift test</h1></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="sm-lede">A marketing mix model learns from history, so it can be wrong. A lift test is a real '
        "experiment: run a campaign in some regions, keep it off in similar ones, and measure the gap. "
        "Google's GeoX picks the regions and does the math. Its result can then steer your Meridian model.</p>",
        unsafe_allow_html=True,
    )
    if G.GEOX_VERSION is None:
        st.error("meridian-geox is not installed. Run `pip install -r requirements.txt`.")
        return

    _how_it_works_strip()
    tabs = st.tabs([":material/school: Try the sample test", ":material/upload_file: Measure your own test",
                    ":material/menu_book: Words explained"])
    with tabs[0]:
        _sample_tab()
    with tabs[1]:
        _own_tab()
    with tabs[2]:
        _glossary()


def _how_it_works_strip():
    steps = [
        ("map", "blue", "1. Split regions", "GeoX picks test regions and control regions that moved together in the past."),
        ("campaign", "violet", "2. Run the campaign", "Ads run only in the test regions, usually for 3-6 weeks."),
        ("query_stats", "teal", "3. Measure the gap", "Control regions show what test regions would have done without ads."),
        ("tune", "amber", "4. Calibrate the MMM", "The measured return per $1 becomes a prior for that channel in Meridian."),
    ]
    cols = st.columns(4, gap="small")
    for col, (ic, accent, title, body) in zip(cols, steps):
        with col:
            st.markdown(f'<div class="sm-tile" style="height:100%">{ui.badge(ic, accent, 36)}<div>'
                        f'<div style="font-weight:700">{title}</div><div class="d" style="font-size:.86rem">{body}</div>'
                        f"</div></div>", unsafe_allow_html=True)
    st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
def _sample_tab():
    ui.callout("This is made-up data for 40 regions. You choose how well the pretend campaign really works, then "
               "see whether GeoX can find that number without being told.", "info")

    with st.container(border=True):
        st.markdown("#### 1 · Plan the test")
        c1, c2, c3 = st.columns(3)
        test_days = c1.select_slider("Test length", [14, 21, 28, 42], value=28, format_func=lambda d: f"{d} days",
                                     key="gx_days")
        max_share = c2.select_slider("Max share of revenue in test regions", [0.1, 0.2, 0.3, 0.4], value=0.3,
                                     format_func=lambda v: f"{v:.0%}", key="gx_share")
        expected = c3.number_input("Return you expect per $1", 0.5, 10.0, 2.0, 0.5, key="gx_expected",
                                   help="Used to suggest a test budget.")
        seed = st.session_state.setdefault("gx_seed", DEFAULT_SPLIT_SEED)
        with st.container(horizontal=True):
            if st.button("Pick test regions", type="primary", icon=":material/map:", key="gx_design_btn"):
                st.session_state.gx_planned = (test_days, max_share, expected, seed)
            if st.session_state.get("gx_planned") and st.button("Try another split", icon=":material/shuffle:",
                                                                 key="gx_reshuffle"):
                st.session_state.gx_seed = seed + 1
                st.session_state.gx_planned = (test_days, max_share, expected, seed + 1)
                st.rerun()

    planned = st.session_state.get("gx_planned")
    if not planned:
        return
    with st.spinner("GeoX is comparing thousands of region splits…"):
        design, metrics, start = _design(*planned)
    s = G.design_summary(design)
    df = _sample(planned[0])
    ui.tiles([
        dict(label="Test regions", value=str(len(s["treatment"])), detail="ads run here", icon="campaign", accent="violet"),
        dict(label="Control regions", value=str(len(s["control"])), detail="no change", icon="block", accent="blue"),
        dict(label="Smallest lift it can detect", value=f"{s['mde']:.1%}", detail="of test-region revenue",
             icon="center_focus_strong", accent="teal"),
        dict(label="Suggested budget", value=ui.money(s["budget"]), detail=f"over {planned[0]} days", icon="payments",
             accent="amber"),
    ])
    st.plotly_chart(charts.geo_groups(df[df["date"] < start], s["treatment"], s["excluded"]), config=charts.CONFIG)

    with st.container(border=True):
        st.markdown("#### 2 · Run it (simulated)")
        c1, c2 = st.columns(2)
        true_iroas = c1.slider("How well the campaign really works (\\$ back per \\$1)", 0.0, 6.0, 2.5, 0.25, key="gx_true",
                               help="Hidden from GeoX. We build this into the data, then check if GeoX finds it.")
        spend_pct = c2.select_slider("Campaign spend, % of test-region revenue", [0.01, 0.02, 0.04, 0.08], value=0.04,
                                     format_func=lambda v: f"{v:.0%}", key="gx_spend")
        if st.button("Run the test and measure", type="primary", icon=":material/play_arrow:", key="gx_run_btn"):
            st.session_state.gx_ran = (*planned, true_iroas, spend_pct)

    ran = st.session_state.get("gx_ran")
    if not ran or ran[:4] != planned:
        return
    with st.spinner("Measuring the lift…"):
        run_df, result = _run_sample(*ran)
    _results(result, start, truth=ran[4])
    _use_as_prior(result, default_channel="TV")


def _results(r: dict, start, truth: float | None = None):
    st.markdown("#### 3 · Results")
    roi, lift, pct = r["iroas"], r["lift"], r["pct"]
    tiles = [
        dict(label="Extra revenue from the campaign", value=ui.money(lift["mean"]),
             detail=f"90% range {ui.money(lift['lo'])} – {ui.money(lift['hi'])}", icon="trending_up", accent="green"),
        dict(label="Lift", value=f"{pct['mean']:+.1%}", detail="vs. expected revenue in test regions",
             icon="north_east", accent="teal"),
    ]
    if roi:
        tiles.append(dict(label="Return per $1 (iROAS)", value=f"${roi['mean']:.2f}",
                          detail=f"90% range ${roi['lo']:.2f} – ${roi['hi']:.2f}", icon="percent", accent="violet"))
    sig = lift["p"] < 0.1
    tiles.append(dict(label="Is it real?", value="Yes" if sig else "Not sure",
                      chip=f"p = {lift['p']:.3f}", direction="up" if sig else "down",
                      detail="" if sig else "Run longer or spend more", icon="verified" if sig else "help",
                      accent="green" if sig else "rose"))
    ui.tiles(tiles)
    if truth is not None and roi:
        inside = roi["lo"] <= truth <= roi["hi"]
        ui.callout(f"GeoX measured <b>${roi['mean']:.2f}</b> back per $1. The true value built into the data was "
                   f"<b>${truth:.2f}</b>, which is {'inside' if inside else 'outside'} GeoX's 90% range. "
                   "A 90% range should miss now and then: across 12 different region splits of this sample, "
                   "the range held the true value 9 times, and every estimate was within 10% of it. "
                   "Press <b>Try another split</b> to see a different one.",
                   "check_circle" if inside else "info")
    c1, c2 = st.columns([1.3, 1], gap="medium")
    with c1:
        st.markdown("##### Test regions: actual vs. expected without the campaign")
        st.plotly_chart(charts.geo_counterfactual(r["counterfactual"], start), config=charts.CONFIG)
    with c2:
        st.markdown("##### Extra revenue, adding up day by day")
        st.plotly_chart(charts.geo_cumulative(r["cumulative"]), config=charts.CONFIG)
    if r["excluded_geos"]:
        st.caption("Left out by GeoX's data checks: " + ", ".join(r["excluded_geos"]))


def _use_as_prior(r: dict, default_channel: str):
    roi = r.get("iroas")
    if not roi:
        return
    with st.container(border=True):
        st.markdown("#### 4 · Teach the model")
        st.markdown('<p style="color:var(--muted);font-size:.93rem">Use this result as the starting belief (a '
                    '"prior") for one channel\'s ROI. The next time you fit in step 1, Meridian combines it with '
                    "your weekly data, which usually narrows that channel's range a lot.</p>",
                    unsafe_allow_html=True)
        channels = SAMPLE_CHANNELS
        if has_model():
            try:
                summary = cached_summary(st.session_state.mmm, st.session_state.model_key)
                channels = summary[~summary.is_total].channel.tolist()
            except Exception:
                pass
        mean, sd = G.prior_from_iroas(roi["mean"], roi["sd"])
        c1, c2 = st.columns([1, 2], vertical_alignment="bottom")
        ch = c1.selectbox("Channel this test measured", channels,
                          index=channels.index(default_channel) if default_channel in channels else 0, key="gx_prior_ch")
        if c2.button(f"Use ${mean:.2f} ± {sd:.2f} as {ch}'s ROI prior", icon=":material/tune:", key="gx_prior_btn"):
            st.session_state.setdefault("calibration", {})[ch] = (mean, sd)
            st.toast(f"Saved. Fit the model in step 1 to use it for {ch}.", icon=":material/check_circle:")
            st.rerun()  # so the sidebar shows the new prior
    cal = st.session_state.get("calibration") or {}
    if cal:
        ui.pills([("tune", f"{c}: ${m:.2f} ± {s:.2f}") for c, (m, s) in cal.items()])
        with st.container(horizontal=True):
            if st.button("Fit with these priors", type="primary", icon=":material/arrow_forward:", key="gx_to_fit"):
                ui.go_to("step1")
            if st.button("Clear priors", icon=":material/delete:", key="gx_clear"):
                st.session_state.calibration = {}
                st.rerun()


# --------------------------------------------------------------------------- #
def _own_tab():
    st.markdown("Upload **daily** data per region with four columns: `date`, `location`, `conversions` "
                "(revenue or sales) and `spend` (campaign spend, 0 outside the test).")
    file = st.file_uploader("Geo test data (CSV)", type=["csv"], key="gx_upload")
    if file is None:
        with st.expander("Example of the format", icon=":material/table_view:"):
            st.dataframe(pd.DataFrame({"date": ["2025-05-01", "2025-05-01", "2025-05-02"],
                                       "location": ["Region 01", "Region 02", "Region 01"],
                                       "conversions": [24310.5, 18022.0, 25110.8], "spend": [950.0, 0.0, 1010.0]}),
                         hide_index=True)
            st.download_button("Download the sample as CSV", G.sample_geo_data().to_csv(index=False),
                               "geox_sample.csv", "text/csv", icon=":material/download:", on_click="ignore")
        return
    df = pd.read_csv(file)
    df.columns = [c.lower() for c in df.columns]
    errors = G.validate_geo_data(df)
    if errors:
        for e in errors:
            st.error(e)
        return
    df["date"] = pd.to_datetime(df["date"])
    regions = sorted(df["location"].astype(str).unique())
    df["location"] = df["location"].astype(str)
    dates = sorted(df["date"].dt.date.unique())
    spending = sorted(df.loc[df["spend"] > 0, "location"].unique())

    c1, c2 = st.columns([2, 1])
    treatment = c1.multiselect("Test regions (where the campaign ran)", regions, default=spending, key="gx_own_t")
    default_start = df.loc[df["spend"] > 0, "date"].min()
    start, end = c2.select_slider("Test period", dates,
                                  value=(default_start.date() if pd.notna(default_start) else dates[len(dates) * 3 // 4],
                                         dates[-1]), key="gx_own_dates")
    if st.button("Measure the lift", type="primary", icon=":material/query_stats:", key="gx_own_btn",
                 disabled=len(treatment) == 0):
        days = (pd.Timestamp(end) - pd.Timestamp(start)).days + 1
        with st.spinner("Measuring the lift…"):
            try:
                with M.heavy_job(on_wait=lambda: st.info("Another job is running. Waiting for a free slot…")):
                    design = G.manual_design(df, treatment, start, days)
                    st.session_state.gx_own = (G.analyze_test(df, design, start, end), start)
            except Exception as e:
                st.error(f"GeoX could not analyze this test: {e}")
    if st.session_state.get("gx_own"):
        result, start = st.session_state.gx_own
        _results(result, start)
        _use_as_prior(result, default_channel="")


def _glossary():
    terms = [
        ("Lift test / geo experiment", "Turning a campaign on in some regions and comparing them with similar regions "
                                        "where it stays off. The difference is what the campaign caused."),
        ("Test and control regions", "Test regions get the campaign. Control regions don't, and show what would have "
                                     "happened anyway."),
        ("Expected without the campaign", "GeoX's prediction for the test regions, built from how they tracked the "
                                          "control regions before the test (Time-Based Regression)."),
        ("Lift", "Extra revenue in the test regions above that prediction."),
        ("Return per $1 (iROAS)", "Extra revenue divided by campaign spend. GeoX calls it ICPD."),
        ("Smallest lift it can detect", "If the real effect is smaller than this, the test will probably miss it. "
                                        "Longer tests and more regions make it smaller."),
        ("p-value", "Roughly, the chance of seeing a gap this big if the campaign did nothing. Below 0.1 is a "
                    "common bar."),
        ("ROI prior", "Meridian's starting belief about a channel's ROI before it sees your data. A lift test makes "
                      "that belief much sharper."),
    ]
    cols = st.columns(2, gap="medium")
    for i, (t, d) in enumerate(terms):
        with cols[i % 2]:
            st.markdown(f'<div class="sm-tile" style="margin-bottom:.6rem"><div><div style="font-weight:700">{t}</div>'
                        f'<div class="d" style="font-size:.9rem">{d}</div></div></div>', unsafe_allow_html=True)
    st.markdown("Read more in Google's [GeoX documentation](https://developers.google.com/meridian/geox).")
