"""Hardcoded Federal Reserve holiday dates, 2025-2030, for the daily-ingest gate.

Observed rules: a Sunday holiday is observed on Monday; a Saturday holiday is not moved (the Fed stays open
the Friday before). Independent of `fedcal`, which computes the same rules; a test cross-checks the two.
"""
from datetime import date

FED_HOLIDAYS = frozenset(date.fromisoformat(s) for s in (
    '2025-01-01', '2025-01-20', '2025-02-17', '2025-05-26', '2025-06-19', '2025-07-04',
    '2025-09-01', '2025-10-13', '2025-11-11', '2025-11-27', '2025-12-25',
    '2026-01-01', '2026-01-19', '2026-02-16', '2026-05-25', '2026-06-19',
    '2026-09-07', '2026-10-12', '2026-11-11', '2026-11-26', '2026-12-25',
    '2027-01-01', '2027-01-18', '2027-02-15', '2027-05-31', '2027-07-05',
    '2027-09-06', '2027-10-11', '2027-11-11', '2027-11-25',
    '2028-01-17', '2028-02-21', '2028-05-29', '2028-06-19', '2028-07-04',
    '2028-09-04', '2028-10-09', '2028-11-23', '2028-12-25',
    '2029-01-01', '2029-01-15', '2029-02-19', '2029-05-28', '2029-06-19', '2029-07-04',
    '2029-09-03', '2029-10-08', '2029-11-12', '2029-11-22', '2029-12-25',
    '2030-01-01', '2030-01-21', '2030-02-18', '2030-05-27', '2030-06-19', '2030-07-04',
    '2030-09-02', '2030-10-14', '2030-11-11', '2030-11-28', '2030-12-25',
))
FIRST_YEAR, LAST_YEAR = 2025, 2030


def is_fed_holiday(d):
    """True on a listed Fed holiday. Raises outside 2025-2030 rather than guessing."""
    if not FIRST_YEAR <= d.year <= LAST_YEAR:
        raise ValueError(f'Fed holiday list covers {FIRST_YEAR}-{LAST_YEAR}, got {d}')
    return d in FED_HOLIDAYS
