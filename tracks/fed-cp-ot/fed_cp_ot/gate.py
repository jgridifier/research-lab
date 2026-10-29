"""Run/skip decision for the scheduled daily ingest. Pure function of a clock and the manifest."""
from datetime import time
from email.utils import parsedate_to_datetime
import os
from .fed_holidays import is_fed_holiday
from .fedcal import ET

WINDOW_START, WINDOW_END = time(13, 30), time(18, 0)  # America/New_York, inclusive


def _last_modified_et_date(row):
    value = row.get('last_modified')
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).astimezone(ET).date()
    except (TypeError, ValueError):
        return None


def already_ingested_today(manifest_rows, today):
    """Today's vintage = fetched today (ET) and the release itself was last modified today (ET).

    A fetch that still returns yesterday's file does not count, so the cron keeps retrying until the
    new file posts. Rows without a parseable Last-Modified never count.
    """
    return any(r.get('fetched_at_et', '')[:10] == today.isoformat() and _last_modified_et_date(r) == today
               for r in manifest_rows)


def decide(now_utc, manifest_rows):
    """Return (run, reason). `now_utc` must be timezone-aware."""
    if now_utc.tzinfo is None:
        raise ValueError('now_utc must be timezone-aware')
    now = now_utc.astimezone(ET)
    today, t = now.date(), now.time()
    if today.weekday() >= 5:
        return False, f'{today} is a weekend'
    if is_fed_holiday(today):
        return False, f'{today} is a Fed holiday'
    if not WINDOW_START <= t.replace(second=0, microsecond=0) <= WINDOW_END:
        return False, f'{now:%H:%M} ET is outside {WINDOW_START:%H:%M}-{WINDOW_END:%H:%M} ET'
    if already_ingested_today(manifest_rows, today):
        return False, f"today's vintage ({today}) is already ingested"
    return True, f'{now:%Y-%m-%d %H:%M} ET inside the ingest window'


def write_github_output(run, reason, path=None):
    path = path or os.environ.get('GITHUB_OUTPUT')
    if path:
        with open(path, 'a') as f:
            f.write(f"run={'true' if run else 'false'}\nreason={reason}\n")
