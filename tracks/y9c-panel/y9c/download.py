"""Download and validate NIC quarterly files without following redirects."""
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
import zipfile

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
NIC = 'https://www.ffiec.gov/npw/FinancialReport/FinancialDataDownload'
URL = 'https://www.ffiec.gov/npw/FinancialReport/ReturnBHCFZipFiles?zipfilename='


def utc():
    return datetime.now(timezone.utc).isoformat()


def quarters(today=None):
    today = today or date.today()
    return [d for y in range(2018, today.year + 1)
            for d in (date(y, 3, 31), date(y, 6, 30), date(y, 9, 30), date(y, 12, 31))
            if d <= today]


def valid_zip(path):
    try:
        with path.open('rb') as f:
            if f.read(2) != b'PK':
                return False
        with zipfile.ZipFile(path) as z:
            return any(n.lower().endswith('.txt') for n in z.namelist()) and z.testzip() is None
    except (OSError, zipfile.BadZipFile, RuntimeError):
        return False


def fetch(session, path):
    url = URL + path.name
    partial = path.with_suffix('.partial')
    detail = ''
    for attempt in range(3):
        try:
            response = session.get(url, timeout=(30, 120), allow_redirects=False)
            detail = (f'status={response.status_code}, content-type={response.headers.get("Content-Type")!r}, '
                      f'location={response.headers.get("Location")!r}, first bytes={response.content[:160]!r}')
            if response.status_code in (408, 429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(2 ** (attempt + 1))
                continue
            if response.status_code != 200 or 'html' in response.headers.get('Content-Type', '').lower():
                break
            partial.write_bytes(response.content)
            if not valid_zip(partial):
                detail += '; invalid ZIP or no .txt member'
                break
            partial.replace(path)
            return
        except requests.RequestException as exc:
            detail = f'network error={exc}; status/content-type/first bytes unavailable if no response'
            if attempt < 2:
                time.sleep(2 ** (attempt + 1))
        finally:
            partial.unlink(missing_ok=True)
            # This function is called only for network downloads, never cache hits.
            time.sleep(1)
    raise RuntimeError(f'{path.name}: {url}\n{detail}\nManual fallback: download from {NIC} '
                       f'and drop {path.name} into {path.parent}/')


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    manifest_path = RAW / 'manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    today = date.today()
    dates = quarters(today)
    session = requests.Session()
    session.headers['User-Agent'] = 'research-lab-y9c/1.0'

    def record(path, d, fetched=False):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        old = manifest.get(path.name, {})
        stamp = (old.get('downloaded_at_utc') if old.get('sha256') == digest else None)
        manifest[path.name] = dict(quarter=f'{d.year}Q{(d.month - 1)//3 + 1}', url=URL + path.name,
                                  bytes=path.stat().st_size, sha256=digest,
                                  downloaded_at_utc=utc() if fetched else stamp or f'pre-existing cache, first seen {utc()}')
        tmp = manifest_path.with_suffix('.partial')
        tmp.write_text(json.dumps(manifest, indent=2) + '\n')
        tmp.replace(manifest_path)

    # Record provenance of seeded files even if an earlier required download fails.
    for d in dates:
        path = RAW / f'BHCF{d:%Y%m%d}.zip'
        if valid_zip(path):
            record(path, d)
    for d in dates:
        path = RAW / f'BHCF{d:%Y%m%d}.zip'
        if valid_zip(path):
            print(f'cached {path.name}', flush=True)
            continue
        try:
            fetch(session, path)
            record(path, d, fetched=True)
            print(f'downloaded {path.name} ({path.stat().st_size:,} bytes)', flush=True)
        except RuntimeError as exc:
            if d == dates[-1] and (today - d).days < 100:
                print(f'WARNING: latest quarter may be unpublished: {exc}', file=sys.stderr)
            else:
                print(f'ERROR: required quarter failed: {exc}', file=sys.stderr)
                return 1
    return 0
