"""Constants for the requests token site. Facts live here once."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DISK_CACHE = ROOT / "var" / "upstream-cache.json"

CONTRACT = "6ceuPfcE67PLs3Z6CbJpFpqNyAevVocP2zsDkbM1pump"
PACKAGE = "requests"

DEX_API = f"https://api.dexscreener.com/latest/dex/tokens/{CONTRACT}"
DEX_PAGE = f"https://dexscreener.com/solana/{CONTRACT}"
PUMP_PAGE = f"https://pump.fun/coin/{CONTRACT}"

PEPY_API = f"https://api.pepy.tech/api/v2/projects/{PACKAGE}"
PEPY_PAGE = f"https://pepy.tech/projects/{PACKAGE}"

PYPI_PAGE = f"https://pypi.org/project/{PACKAGE}/"
PYPI_RECENT = f"https://pypistats.org/api/packages/{PACKAGE}/recent"
PYPI_OVERALL = f"https://pypistats.org/api/packages/{PACKAGE}/overall"
PYPISTATS_PAGE = f"https://pypistats.org/packages/{PACKAGE}"

DOCS_PAGE = "https://requests.readthedocs.io/"
SOURCE_PAGE = "https://github.com/psf/requests"

USER_AGENT = "requeststoken.org/1.0 (+https://requeststoken.org)"

# Successful DexScreener reads are reused for a little under the 30s poll.
TOKEN_TTL = 20
TOKEN_ERROR_TTL = 15
# Download totals move on a daily cadence, and pepy.tech's free key is 5 RPM.
STATS_TTL = 15 * 60
STATS_ERROR_TTL = 60

PRIMARY_LINKS = (
    {
        "label": "This website",
        "href": "https://requeststoken.org/",
        "note": "The page you are on",
    },
    {
        "label": "DexScreener",
        "href": DEX_PAGE,
        "note": "Market pair for this contract",
    },
    {
        "label": "pump.fun",
        "href": PUMP_PAGE,
        "note": "Token page for this contract",
    },
    {
        "label": "Requests on PyPI",
        "href": PYPI_PAGE,
        "note": "The library, not the token",
    },
    {
        "label": "Requests documentation",
        "href": DOCS_PAGE,
        "note": "The library",
    },
    {
        "label": "Requests source",
        "href": SOURCE_PAGE,
        "note": "github.com/psf/requests",
    },
    {
        "label": "pepy.tech",
        "href": PEPY_PAGE,
        "note": "Download counts for the library",
    },
    {
        "label": "pypistats.org",
        "href": PYPISTATS_PAGE,
        "note": "Public PyPI download statistics",
    },
)

# Published on the token's DexScreener profile. Confirm before treating
# them as canonical; they are labeled that way on the page.
PROFILE_LINKS = (
    {
        "label": "Kenneth Reitz on X",
        "href": "https://x.com/kennethreitz42",
        "note": "Published on the token's DexScreener profile",
    },
    {
        "label": "@RequestsToken on X",
        "href": "https://x.com/RequestsToken",
        "note": "Published on the token's DexScreener profile",
    },
)
