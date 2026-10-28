import streamlit as st

from utils import tour, ui

GLOSSARY = [
    ("Marketing mix model (MMM)", "A statistical model that looks at weekly sales and weekly ad spend over a few years "
                                  "and works out how much of the sales each channel caused."),
    ("Google Meridian", "Google's free, open-source MMM. Simple Meridian runs it for you, so you don't need Python."),
    ("Channel", "A place you spend money on ads: TV, radio, search, social, email and so on."),
    ("Baseline", "Sales you would get with no ads at all: loyal customers, word of mouth, season."),
    ("Incremental revenue", "Sales that happened because of a channel, on top of the baseline."),
    ("ROI", "Incremental revenue divided by spend. An ROI of 2.5 means each $1 brought back $2.50."),
    ("Marginal ROI", "What the next $1 would bring back. It drops as a channel saturates."),
    ("Response curve", "Sales a channel brings at different spend levels. Flat means more money buys little."),
    ("Carryover", "An ad keeps working for days or weeks after it runs. Meridian models this."),
    ("Saturation", "Each extra dollar on a channel buys less than the one before."),
    ("Credible interval (90% range)", "The range the true value is very likely in. Narrow means the model is sure."),
    ("R²", "How much of the week-to-week movement in sales the model explains. 1.0 is perfect."),
    ("R-hat", "A check that the model finished learning. Below 1.2 is good; above it, fit again with more samples."),
    ("Lift test (GeoX)", "An experiment: ads run in some regions and not others, and the gap is measured. "
                         "See the GeoX (Lift test) page."),
    ("Prior", "What the model believes before it sees your data. A lift test result makes a much better prior."),
]

FAQ = [
    ("Do I need to know statistics?", "No. Take the guided tour, then load your own spreadsheet. Every chart has a "
                                      "plain-language caption."),
    ("What data do I need?", "One row per week with no gaps (two to three years is ideal): a date, your sales or "
                             "revenue, and spend for each channel. Impressions or clicks per channel help."),
    ("Is my data sent anywhere?", "No. The model runs on the machine that hosts this app."),
    ("How long does a fit take?", "About a minute on a laptop for the sample data. Larger data takes longer."),
    ("Can I trust the numbers?", "Check Model fit (R² and R-hat) and how wide the ROI ranges are. "
                                 "The best check is a lift test, which you can add as a prior."),
]


def show_help():
    st.markdown(f'<div class="sm-head">{ui.badge("help", "amber", 52)}<div><div class="sm-kicker">New here?</div>'
                f"<h1>Help &amp; glossary</h1></div></div>", unsafe_allow_html=True)
    st.markdown('<p class="sm-lede">Every term the app uses, in plain words. Or let the guided tour walk you '
                "through the demo step by step.</p>", unsafe_allow_html=True)
    if st.button("Start the guided tour", type="primary", icon=":material/tour:", key="help_tour"):
        tour.start()

    st.markdown("### Words you'll see")
    cols = st.columns(3, gap="medium")
    for i, (term, text) in enumerate(GLOSSARY):
        with cols[i % 3]:
            st.markdown(f'<div class="sm-tile" style="margin-bottom:.7rem;min-height:118px"><div>'
                        f'<div style="font-weight:700">{term}</div><div class="d" style="font-size:.9rem">{text}</div>'
                        f"</div></div>", unsafe_allow_html=True)

    st.markdown("### Learn more from Google")
    st.markdown(
        "- [Google Meridian: official site and documentation](https://developers.google.com/meridian)\n"
        "- [Meridian on GitHub](https://github.com/google/meridian)\n"
        "- [Meridian GeoX: lift tests](https://developers.google.com/meridian/geox)\n"
        "- [Using past experiments as priors](https://developers.google.com/meridian/docs/advanced-modeling/set-custom-priors-past-experiments)"
    )

    st.markdown("### Common questions")
    for q, a in FAQ:
        with st.expander(q, icon=":material/help:"):
            st.markdown(a)
