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

PAGES = ["home", "step1", "step2", "step3", "geox", "help"]


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


def test_tour_renders_on_every_step():
    from utils import tour
    for i, step in enumerate(tour.steps()):
        at = AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=180)
        at.session_state["page"] = step["page"]
        at.session_state["tour"] = i
        at.run()
        assert not at.exception, f"tour step {i}: {at.exception}"


if __name__ == "__main__":
    for t in (test_pages_without_model, test_pages_with_demo_model, test_tour_renders_on_every_step):
        t()
        print("ok", t.__name__)
