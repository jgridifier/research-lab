import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from .paths import TRIALS_PATH, ROOT
from .preflight import preflight, validate_provenance
from .errors import ProvenanceError
from .parse import load_vol
CONFIRMATORY_TRIALS = (
    ('WAR vs B*', {'family':'A','candidate':'WAR','comparator':'B*'}),
    ('TMAR vs B*', {'family':'A','candidate':'TMAR','comparator':'B*'}),
    ('SEL vs P', {'family':'B','candidate':'SEL','comparator':'P'}))

def git_head():
    """HEAD of the checkout. Raises ProvenanceError (nothing logged) when there is no git checkout or git binary."""
    try:
        out = subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True,timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        raise ProvenanceError(f'git unavailable ({exc.__class__.__name__}); a trial needs a git head. Nothing was logged.') from None
    head = out.stdout.strip()
    if out.returncode != 0 or len(head) != 40:
        raise ProvenanceError('No git checkout; a trial needs a git head. Nothing was logged.')
    return head

def log_trial(config, label, provenance, path=TRIALS_PATH):
    validate_provenance(provenance, require_oos=True)
    encoded = json.dumps(config, sort_keys=True, separators=(',',':'), allow_nan=False)
    record = {'timestamp_utc':datetime.now(timezone.utc).isoformat(),
              'git_head':git_head(),
              'config_hash':hashlib.sha256(encoded.encode()).hexdigest(), 'label':label,
              'provenance':dict(provenance.file_hashes), 'counts_as_trial':True}
    with Path(path).open('a') as f: f.write(json.dumps(record, sort_keys=True)+'\n')
    return record

def trial_count(path=TRIALS_PATH):
    p = Path(path)
    return sum(json.loads(s)['counts_as_trial'] is True for s in p.read_text().splitlines()) if p.exists() else 0

def _assert_harness_implemented():
    raise NotImplementedError('OOS harness is a later PR; no trial was logged')

def run_oos():
    provenance = preflight('oos')
    _assert_harness_implemented()
    for label, config in CONFIRMATORY_TRIALS: log_trial(config, label, provenance)
    return load_vol(provenance)
