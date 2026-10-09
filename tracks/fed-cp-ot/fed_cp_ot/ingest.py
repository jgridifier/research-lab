"""Immutable vintage storage. Fetching/hashing bytes does not interpret amounts."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo
import zipfile
import xml.etree.ElementTree as ET
from .paths import DATA_DIR, SOURCE_URL, PINNED_RESEARCH_ZIP_SHA256

def _manifest(cache_dir):
    p = Path(cache_dir) / 'manifest.jsonl'
    return [json.loads(line) for line in p.read_text().splitlines()] if p.exists() else []

def latest_vintage(cache_dir=DATA_DIR):
    rows = _manifest(cache_dir)
    if not rows: raise FileNotFoundError('No cached vintage; use ingest fetch or seed')
    return Path(cache_dir) / rows[-1]['path']

def _store(blob, cache_dir, metadata):
    sha = hashlib.sha256(blob).hexdigest()
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        h = hashlib.sha256()
        with z.open('CP_data.xml') as f:
            for chunk in iter(lambda:f.read(1024*1024), b''): h.update(chunk)
        prepared = None
        with z.open('CP_data.xml') as f:
            for _, elem in ET.iterparse(f, events=('end',)):
                tag = elem.tag.rsplit('}',1)[-1]
                if tag == 'Prepared': prepared = elem.text
                if tag == 'Header': break
                elem.clear()
    cache_dir = Path(cache_dir)
    previous = _manifest(cache_dir)
    now = datetime.now(timezone.utc)
    same = bool(previous and previous[-1]['sha256'] == sha)
    existing = next((r['path'] for r in previous if r['sha256'] == sha), None)
    name = existing or f'vintages/FRB_CP_xml_{now:%Y%m%dT%H%M%SZ}_{sha[:12]}.zip'
    dest = cache_dir / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists(): dest.write_bytes(blob)
    record = dict(source_url=SOURCE_URL, fetched_at_utc=now.isoformat(),
                  fetched_at_et=now.astimezone(ZoneInfo('America/New_York')).isoformat(),
                  sha256=sha, bytes=len(blob), http_status=None, last_modified=None,
                  etag=None, content_length=None, zip_member_sha256=h.hexdigest(),
                  xml_prepared=prepared, unchanged_from_previous=same, path=name)
    record.update(metadata)
    with (cache_dir/'manifest.jsonl').open('a') as f: f.write(json.dumps(record, sort_keys=True)+'\n')
    return record

def fetch_vintage(cache_dir=DATA_DIR, url=SOURCE_URL, opener=None, retries=3, backoff_s=1):
    opener = opener or urlopen
    for attempt in range(retries):
        try:
            req = Request(url, headers={'User-Agent':'research-lab fed-cp-ot (jgridifier)'})
            with opener(req) as response:
                status = response.status
                if status != 200: raise ValueError(f'HTTP {status}')
                blob = response.read()
                headers = response.headers
            return _store(blob, cache_dir, dict(source_url=url, http_status=status,
                last_modified=headers.get('Last-Modified'), etag=headers.get('ETag'),
                content_length=headers.get('Content-Length')))
        except (OSError, ValueError, zipfile.BadZipFile, KeyError):
            if attempt == retries-1: raise
            time.sleep(backoff_s * 2**attempt)
    raise ValueError('retries must be positive')

def register_local_vintage(path, note, cache_dir=DATA_DIR, pinned=False):
    blob = Path(path).read_bytes()
    if pinned and hashlib.sha256(blob).hexdigest() != PINNED_RESEARCH_ZIP_SHA256:
        raise ValueError('Pinned research zip hash mismatch')
    return _store(blob, cache_dir, {'note':note, 'provenance':'local copy'})

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['fetch','seed','list'])
    parser.add_argument('path', nargs='?')
    args = parser.parse_args()
    if args.command == 'fetch': result = fetch_vintage()
    elif args.command == 'seed': result = register_local_vintage(args.path, 'Pinned research seed', pinned=True)
    else: result = _manifest(DATA_DIR)
    print(json.dumps(result, indent=2))
if __name__ == '__main__': main()
