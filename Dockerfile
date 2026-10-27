FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TF_CPP_MIN_LOG_LEVEL=2 \
    # JAX fits the sample model ~2.8x faster than the TensorFlow backend.
    MERIDIAN_BACKEND=jax

WORKDIR /app

# Install, then in the same layer drop what nothing needs at runtime: C++
# headers, test suites, libclang, and debug symbols in native libraries
# (TensorFlow ships unstripped). Saves ~1.1 GB.
COPY requirements.txt .
RUN pip install -r requirements.txt \
 && SP="$(python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')" \
 && find "$SP" -type d -name include -prune -exec rm -rf {} + \
 && find "$SP" -type d \( -name tests -o -name test \) -prune -exec rm -rf {} + \
 && rm -rf "$SP/clang" "$SP"/libclang-*.dist-info \
 && apt-get update && apt-get install -y --no-install-recommends binutils \
 && find "$SP" -name "*.so*" -type f -exec strip --strip-unneeded {} + \
 && apt-get purge -y binutils && apt-get autoremove -y && rm -rf /var/lib/apt/lists/* \
 && python -c "import meridian.analysis.analyzer, meridian.schema.serde.meridian_serde, streamlit"

COPY --chown=1000:1000 . .
RUN useradd --uid 1000 --create-home app
USER app

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
