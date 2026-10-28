# Changelog

What changed in Simple Meridian, newest first. The [README](README.md#whats-new) has the short version.

## 28 Oct 2026

- **Guided tour story, rewritten.** Seven scenes on a made-up shop: the team guesses, the boss asks where next year's budget should go, they run Google Meridian, the answers come back, they move the money, and it ends with "Now it's your turn to try it." Meridian's answers are shown as the questions it can answer.
- **Budget scene shows the change in %.** Each channel's bar is its budget change with the plan (Email +31%, Radio +30%, Display −30%), so a small channel that grows a lot no longer looks like a sliver next to TV.
- **Files reorganized.** Images moved from `pic/` to `assets/` (screenshots in `assets/screenshots/`). The demo build scripts moved to `scripts/demo/`. The website's build scripts moved out of `docs/` into `scripts/site/`, with a new `publish.sh` that stamps the site's file links and copies `docs/` to the demo repository. `docs/` now holds only the website.
- **New README** with an animated overview, a before-and-after table and fold-out sections.
- **Visit counts on the guided tour site.** The site now loads [GoatCounter](https://www.goatcounter.com/), which counts visits, tour steps reached, and clicks on the start buttons and outside links. GoatCounter sets no cookies and never saves IP addresses. The script is pinned to version 5 with an integrity hash, and the site's security rules allow only that script and the counter's address.
- **Curve charts fit their card.** Meridian draws its response curves three across at 400 px each, about 1,600 px wide, so they ran past the card. Each channel now gets its own chart, two per row, sized to the card, with one caption that explains the line styles and marks.
- **Welcome screen.** The story button is now on the left and reads "See it as a story first"; the guided tour button is on the right.
- **Fixes from a code review.** "Change data" after a fit opens the upload screen again instead of jumping to Insights. A lift test with no positive return no longer offers a broken ROI prior. Lift-test files with bad dates or text in number columns now get a plain error message, and old results no longer show under a new file. Monthly data passes the date check. An R-hat that could not be computed shows "Not checked" instead of "Converged". The donut chart shows totals under $1M correctly. New checks live in `tests/test_logic.py`.

## 27 Oct 2026, Meridian 2.1.0

- Upgraded from `google-meridian` 1.0.6 to **2.1.0** (TensorFlow 2.21, JAX backend). Ported the app to the 2.x API: `DataFrameDataLoader`, `start_date`/`end_date` in the optimizer, and the new report signatures.
- Added a Help & glossary page, and a guided tour website for people new to MMM.
- Added **lift tests with Meridian GeoX 1.0.1**: design a geo experiment, measure it, and use the result as an ROI prior.
- Added a demo: a pre-fitted model with precomputed charts, so you can see the results without fitting anything.
- The guided tour lives on its own website. It spotlights each part it explains and dims the rest, with a caption right above that part. It opens with a short animated story, then walks through upload, the model run, every chart from Meridian's own report, the budget plan and GeoX. The app itself opens on the upload screen.
- New **Meridian charts** page: the 12 model charts and 4 budget-plan charts from Meridian's HTML report, drawn by Meridian, each with "what it shows" and "how to read it" in plain words.
- Step 1 now runs in order (data, time and outcome, channels, controls, fit), with channel cards you can rename, re-map, add and remove.
- Budget plan period: latest 52 weeks, last full calendar year, full history, or custom dates from an in-app calendar.
- Privacy & terms page, SECURITY.md and THIRD_PARTY_NOTICES.md; pickle model files are off by default; uploads capped at 50 MB.
- Local edition for macOS and Windows (`start.sh`, `start.bat`, `docker-compose.yml`) and a static live demo in `docs/`.
- Faster: Meridian loads in the background instead of on the first page load (page import went from 7.1 s to 0.5 s), optimizer results are cached, and the JAX backend is pinned.
- Models are saved as `.binpb` with Meridian's serializer, replacing the deprecated pickle format.
- Redesigned the interface: an upload screen with three starting points, a navigation sidebar, icons, pill tabs, and one color per channel across every chart. Step 1 now has numbered sections and a "Ready to fit" checklist; data is checked before fitting.
- Budget plan supports a new total budget as well as the same budget, with per-channel limits.
- Docker image went from 3.82 GB to 2.62 GB by dropping C++ headers, test suites, libclang and debug symbols. It runs on Python 3.12 as a non-root user, with a health check.

## April 2025, Meridian 1.0.6

- First release ([browse the code](https://github.com/alibb007/Simple-Meridian/tree/5438c16)): upload data, map columns, fit Meridian, view its charts, and run the budget optimizer.
