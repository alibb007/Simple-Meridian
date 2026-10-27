"""Simple Meridian: a no-code Streamlit front end for Google Meridian."""
import streamlit as st

st.set_page_config(
    page_title="Simple Meridian",
    page_icon="pic/favicon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

from app_pages.home import show_home  # noqa: E402
from app_pages.step1_upload_and_run import show_upload_and_run  # noqa: E402
from app_pages.step2_insights import show_insights  # noqa: E402
from app_pages.step3_optimization import show_optimization  # noqa: E402
from utils import ui  # noqa: E402
from utils.mmm import MERIDIAN_VERSION  # noqa: E402

DEFAULTS = {
    "page": "home",
    "data": None,
    "data_name": None,
    "mmm": None,
    "model_key": None,
    "model_info": None,
    "optimization": None,
    "visited_insights": False,
}
for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, value)

PAGES = {
    "home": show_home,
    "step1": show_upload_and_run,
    "step2": show_insights,
    "step3": show_optimization,
}


def main():
    ui.inject_css()
    ui.sidebar(MERIDIAN_VERSION)
    if MERIDIAN_VERSION is None:
        st.error("google-meridian is not installed. Run `pip install -r requirements.txt` and restart the app.")
    PAGES.get(st.session_state.page, show_home)()
    ui.footer()


main()
