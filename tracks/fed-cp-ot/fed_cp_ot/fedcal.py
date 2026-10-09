"""Federal Reserve holiday schedule and release-availability time.

Fed holidays with observed-date rules: a holiday on Sunday is observed on Monday; a holiday on
Saturday is NOT moved to Friday (the Federal Reserve stays open that Friday). Juneteenth counts from 2021.
"""
from datetime import date, datetime, time, timedelta
from functools import lru_cache
from zoneinfo import ZoneInfo
import pandas as pd

ET = ZoneInfo('America/New_York')
RELEASE_TIME_ET = time(13)


def _nth_weekday(year, month, weekday, n):
    d = date(year, month, 1)
    d += timedelta(days=(weekday - d.weekday()) % 7)
    return d + timedelta(weeks=n - 1)


def _last_weekday(year, month, weekday):
    d = date(year, month + 1, 1) - timedelta(days=1)
    return d - timedelta(days=(d.weekday() - weekday) % 7)


def _observed(d):
    return d + timedelta(days=1) if d.weekday() == 6 else d  # Sunday -> Monday; Saturday not moved


@lru_cache(maxsize=None)
def fed_holidays(year):
    fixed = [date(year, 1, 1), date(year, 7, 4), date(year, 11, 11), date(year, 12, 25)]
    if year >= 2021:
        fixed.append(date(year, 6, 19))
    observed = {_observed(d) for d in fixed}
    observed |= {
        _nth_weekday(year, 1, 0, 3),   # Martin Luther King Jr. Day
        _nth_weekday(year, 2, 0, 3),   # Washington's Birthday (Presidents Day)
        _last_weekday(year, 5, 0),     # Memorial Day
        _nth_weekday(year, 9, 0, 1),   # Labor Day
        _nth_weekday(year, 10, 0, 2),  # Columbus Day
        _nth_weekday(year, 11, 3, 4),  # Thanksgiving Day
    }
    return frozenset(d for d in observed if d.weekday() < 5)


def is_fed_business_day(d):
    d = pd.Timestamp(d).date()
    return d.weekday() < 5 and d not in fed_holidays(d.year)


def next_fed_business_day(d):
    d = pd.Timestamp(d).date() + timedelta(days=1)
    while not is_fed_business_day(d):
        d += timedelta(days=1)
    return d


def data_available_at(day):
    """Daily data for `day` post at 13:00 ET on the next Fed business day (DATA_SPEC: one-day lag, ~1 pm ET)."""
    return datetime.combine(next_fed_business_day(day), RELEASE_TIME_ET, ET)


def last_fed_business_day_of_week(friday):
    """Last Fed business day in the Mon-Fri week labelled by `friday` (None if the whole week is holidays)."""
    friday = pd.Timestamp(friday).date()
    for k in range(5):
        d = friday - timedelta(days=k)
        if is_fed_business_day(d):
            return d
    return None
