# Third-party notices

Simple Meridian is MIT-licensed (see `LICENSE`). It depends on the open-source components below, each under its own license. Versions are those pinned in `requirements.txt` or resolved by it on 27 Oct 2026.

| Component | Version | License | Source |
|---|---|---|---|
| Google Meridian (`google-meridian[schema]`) | 2.1.0 | Apache-2.0 | https://github.com/google/meridian |
| Meridian GeoX (`meridian-geox`) | 1.0.1 | Apache-2.0 | https://github.com/google/meridian-geox |
| mmm-proto-schema | 1.6.0 | Apache-2.0 | installed with `google-meridian[schema]` |
| TensorFlow | 2.21.0 | Apache-2.0 | https://github.com/tensorflow/tensorflow |
| TensorFlow Probability (tfp-nightly) | 0.26.0.dev20260130 | Apache-2.0 | https://github.com/tensorflow/probability |
| JAX / jaxlib | 0.12.0.1 | Apache-2.0 | https://github.com/jax-ml/jax |
| ArviZ | 0.19.0 | Apache-2.0 | https://github.com/arviz-devs/arviz |
| xarray | 2026.9.0 | Apache-2.0 | https://github.com/pydata/xarray |
| Streamlit | 1.66.1 | Apache-2.0 | https://github.com/streamlit/streamlit |
| Plotly | 7.1.0 | MIT | https://github.com/plotly/plotly.py |
| Altair | 6.3.0 | BSD-3-Clause | https://github.com/vega/altair |
| pandas | 2.3.3 | BSD-3-Clause | https://github.com/pandas-dev/pandas |
| NumPy | 2.3.5 | BSD-3-Clause | https://github.com/numpy/numpy |
| SciPy | 1.18.1 | BSD-3-Clause | https://github.com/scipy/scipy |
| statsmodels | 0.14.6 | BSD-3-Clause | https://github.com/statsmodels/statsmodels |
| tslearn | 0.10.0 | BSD-2-Clause | https://github.com/tslearn-team/tslearn |
| seaborn | 0.13.2 | BSD-3-Clause | https://github.com/mwaskom/seaborn |
| pandera | 0.35.0 | MIT | https://github.com/unionai-oss/pandera |
| openpyxl | 3.1.5 | MIT | https://foss.heptapod.net/openpyxl/openpyxl |
| XlsxWriter | 3.3.0 | BSD-2-Clause | https://github.com/jmcnamara/XlsxWriter |
| Material Symbols (icons, loaded by Streamlit) | | Apache-2.0 | https://github.com/google/material-design-icons |
| Red Hat Display / Text / Mono (fonts, served from `static/fonts/`, via @fontsource) | 5.3.0 | SIL Open Font License 1.1 | https://github.com/RedHatOfficial/RedHatFont |
| Vega (live demo site, `docs/assets/vendor/`) | 6.2.0 | BSD-3-Clause | https://github.com/vega/vega |
| Vega-Lite (live demo site) | 6.4.1 | BSD-3-Clause | https://github.com/vega/vega-lite |
| vega-embed (live demo site) | 7.0.2 | BSD-3-Clause | https://github.com/vega/vega-embed |
| vega-interpreter (live demo site) | 2.2.1 | BSD-3-Clause | https://github.com/vega/vega |

Licenses were read from each package's installed metadata. The Apache-2.0 components ask that their license and NOTICE files travel with redistributed copies; the Docker image keeps every package's installed `*.dist-info` folder, where pip places those files.

"Google", "Meridian" and "GeoX" are trademarks of Google LLC. Simple Meridian is not affiliated with or endorsed by Google.
