# requeststoken.org

An honest homepage for the **requests** community token on Solana. The coin is named for Kenneth Reitz’s Python library [Requests](https://github.com/psf/requests). Creator fees are directed to him. This site states what is known, marks what is not, and does not take wallets, keys, or payments.

The server is [Responder](https://github.com/kennethreitz/responder).

## Run locally

Install [uv](https://docs.astral.sh/uv/), then from this directory:

```bash
uv sync
uv run python app.py
```

Open http://127.0.0.1:5042

`uv sync` creates `.venv` from `uv.lock`. `uv run` uses that environment. The process listens on `0.0.0.0`.

Optional environment variables, in a `.env` file (loaded if present, without overriding variables you already exported) or in the environment:

| Variable | Purpose |
| --- | --- |
| `PEPY_API_KEY` | API key for [pepy.tech](https://pepy.tech/pepy-api). Sent only as the `X-API-Key` header on the server. Never put it in the page or the client. |
| `PORT` | Port to bind. Defaults to `5042`. |
| `LOG_LEVEL` | Python log level. Defaults to `INFO`. |

Copy `.env.example` to `.env` if you want the key locally.

## Download stats and the pepy.tech key

`GET /api/requests` reads the PyPI package `requests`.

- With `PEPY_API_KEY`, the server calls `https://api.pepy.tech/api/v2/projects/requests`. That response includes the all-time total and about three months of daily downloads per version. The page sums versions into one number per day. pepy.tech requires a key; a missing or rejected key is not shown to visitors.
- Without a key, or if pepy.tech fails, the server uses the public [pypistats.org](https://pypistats.org/packages/requests) API (recent totals, and daily downloads with mirrors excluded). pypistats does not publish an all-time total, so that figure is left off and the page says where the numbers came from.
- If both sources fail, the page says download stats are temporarily unavailable. A previous successful read, including one saved in `var/upstream-cache.json`, is shown instead and marked as the last saved figures.

Successful download reads are cached in memory for 15 minutes. The free pepy.tech key is limited to a handful of requests per minute, and the underlying counts are daily.

## Market figures

`GET /api/token` reads DexScreener:

`https://api.dexscreener.com/latest/dex/tokens/6ceuPfcE67PLs3Z6CbJpFpqNyAevVocP2zsDkbM1pump`

The first object in `pairs` is the one displayed. The browser asks `/api/token` again about every 30 seconds. The server reuses a successful read for 20 seconds, and if a later read fails it keeps showing the last good one.

## Tests

```bash
uv run pytest
```

The tests call the JSON routes through Responder’s in-process client. DexScreener, pepy.tech, and pypistats are replaced with scripted responses, so the suite does not use the network.

## Deploy

The container build uses uv and the lockfile. It does not install packages any other way.

```bash
docker build -t requeststoken .
docker run --rm -p 5042:5042 -e PEPY_API_KEY=... requeststoken
```

Pass `PORT` if the platform assigns one. The app binds `0.0.0.0` on that port.

`Procfile` is `web: .venv/bin/python app.py`. On a platform that expects a Procfile, install dependencies in the build step with `uv sync --frozen --no-dev`, then start from the Procfile. Set `PEPY_API_KEY` in the host environment. Do not bake the key into the image.

The cache is per process and in `var/` on local disk. More than one worker means more than one cache.

## Facts left open

These are marked **TODO** on the page. They were not filled in, because they were not provided:

- A locker address or transaction for Kenneth’s holding (about 11% of supply, locked until February 14, 2027), so the lock can be checked on chain.
- Which accounts he considers official. The footer links Kenneth Reitz on X (`https://x.com/kennethreitz42`). Other X accounts listed on the token's DexScreener page are filtered out (`BLOCKED_HANDLES` in `requeststoken/config.py`); one of them is a known bad actor and is not official.
- A plain description of how creator fees move, beyond the fact that they are directed to Kenneth Reitz.
- DexScreener also lists `https://requeststoken.com/` as a website. This project does not treat that address as an official link until it is confirmed.

There is no roadmap on this page.

## Fonts

Fraunces, Outfit, and IBM Plex Mono are self-hosted Latin subsets under the SIL Open Font License. The license texts are in `static/fonts/`.
