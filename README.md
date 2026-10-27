<div align="center">

<img src="pic/brand-mark.png" alt="" width="72">

# Simple Meridian

**A no-code app for Google Meridian, the open-source marketing mix model.**
Upload weekly spend and sales, and get channel ROI, response curves and a budget plan without writing code.

[![Google Meridian 2.1.0](https://img.shields.io/badge/google--meridian-2.1.0-2A78D6)](https://pypi.org/project/google-meridian/)
[![Python 3.12](https://img.shields.io/badge/python-3.12-15202B?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit 1.66](https://img.shields.io/badge/streamlit-1.66-D23F2A?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Docker](https://img.shields.io/badge/docker-ready-2E6B55?logo=docker&logoColor=white)](#run-with-docker)
[![License: MIT](https://img.shields.io/badge/license-MIT-5A6872)](LICENSE)

<img src="pic/home.png" alt="Simple Meridian home page" width="92%">

</div>

---

## What it does

Marketing mix modeling (MMM) estimates how much revenue each channel produced, using only weekly totals. No user tracking or cookies are involved. [Meridian](https://github.com/google/meridian) is Google's Bayesian MMM. It handles carryover (an ad keeps working for weeks after it runs) and saturation (each extra dollar buys less than the one before). Running it normally takes a notebook and a fair amount of Python. This app handles data loading, sampling, analysis and reports through a point-and-click interface.

| Step | What you do | What you get |
|---|---|---|
| **1 · Data & model** | Upload a CSV or Excel file. Confirm the date, outcome and channel columns (they are detected automatically). Pick a sampling preset. | A fitted Meridian model, fit quality (R², MAPE, R-hat), and a model file you can download and reopen later. |
| **2 · Insights** | Look through the tabs. | ROI with 90% credible intervals, average vs. marginal ROI, baseline vs. media revenue, share of spend vs. share of revenue, response curves, actual vs. predicted, and Meridian's HTML report. |
| **3 · Budget plan** | Pick a period, a per-channel limit (±30% by default), and keep the budget or set a new total. | The spend split with the most incremental revenue, where it lands on each response curve, and CSV, Excel and HTML exports. |

Everything runs on your machine. Your data is not sent anywhere.

<table>
  <tr>
    <td width="50%"><img src="pic/app.png" alt="Insights: ROI by channel with 90% credible intervals"></td>
    <td width="50%"><img src="pic/budget-plan.png" alt="Budget plan: actual vs. optimized budget mix"></td>
  </tr>
  <tr>
    <td align="center"><sub>Insights: ROI by channel, with uncertainty</sub></td>
    <td align="center"><sub>Budget plan: actual vs. optimized budget mix</sub></td>
  </tr>
</table>

## Quick start

### Run with Docker

```bash
git clone https://github.com/alibb007/Simple-Meridian.git
cd Simple-Meridian
docker build -t simple-meridian .
docker run --rm -p 8501:8501 simple-meridian
```

Then open <http://localhost:8501>. The image is about 4 GB because Meridian depends on TensorFlow and JAX, so the first build takes a few minutes.

### Run with Python

Python 3.11 or newer is required. 3.12 is what the app is tested on.

```bash
git clone https://github.com/alibb007/Simple-Meridian.git
cd Simple-Meridian
python3.12 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Click **Try the sample data** on the home page to see the full flow on a three-year synthetic dataset with six channels.

## Data format

One row per week, one column per measure:

| week | tv_spend | tv_impressions | search_spend | search_clicks | price_index | sales |
|---|---|---|---|---|---|---|
| 2024-01-07 | 81200 | 9100000 | 22400 | 41000 | 1.02 | 612400 |
| 2024-01-14 | 77950 | 8700000 | 23100 | 43900 | 1.02 | 598100 |

- **Dates**: weekly, evenly spaced, with no gaps or repeats. Any common date format works. Two to three years of data gives much more stable estimates than one.
- **Outcome**: revenue, or conversions. For conversions you can add a revenue-per-conversion column so ROI comes out in currency.
- **Channels**: spend for every paid channel, plus impressions, clicks or GRPs for the same channel. Columns named `<channel>_spend` and `<channel>_impression(s)` are paired automatically. If a channel only has spend, use the spend column for both.
- **Controls** (optional): price, promotions, seasonality, competitor activity, market trends. Anything that moves sales but is not paid media.

The app checks the data before fitting. Gaps, repeated dates, empty cells, negative spend and constant controls are reported in plain language.

A sample file is in [`data/simple_dataset.csv`](data/simple_dataset.csv).

## Sampling presets

Meridian estimates the model with MCMC sampling. More samples take longer and give tighter, more reliable estimates.

| Preset | Chains | Adapt / burn-in / keep | Typical time* | Use it for |
|---|---|---|---|---|
| Quick check | 2 | 300 / 300 / 250 | ~1 min | Checking your setup |
| Standard | 4 | 500 / 500 / 500 | a few min | Numbers you plan to act on |
| Thorough | 4 | 1000 / 1000 / 1000 | 10+ min | Final reads, borderline convergence |

\* Six channels and 156 weeks on a recent laptop CPU. Time grows with the number of channels and weeks.

Under **Advanced** you can set the maximum carryover (default 8 weeks) and the random seed. The same seed with the same data gives the same result.

If max R-hat on the **Model fit** tab is above 1.2, the chains have not agreed yet. Fit again with a longer preset before trusting the numbers.

## Saving and reopening models

**Download model file** saves the model in Meridian's protobuf format (`.binpb`, via `meridian.schema.serde`). Open it again from step 1, 2 or 3 to skip re-fitting. Open it with the same `google-meridian` version that saved it.

`.pkl` files from older versions of this app (Meridian 1.0.x) can still be opened, but they usually fail under Meridian 2.x. Re-fit those models. Pickle files can run code when opened, so only open ones you made yourself.

## Project layout

```
app.py                         entry point: page setup, sidebar, routing
app_pages/
  home.py                      overview page
  step1_upload_and_run.py      upload, column mapping, validation, fitting
  step2_insights.py            ROI, contribution, response curves, fit, report
  step3_optimization.py        budget optimizer and exports
  common.py                    shared state, caching, model upload/download
utils/
  mmm.py                       all Meridian calls; returns plain pandas tables
  charts.py                    Plotly charts
  ui.py                        theme, CSS, sidebar navigation, small components
.streamlit/config.toml         theme
data/simple_dataset.csv        sample data
```

`utils/mmm.py` is the only file that imports Meridian. If a future Meridian release changes its API, that is the one file to update.

## What changed in this version

- Upgraded from `google-meridian` 1.0.6 to **2.1.0** (TensorFlow 2.21, JAX backend). Ported the app to the 2.x API: `DataFrameDataLoader`, `start_date`/`end_date` in the optimizer, and the new report signatures.
- Models are now saved as `.binpb` with Meridian's serializer, replacing the deprecated pickle format.
- Redesigned the interface: navigation sidebar, icons, and one color per channel across every chart. Channels are set up as spend + exposure pairs, data is checked before fitting, sampling has presets, and all charts are interactive with uncertainty ranges.
- Model and optimization results are kept in session state, so they stay on screen while you use other controls.
- Removed calls to `st.experimental_rerun`, which current Streamlit no longer has.
- Docker image runs on Python 3.12 as a non-root user, with a health check.

## Troubleshooting

- **The fit is slow.** Start with **Quick check**. Fewer channels and fewer weeks also help. Docker Desktop on macOS gets fewer CPUs than the host by default; raise the limit under Settings → Resources.
- **"Dates are not evenly spaced."** Meridian needs one row per period with no gaps. Fill missing weeks with zeros for spend and the real outcome value.
- **ROI intervals are very wide.** The data cannot separate that channel from the others, often because its spend barely changes or moves in step with another channel. Longer history or more spend variation helps.
- **Port 8501 is taken.** Use `docker run -p 8502:8501 simple-meridian` and open <http://localhost:8502>.

## Credits

Built by **Ali Barfi Bafghi** · [GitHub](https://github.com/alibb007) · [LinkedIn](https://www.linkedin.com/in/alibarfibafghi/) · [Email](mailto:ali.barfib@gmail.com)

Simple Meridian is an independent project. It uses the open-source [Google Meridian](https://github.com/google/meridian) library (Apache 2.0) and is not affiliated with or endorsed by Google. Meridian is a trademark of Google LLC.

Released under the [MIT License](LICENSE).
