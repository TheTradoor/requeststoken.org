# Requests observatory

The observatory is a library download-history and public-project evidence page.
It runs in the existing Responder application and needs no additional production
dependency, API key, Google Cloud account or frontend build step. Realtime event
collection remains deferred; `requests-intraday-proof.sql` is an unexecuted
candidate query for that separate work.

## Routes and files

| Path | Purpose |
| --- | --- |
| `/observatory` | Server-rendered page with interactive counters, archive and project directory |
| `/api/observatory` | Shared source snapshot, cache status and timestamps |
| `requeststoken/observatory.py` | Source queries/validation, SQLite snapshot, refresh lease and error backoff |
| `static/js/observatory-stats.mjs` | Calendar periods, gap-preserving history and CSV |
| `static/js/observatory.mjs` | Charts, controls, source status and accessible project dialogs |
| `static/observatory/adoption-evidence.json` | Reviewed project manifest and downloadable evidence |
| `static/observatory/download-snapshot.json` | Fixed, dated fallback audit |
| `static/observatory/download-proof-2026-10-25.zip` | Original SQL, raw responses, CSV and integrity hashes |
| `var/observatory.sqlite` | Runtime cache and daily source-check history; not committed |

The existing homepage, `/api/token`, and `/api/requests` keep their current
contracts. The latter uses pypistats with mirrors excluded and reported rolling
windows. Its metrics must not be silently combined with the observatory's
ClickHouse raw/aggregate counts and UTC calendar windows.

## Current source and audited baseline

The public endpoint is `https://sql-clickhouse.clickhouse.com/`, using its
documented public username `demo`. It is not a secret. SQL is generated
server-side for the fixed package `requests`; callers cannot supply SQL.

- Daily history: `SUM(count)` grouped by date from `pypi.pypi_downloads_per_day`.
- Historical/latest raw counts: `COUNT()` from `pypi.pypi`.
- Overflow modes are `throw`, so a public-service limit fails instead of silently
  returning a truncated count. Unexpected row counts and malformed/regressed
  histories also fail validation.

The bundled audit was fetched **2026-10-25 00:51:08 UTC** and ends on
**2026-10-24 UTC**. It contains **34,524,196** raw records for the latest date,
**39,530,831,689** historical raw records from **2016-01-22**, and **3,850**
reported dates with **79** missing dates. The daily aggregate sum is
**39,532,848,966**, exceeding the raw baseline by **2,017,277**. The UI computes
and discloses this difference for each snapshot.

This historical total is not a verified count since Requests' first release.
Downloads are not unique users, completed installs, or identifiable company
activity. Repeated CI jobs and partial transfers can contribute records. Historic
metric definitions changed; the original baseline was not backfilled with the
candidate distribution-filename filter in the BigQuery proof query.

References:

- [PyPI download dataset](https://docs.pypi.org/api/bigquery/)
- [ClickPy ingestion and daily exports](https://clickhouse.com/blog/clickpy-2-trillion-rows)
- [PyPI count-definition changes](https://blog.pypi.org/posts/2026-08-31-download-counts/)

## Refresh and storage behavior

Requests return an existing snapshot immediately. When a refresh is due, a
SQLite transaction obtains a 120-second lease and submits one background job.
The job performs bounded HTTP source queries, validates the results, and replaces
the snapshot atomically. A unique lease token prevents an expired worker from
overwriting a newer worker's result. Successful checks wait an hour; failures
retain the last snapshot and wait ten minutes. No visit means no refresh, and
there is no separate scheduler or realtime collector.

The browser rechecks every five minutes while visible, on returning to the tab,
or on manual refresh. While a shared job is running, it checks its status every
ten seconds. It reads the shared cache, not a separate upstream query per visitor.

SQLite coordinates workers that share the same database file. Separate hosts
or containers with different storage have independent caches and leases. Persist
`var/` across redeployments; for multiple hosts, choose an appropriate shared
collector/database before scaling this refresh design. The existing deployment
files are not changed to provision infrastructure automatically.

`REQUESTS_OBSERVATORY_REFRESH=0` disables upstream attempts for offline review.
A missing/unwritable database or network failure leaves the saved audit visible
with a warning. An import/client/proxy configuration failure is handled inside
the background job; it does not prevent the rest of the page from rendering.

## API and time semantics

The JSON response contains `snapshot`, `status`, `checkedAt`, `serverTime`,
`refreshing`, and `message`. Snapshot fields are `package`, `firstDate`,
`latestDate`, `rawTotal`, `rawLatest`, `fetchedAt`, `source`, `queries`, and an
ascending array of `{date, downloads}` daily records.

- `status: current` means a source request succeeded, not that ingestion is realtime.
- `cached` indicates a failed subsequent check; `fallback` indicates the saved audit/cache fallback.
- `fetchedAt` belongs to the retained data. `checkedAt` may describe a later failed attempt.
- `latestDate` is the newest represented calendar day, not an event-time watermark.
- `serverTime` lets the client align UTC calendar boundaries with the server clock.

Daily periods start at 00:00 UTC; weekly periods start Monday; calendar months
start on the first. A newly opened period with no rows displays Pending. An
explicit source-reported zero remains zero. Open periods are partial and missing
historic dates remain unknown. Corrections can decrease totals. Countdown ticks
never add downloads, and the historical total never resets.

Date filters select overlapping calendar periods. A weekly/monthly row always
shows that whole period's available count, even when the chosen filter begins
mid-period. CSV includes coverage and status columns; missing values are blank.
The chart breaks its line at missing periods rather than drawing zeros.

## Project evidence and maintenance

The manifest contains 120 projects: 84 technology/enterprise and 36 crypto/Web3,
across 116 distinct organization/community labels. These labels are not a count
of corporate parents. Each entry has its usage explanation, three-step flow,
scope note, immutable revision, source lines, reviewed timestamp and integrity
hashes. 119 entries have code-backed usage details; Elastic's optional extra is
explicitly dependency-only. Avatars are local copies of public repository-owner
images, with their original source URLs retained in the manifest.

OpenAI SDK v0.28.1 and Anthropic SDK v0.2.9 are separate historical cards. They do
not establish current SDK dependencies or live activity, and do not add to the
120-project/116-label totals. The OpenAI tiktoken directory entry remains a
different project with its own evidence.

When updating a project, inspect the specific source, pin the revision and lines,
refresh hashes and its actual review timestamp, and preserve the true usage
scope. Do not turn examples, tests, vendored copies or optional transports into
claims about a whole company's production infrastructure. Existing third-party
provenance and license notices remain applicable. This directory is non-exhaustive
and does not imply endorsement of a token.

## Deferred realtime work

No BigQuery job or credential is included. Official PyPI logs contain event
timestamps, but ingestion is batched. The upstream Fastly rotation interval is
not an end-to-end freshness guarantee; current latency/completeness has not been
established here.

If adding an intraday source later:

1. Choose an owner-operated query project/identity or another verified source.
2. Use a dry run and an explicit byte/cost limit before any billable query. Record
   fixed query windows, job IDs, observed counts and fetch/event timestamps.
3. Compare bounded queries at different times to measure actual observed lag.
   The newest event time alone does not prove completeness.
4. Requery overlapping buckets and replace their absolute counts, allowing late
   arrivals and corrections. All visitors should read a shared cache.
5. Reconcile filtering/coverage against the historical baseline before combining
   metrics. Show source lag and incomplete periods explicitly.

The realtime feature can be completed independently of this PR. The current
directory and daily-source archive do not require it.
