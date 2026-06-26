#!/usr/bin/env python3
"""Fast, read-only Apple Calendar query via the local SQLite database."""

from __future__ import annotations

import argparse
import datetime as dt
import sqlite3
from pathlib import Path


APPLE_EPOCH_OFFSET = 978_307_200
DB_PATH = Path.home() / "Library/Group Containers/group.com.apple.calendar/Calendar.sqlitedb"


def apple_seconds(value: dt.datetime) -> float:
    return value.timestamp() - APPLE_EPOCH_OFFSET


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read Apple Calendar events quickly.")
    parser.add_argument("--days", type=int, default=35, help="Number of days to read from the start date.")
    parser.add_argument("--from", dest="from_date", help="Start date, YYYY-MM-DD. Defaults to today.")
    parser.add_argument("--calendar", help="Only include calendars whose title contains this text.")
    parser.add_argument("--limit", type=int, default=120)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not DB_PATH.exists():
        raise SystemExit(f"Calendar database not found: {DB_PATH}")

    start_day = dt.date.fromisoformat(args.from_date) if args.from_date else dt.date.today()
    start = dt.datetime.combine(start_day, dt.time.min).astimezone()
    end = start + dt.timedelta(days=args.days, seconds=-1)

    occurrence_query = """
    SELECT
      cal.title AS calendar,
      ci.summary AS title,
      COALESCE(oc.occurrence_start_date, oc.occurrence_date, ci.start_date) AS start_s,
      COALESCE(oc.occurrence_end_date, ci.end_date) AS end_s,
      COALESCE(ci.all_day, 0) AS all_day
    FROM OccurrenceCache oc
    JOIN CalendarItem ci ON ci.ROWID = oc.event_id
    JOIN Calendar cal ON cal.ROWID = oc.calendar_id
    WHERE COALESCE(oc.occurrence_start_date, oc.occurrence_date, ci.start_date) BETWEEN ? AND ?
      AND IFNULL(ci.hidden, 0) = 0
      AND (? IS NULL OR cal.title LIKE '%' || ? || '%')
    ORDER BY COALESCE(oc.occurrence_start_date, oc.occurrence_date, ci.start_date), ci.summary
    LIMIT ?
    """

    # ponytail: old one-off events can be absent from OccurrenceCache; direct CalendarItem read covers history.
    item_query = """
    SELECT
      cal.title AS calendar,
      ci.summary AS title,
      ci.start_date AS start_s,
      ci.end_date AS end_s,
      COALESCE(ci.all_day, 0) AS all_day
    FROM CalendarItem ci
    JOIN Calendar cal ON cal.ROWID = ci.calendar_id
    WHERE ci.start_date BETWEEN ? AND ?
      AND IFNULL(ci.hidden, 0) = 0
      AND (? IS NULL OR cal.title LIKE '%' || ? || '%')
    ORDER BY ci.start_date, ci.summary
    LIMIT ?
    """

    seen: set[tuple[str, str, float, float, int]] = set()
    with sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True) as conn:
        rows = conn.execute(
            occurrence_query,
            (apple_seconds(start), apple_seconds(end), args.calendar, args.calendar, args.limit),
        ).fetchall()
        rows += conn.execute(
            item_query,
            (apple_seconds(start), apple_seconds(end), args.calendar, args.calendar, args.limit),
        ).fetchall()

    printed = 0
    for calendar, title, start_s, end_s, all_day in sorted(rows, key=lambda row: (row[2], row[1])):
        key = (calendar, title, start_s, end_s, all_day)
        if key in seen:
            continue
        seen.add(key)
        if printed >= args.limit:
            break

        start_local = dt.datetime.fromtimestamp(start_s + APPLE_EPOCH_OFFSET).strftime("%Y-%m-%d %H:%M")
        end_local = dt.datetime.fromtimestamp(end_s + APPLE_EPOCH_OFFSET).strftime("%Y-%m-%d %H:%M")
        marker = "all-day" if all_day else "timed"
        print(f"{start_local} -> {end_local} | {calendar} | {marker} | {title}")
        printed += 1


if __name__ == "__main__":
    main()
