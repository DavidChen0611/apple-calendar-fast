# apple-calendar-fast

Tiny read-only CLI for querying local macOS Apple Calendar events.

It reads:

```text
~/Library/Group Containers/group.com.apple.calendar/Calendar.sqlitedb
```

The script opens the database in read-only mode. It does not create, edit, or delete calendar events.

## Usage

```bash
python3 apple_calendar_fast.py --from 2026-06-01 --days 30 --limit 120
python3 apple_calendar_fast.py --from 2023-02-01 --days 28 --calendar 通用
```

Output:

```text
2026-06-24 17:00 -> 2026-06-25 01:30 | 通用 | timed | PBMC Pilot Study #7
```

## Why this exists

AppleScript is reliable for writes, but slow for broad reads. `OccurrenceCache` is fast and expands most recurring events, but older one-off events can be missing from it. This tool reads both:

- `OccurrenceCache` for fast expanded occurrences
- `CalendarItem` as a fallback for older direct events

Then it de-duplicates rows and prints a simple text stream for scripts, agents, and summaries.

## Compared with other approaches

- `icalBuddy`: mature CLI, but older and can hit Calendar permission/compatibility friction on newer macOS setups.
- EventKit-based tools: safer public API, better for full apps, but require dependencies or compiled code.
- CalDAV/vdir tools such as `khal`: great if your calendars are managed as CalDAV/vdir data, but not a drop-in reader for Apple Calendar's local database.
- Full Apple Calendar MCP servers: better when you need a full agent integration. This script is the small fallback: one file, no dependencies, read-only.

## Caveats

- This relies on Apple's private local SQLite schema, so macOS updates can break it.
- Direct database reads are for reading only. Use Calendar.app, AppleScript, EventKit, or CalDAV APIs for writes.
- Recently synced events may require opening Calendar.app first.
- Time zones and complex recurrence rules can still deserve a Calendar.app cross-check for important decisions.

## Smoke Test

```bash
python3 -m py_compile apple_calendar_fast.py
python3 apple_calendar_fast.py --from 2023-02-01 --days 28 --limit 5
python3 apple_calendar_fast.py --from 2026-06-01 --days 30 --limit 5
```

## Tested Environment

Tested on a Mac mini (Apple M4, Mac16,10) running macOS 26.5.1 build 25F80.

Other macOS versions may have different Calendar SQLite schemas. Please open an issue if it breaks on your setup.

## License

MIT
