# Security policy

## Reporting a problem

Please do **not** open a public issue for security problems. Email ali.barfib@gmail.com with:

- what you found and how to reproduce it,
- the version (commit or release) you tested,
- any proof-of-concept files, if you have them.

You should get a reply within 7 days. Fixes are released as soon as they are ready, and you will be credited unless you ask not to be.

## How the app is hardened

- **Runs locally by default.** `docker compose up` and the start scripts publish the app on `127.0.0.1` only, so other machines on your network cannot reach it.
- **Non-root container.** The image runs as user `app` (UID 1000) with a health check.
- **No pickle by default.** Legacy `.pkl` model files can execute code when loaded, so they are refused unless the operator sets `ALLOW_PICKLE_MODELS=1`. Models are saved in Meridian's `.binpb` (protobuf) format instead.
- **Escaped output.** Column and region names from uploaded files are HTML-escaped before they are placed in page markup.
- **Streamlit settings** (`.streamlit/config.toml`): XSRF protection on, CORS checks on, 50 MB upload cap, usage statistics off, and error pages show only the error type, not stack traces.
- **Bounded compute.** At most `MAX_CONCURRENT_FITS` (default 1) model fits or lift tests run at once; others wait in a queue.
- **No secrets.** The app needs no API keys or credentials, and none are stored in the repository or image.

## If you host it for other people

- Put it behind HTTPS (a reverse proxy such as Caddy or a platform that terminates TLS).
- Add authentication if the data is confidential; Streamlit has no login of its own.
- Keep `ALLOW_PICKLE_MODELS` unset.
- Rebuild the image regularly to pick up security fixes in the base image and dependencies.
