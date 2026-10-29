"""Hash-chained JSONL manifest: each entry stores the previous entry's hash and its own."""
import hashlib
import json
from pathlib import Path

GENESIS = '0' * 64


class ChainError(ValueError):
    pass


def entry_hash(record):
    body = {k: v for k, v in record.items() if k != 'entry_hash'}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def read_rows(path):
    path = Path(path)
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def append_chained(path, record):
    """Append `record` linked to the current tail; returns the stored row."""
    rows = read_rows(path)
    verify_rows(rows)
    row = dict(record, prev_hash=rows[-1]['entry_hash'] if rows else GENESIS)
    row['entry_hash'] = entry_hash(row)
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as f:
        f.write(json.dumps(row, sort_keys=True) + '\n')
    return row


def verify_rows(rows):
    prev = GENESIS
    for i, row in enumerate(rows):
        if row.get('prev_hash') != prev:
            raise ChainError(f'entry {i}: prev_hash does not match the previous entry')
        if row.get('entry_hash') != entry_hash(row):
            raise ChainError(f'entry {i}: entry_hash does not match its contents (edited?)')
        prev = row['entry_hash']
    return len(rows)


def verify_chain(path):
    """Raise ChainError on any edit, deletion, reorder or insertion; returns the entry count."""
    try:
        rows = read_rows(path)
    except json.JSONDecodeError as exc:
        raise ChainError(f'unparseable manifest line: {exc}') from exc
    return verify_rows(rows)
