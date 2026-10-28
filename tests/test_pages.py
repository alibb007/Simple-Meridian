"""Render every page headlessly and fail on any exception.

    python -m pytest tests -q        # or: python tests/test_pages.py
"""
import os
import sys

import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

PAGES = ["step1", "step2", "step3", "report", "geox", "help", "legal"]


def _app(page: str, demo: bool) -> AppTest:
    at = AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=180)
    at.session_state["page"] = page
    if demo:
        from app_pages.common import DEMO_MODEL_PATH, SAMPLE_PATH
        at.session_state["data"] = pd.read_csv(SAMPLE_PATH)
        at.session_state["data_name"] = "simple_dataset.csv"
        at.session_state["mmm"] = "demo"
        at.session_state["model_key"] = f"demo-{os.path.getmtime(DEMO_MODEL_PATH):.0f}"
        at.session_state["model_info"] = {"source": "demo model", "r2": 0.97}
    return at.run()


def test_pages_without_model():
    for page in PAGES:
        at = _app(page, demo=False)
        assert not at.exception, f"{page}: {at.exception}"


def test_pages_with_demo_model():
    for page in PAGES:
        at = _app(page, demo=True)
        assert not at.exception, f"{page}: {at.exception}"


def test_change_data_keeps_step1():
    """With a model but no data ("Change data" after a fit), step 1 shows the upload screen."""
    at = _app("step1", demo=True)
    at.session_state["data"] = None
    at.run()
    assert not at.exception, at.exception
    assert at.session_state["page"] == "step1"
    assert any(b.label == "Load sample data" for b in at.button)


def test_unknown_rhat_is_not_called_converged():
    at = _app("step1", demo=True)  # the demo's model_info has no max_rhat
    assert not at.exception, at.exception
    html = " ".join(m.value for m in at.markdown)
    assert "Not checked" in html and "Converged" not in html


if __name__ == "__main__":
    for t in (test_pages_without_model, test_pages_with_demo_model, test_change_data_keeps_step1,
              test_unknown_rhat_is_not_called_converged):
        t()
        print("ok", t.__name__)
