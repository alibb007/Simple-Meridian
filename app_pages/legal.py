import streamlit as st

from utils import ui
from utils.geox import GEOX_VERSION
from utils.mmm import MERIDIAN_VERSION

THIRD_PARTY = [
    ("Google Meridian", MERIDIAN_VERSION or "2.1.0", "Apache-2.0", "https://github.com/google/meridian"),
    ("Meridian GeoX", GEOX_VERSION or "1.0.1", "Apache-2.0", "https://github.com/google/meridian-geox"),
    ("TensorFlow / TensorFlow Probability", "2.21 / 0.26", "Apache-2.0", "https://www.tensorflow.org"),
    ("JAX", "0.12", "Apache-2.0", "https://github.com/jax-ml/jax"),
    ("Streamlit", "1.66", "Apache-2.0", "https://streamlit.io"),
    ("Plotly", "7.1", "MIT", "https://plotly.com/python/"),
    ("pandas, NumPy, SciPy, statsmodels, Altair", "", "BSD-3-Clause", "https://pandas.pydata.org"),
    ("Material Symbols (icons)", "", "Apache-2.0", "https://fonts.google.com/icons"),
    ("Red Hat Display / Text (fonts)", "", "SIL Open Font License 1.1", "https://github.com/RedHatOfficial/RedHatFont"),
]


def show_legal():
    st.markdown(f'<div class="sm-head">{ui.badge("shield", "green", 52)}<div><div class="sm-kicker">Trust</div>'
                f"<h1>Privacy &amp; terms</h1></div></div>", unsafe_allow_html=True)
    st.markdown('<p class="sm-lede">Plain-language summary. This is not legal advice; if you run Simple Meridian for '
                "a business, have your own counsel review it.</p>", unsafe_allow_html=True)

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        ui.card("Your data", """
            <ul>
              <li>Files you upload are processed <b>in memory on the machine running this app</b> (your computer, if
              you use the Docker version). The app does not write them to disk or send them to us or to Google.</li>
              <li>When your session ends, your data and models are dropped. Charts computed from them can stay in the
              server's memory cache for up to one hour, then they expire.</li>
              <li>Upload <b>aggregate</b> weekly or daily totals only. Do not upload personal data such as names,
              emails or customer IDs. Marketing mix models never need it.</li>
              <li>Usage statistics to Streamlit are switched off. Page fonts and icons are loaded from Google Fonts,
              which receives the visitor's IP address like any web request.</li>
            </ul>""", "lock", "green")
    with c2:
        ui.card("What the results are", """
            <ul>
              <li>ROI, contribution, budget plans and lift-test results are <b>statistical estimates</b> with
              uncertainty ranges, not guarantees. They are not financial, legal or investment advice.</li>
              <li>The sample data and the demo company are made up. Do not use the demo numbers for decisions.</li>
              <li>Make big budget changes in stages and check results, ideally with a real lift test.</li>
            </ul>""", "info", "amber")

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        ui.card("License and warranty", """
            <p>Simple Meridian is released under the <b>MIT License</b>. It is provided "as is", without warranty of
            any kind, and the authors are not liable for any claim or damages arising from its use. See the LICENSE
            file in the repository.</p>""", "gavel", "violet")
    with c2:
        ui.card("Trademarks", """
            <p>Simple Meridian is an independent project by Ali Barfi Bafghi. It is <b>not affiliated with, sponsored
            by or endorsed by Google</b>. Google, Meridian and GeoX are trademarks of Google LLC, used here only to
            name the open-source libraries the app runs on.</p>""", "verified", "blue")

    st.markdown("### Security")
    st.markdown(
        "- The Docker image runs as a non-root user, and the start scripts expose the app on `localhost` only.\n"
        "- Text from uploaded files (column and region names) is escaped before it is placed in page HTML.\n"
        "- Model files are opened in Meridian's `.binpb` format. Legacy `.pkl` files can run code when opened, so "
        "they are refused unless the person running the server sets `ALLOW_PICKLE_MODELS=1`.\n"
        "- Cross-site request forgery protection is on and uploads are capped at 50 MB.\n"
        "- Found a problem? Please report it privately as described in `SECURITY.md` in the repository."
    )

    st.markdown("### Open-source components")
    rows = "".join(
        f'<tr><td><a href="{url}" target="_blank" rel="noopener">{name}</a></td><td>{ver}</td><td>{lic}</td></tr>'
        for name, ver, lic, url in THIRD_PARTY
    )
    st.markdown(f'<table style="width:100%;font-size:.9rem"><tr style="font-weight:700"><td>Component</td>'
                f"<td>Version</td><td>License</td></tr>{rows}</table>", unsafe_allow_html=True)
    st.caption("Full list with license texts: THIRD_PARTY_NOTICES.md in the repository.")
