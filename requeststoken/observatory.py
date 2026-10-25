"""Download snapshots from ClickHouse, with a shared SQLite cache and lease.

This is a delayed daily source. Realtime event collection is intentionally not
implemented. Requests return the last snapshot while one background read runs.
"""

from __future__ import annotations

import copy
import json
import logging
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager, nullcontext
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

import httpx

from requeststoken.config import ROOT, USER_AGENT
from requeststoken.data import SystemClock

logger = logging.getLogger("requeststoken.observatory")
ASSETS = ROOT / "static" / "observatory"
ENDPOINT = "https://sql-clickhouse.clickhouse.com/"
SETTINGS = (
    "SETTINGS max_execution_time=25, read_overflow_mode='throw', "
    "timeout_overflow_mode='throw', result_overflow_mode='throw', "
    "group_by_overflow_mode='throw' FORMAT JSON"
)
MAX_SAFE_INTEGER = 2**53 - 1


def iso_day(value: str) -> str:
    if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
        raise ValueError("Invalid calendar date")
    return value


def count(value) -> int:
    if isinstance(value, str) and value.isascii() and value.isdigit():
        value = int(value)
    if type(value) is not int or not 0 <= value <= MAX_SAFE_INTEGER:
        raise ValueError("Invalid download count")
    return value


def queries_for(today: str, latest: str, first: str = "2016-01-22") -> dict:
    today, latest, first = map(iso_day, (today, latest, first))
    cutoff = (date.fromisoformat(latest) + timedelta(days=1)).isoformat()
    return {
        "daily": "SELECT date, sum(count) AS downloads FROM pypi.pypi_downloads_per_day "
        f"WHERE project='requests' AND date<='{today}' GROUP BY date ORDER BY date {SETTINGS}",
        "total": "SELECT count() AS downloads FROM pypi.pypi WHERE project='requests' "
        f"AND date>='{first}' AND date<'{cutoff}' {SETTINGS}",
        "latest": "SELECT count() AS downloads FROM pypi.pypi WHERE project='requests' "
        f"AND date='{latest}' {SETTINGS}",
    }


def validate_snapshot(value: dict) -> dict:
    if not isinstance(value, dict) or value.get("package") != "requests":
        raise ValueError("Invalid package snapshot")
    first, latest = iso_day(value["firstDate"]), iso_day(value["latestDate"])
    raw_total, raw_latest = count(value["rawTotal"]), count(value["rawLatest"])
    if first > latest or raw_total < raw_latest:
        raise ValueError("Invalid snapshot range")
    stamp = datetime.fromisoformat(value["fetchedAt"].replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("Snapshot timestamp must include a timezone")
    rows = value["daily"]
    if not isinstance(rows, list) or not 1 <= len(rows) <= 10_000:
        raise ValueError("Invalid daily history")
    daily, previous = [], ""
    for row in rows:
        day = iso_day(row["date"])
        if not first <= day <= latest or day <= previous:
            raise ValueError("Unsorted, duplicate or out-of-range date")
        daily.append({"date": day, "downloads": count(row["downloads"])})
        previous = day
    if daily[0]["date"] != first or daily[-1]["date"] != latest:
        raise ValueError("Snapshot bounds disagree with its history")
    return {
        "package": "requests", "firstDate": first, "latestDate": latest,
        "rawTotal": raw_total, "rawLatest": raw_latest,
        "fetchedAt": value["fetchedAt"], "daily": daily,
        "source": "ClickPy / ClickHouse · PyPI download logs",
        "queries": queries_for(latest, latest, first),
    }


@lru_cache(maxsize=1)
def adoption_manifest() -> dict:
    return json.loads((ASSETS / "adoption-evidence.json").read_text(encoding="utf-8"))


class DownloadObservatory:
    def __init__(self, *, database=None, seed=None, client=None, clock=None,
                 refresh_enabled=None, executor=None):
        self.database = Path(database) if database is not None else ROOT / "var" / "observatory.sqlite"
        self.seed = validate_snapshot(seed if seed is not None else json.loads(
            (ASSETS / "download-snapshot.json").read_text(encoding="utf-8")
        ))
        self.clock = clock or SystemClock()
        self.client = client
        self.refresh_enabled = (
            os.environ.get("REQUESTS_OBSERVATORY_REFRESH", "1") != "0"
            if refresh_enabled is None else refresh_enabled
        )
        self.executor = executor or ThreadPoolExecutor(max_workers=1, thread_name_prefix="downloads")

    @contextmanager
    def _connect(self):
        self.database.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.database, timeout=3)
        try:
            db.row_factory = sqlite3.Row
            db.execute("""CREATE TABLE IF NOT EXISTS snapshot (
                id TEXT PRIMARY KEY, payload TEXT NOT NULL, checked_at TEXT NOT NULL,
                status TEXT NOT NULL, next_attempt REAL NOT NULL DEFAULT 0,
                lease_until REAL NOT NULL DEFAULT 0, lease_token TEXT)""")
            db.execute("""CREATE TABLE IF NOT EXISTS source_checks (
                day TEXT PRIMARY KEY, fetched_at TEXT NOT NULL, latest_date TEXT NOT NULL,
                raw_total INTEGER NOT NULL, raw_latest INTEGER NOT NULL, reported_days INTEGER NOT NULL)""")
            db.execute("INSERT OR IGNORE INTO snapshot (id,payload,checked_at,status) VALUES (?,?,?,?)",
                       ("requests", json.dumps(self.seed), self.seed["fetchedAt"], "fallback"))
            db.commit()
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def read(self) -> dict:
        now = self.clock.timestamp()
        stamp = self.clock.now().astimezone(timezone.utc).isoformat()
        snapshot, checked, status, refreshing = self.seed, self.seed["fetchedAt"], "fallback", False
        token = None
        try:
            with self._connect() as db:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute("SELECT * FROM snapshot WHERE id='requests'").fetchone()
                snapshot = validate_snapshot(json.loads(row["payload"]))
                checked, status = row["checked_at"], row["status"]
                if status not in ("current", "cached", "fallback"):
                    raise ValueError("Invalid cache status")
                refreshing = row["lease_until"] > now
                if self.refresh_enabled and not refreshing and row["next_attempt"] <= now:
                    token, refreshing = uuid4().hex, True
                    db.execute("UPDATE snapshot SET lease_until=?, lease_token=? WHERE id='requests'",
                               (now + 120, token))
            if token:
                self.executor.submit(self._refresh, snapshot, token)
        except Exception as exc:
            logger.warning("snapshot cache unavailable (%s)", type(exc).__name__)
            # A valid saved row remains usable if scheduling or storage fails.
            status, refreshing = "fallback", False
        message = None
        if status == "cached":
            message = "The latest source check failed. Showing the last successful snapshot."
        elif status == "fallback":
            message = "Showing the saved audit. A fresh source snapshot has not been confirmed."
        return {
            "snapshot": copy.deepcopy(snapshot), "status": status, "checkedAt": checked,
            "serverTime": stamp, "refreshing": refreshing, "message": message,
        }

    def _query(self, sql: str, client) -> list:
        response = client.get(ENDPOINT, params={"user": "demo", "query": sql})
        response.raise_for_status()
        body = response.json()
        if not isinstance(body, dict) or body.get("exception") or not isinstance(body.get("data"), list):
            raise ValueError("Invalid source response")
        rows = body["data"]
        if body.get("rows") != len(rows) or body.get("rows_before_limit_at_least", 0) > len(rows):
            raise ValueError("Truncated source response")
        return rows

    def fetch_snapshot(self, previous: dict) -> dict:
        transport = nullcontext(self.client) if self.client is not None else httpx.Client(
            timeout=httpx.Timeout(30.0, connect=5.0),
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        )
        with transport as client:
            return self._fetch_snapshot(previous, client)

    def _fetch_snapshot(self, previous: dict, client) -> dict:
        today = self.clock.now().astimezone(timezone.utc).date().isoformat()
        rows = self._query(queries_for(today, previous["latestDate"])["daily"], client)
        if not rows or len(rows) < len(previous["daily"]) * .95 or len(rows) > 10_000:
            raise ValueError("Missing source history")
        daily = [{"date": iso_day(r["date"]), "downloads": count(r["downloads"])} for r in rows]
        first, latest = daily[0]["date"], daily[-1]["date"]
        if latest > today or latest < previous["latestDate"]:
            raise ValueError("Regressed or future source date")
        queries = queries_for(today, latest, first)
        total, last = self._query(queries["total"], client), self._query(queries["latest"], client)
        if len(total) != 1 or len(last) != 1:
            raise ValueError("Missing raw counts")
        result = validate_snapshot({
            "package": "requests", "firstDate": first, "latestDate": latest,
            "rawTotal": count(total[0]["downloads"]), "rawLatest": count(last[0]["downloads"]),
            "daily": daily, "fetchedAt": self.clock.now().astimezone(timezone.utc).isoformat(),
        })
        result["queries"] = queries
        return result

    def _refresh(self, previous: dict, token: str):
        try:
            fresh = self.fetch_snapshot(previous)
            with self._connect() as db:
                changed = db.execute("""UPDATE snapshot SET payload=?,checked_at=?,status='current',
                    next_attempt=?,lease_until=0,lease_token=NULL WHERE id='requests' AND lease_token=?""",
                    (json.dumps(fresh), fresh["fetchedAt"], self.clock.timestamp() + 3600, token)).rowcount
                if changed:
                    db.execute("INSERT OR REPLACE INTO source_checks VALUES (?,?,?,?,?,?)", (
                        self.clock.now().astimezone(timezone.utc).date().isoformat(), fresh["fetchedAt"],
                        fresh["latestDate"], fresh["rawTotal"], fresh["rawLatest"], len(fresh["daily"]),
                    ))
        except Exception as exc:
            logger.warning("download source refresh failed (%s)", type(exc).__name__)
            try:
                with self._connect() as db:
                    db.execute("""UPDATE snapshot SET checked_at=?,status='cached',next_attempt=?,
                        lease_until=0,lease_token=NULL WHERE id='requests' AND lease_token=?""",
                        (self.clock.now().astimezone(timezone.utc).isoformat(), self.clock.timestamp() + 600, token))
            except Exception as cache_error:
                logger.warning("could not record source failure (%s)", type(cache_error).__name__)
