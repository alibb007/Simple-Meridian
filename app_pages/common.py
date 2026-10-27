"""Helpers shared by the step pages: data loading, model state, cached analysis."""
from __future__ import annotations

import os
import time
import uuid

import pandas as pd
import streamlit as st

from utils import mmm as M
from utils import ui

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_PATH = os.path.join(ROOT, "data", "simple_dataset.csv")


def load_sample():
    set_data(pd.read_csv(SAMPLE_PATH), "simple_dataset.csv")


def set_data(df: pd.DataFrame, name: str):
    st.session_state.data = df
    st.session_state.data_name = name
    for k in [k for k in st.session_state.keys() if str(k).startswith("cfg_")]:
        del st.session_state[k]


def read_upload(file) -> pd.DataFrame:
    if file.name.lower().endswith(".csv"):
        return pd.read_csv(file)
    return pd.read_excel(file)


def set_model(mmm, source: str, extra: dict | None = None):
    st.session_state.mmm = mmm
    st.session_state.model_key = uuid.uuid4().hex
    st.session_state.optimization = None
    info = {"source": source, "loaded_at": time.time()}
    try:
        info.update(cached_quality(mmm, st.session_state.model_key))
    except Exception:  # quality is informational; never block on it
        pass
    info.update(extra or {})
    st.session_state.model_info = info


def has_model() -> bool:
    return st.session_state.get("mmm") is not None


# Analyzer calls take a few seconds each. Cache them per model; the leading
# underscore tells Streamlit not to hash the Meridian object itself.
@st.cache_data(show_spinner=False, max_entries=8)
def cached_summary(_mmm, model_key: str) -> pd.DataFrame:
    return M.channel_summary(_mmm)


@st.cache_data(show_spinner=False, max_entries=8)
def cached_quality(_mmm, model_key: str) -> dict:
    return M.fit_quality(_mmm)


@st.cache_data(show_spinner=False, max_entries=8)
def cached_fit_series(_mmm, model_key: str) -> pd.DataFrame:
    return M.fit_series(_mmm)


@st.cache_data(show_spinner=False, max_entries=8)
def cached_curves(_mmm, model_key: str) -> pd.DataFrame:
    return M.response_curves(_mmm)


@st.cache_data(show_spinner=False, max_entries=8)
def cached_model_bytes(_mmm, model_key: str) -> tuple[bytes, str]:
    return M.model_to_bytes(_mmm)


def model_download_button(key: str):
    data, ext = cached_model_bytes(st.session_state.mmm, st.session_state.model_key)
    st.download_button(
        "Download model file",
        data=data,
        file_name=f"simple_meridian_model.{ext}",
        mime="application/octet-stream",
        key=key,
        icon=":material/download:",
        on_click="ignore",
        help="Reopen this file later instead of re-fitting. Open it with the same google-meridian version.",
    )


def model_loader(key: str):
    """Upload a saved model file."""
    file = st.file_uploader(
        "Open a saved model",
        type=["binpb", "pkl"],
        key=key,
        help=".binpb files come from this app (Meridian 2.x). .pkl files from older versions may not load.",
    )
    if file is not None and st.session_state.get(f"{key}_loaded") != file.file_id:
        if file.name.lower().endswith(".pkl"):
            st.warning("`.pkl` files run code when opened. Only open model files you created yourself.")
        with st.spinner("Opening model…"):
            try:
                mmm = M.model_from_bytes(file.getvalue(), file.name)
            except Exception as e:
                st.error(f"Could not open {file.name}: {e}. Models saved with an older google-meridian "
                         "version may need to be re-fitted with this one.")
                return
        st.session_state[f"{key}_loaded"] = file.file_id
        set_model(mmm, file.name)
        st.rerun()


def require_model(step_label: str) -> bool:
    if has_model():
        return True
    st.markdown("### No model yet")
    st.markdown(f'<p class="sm-lede">{step_label} needs a fitted model. Fit one in step 1, '
                f"or open a model file you saved earlier.</p>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1.4], gap="large")
    with c1:
        if st.button("Go to step 1", type="primary", key=f"goto1_{step_label}"):
            ui.go_to("step1")
    with c2:
        model_loader(f"loader_{step_label}")
    return False
