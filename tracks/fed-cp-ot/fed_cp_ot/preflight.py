from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
import os
import hashlib
import json
import uuid
import numpy as np
from .paths import PREREG_DIR, ROOT, BURNIN, OOS, EXPECTED_TRIALS
from .metric import X_LOG
from .errors import ProvenanceError, OOSNotAuthorized

PINS = {
 'test_design_fed_cp_ot_v1.json':'6c87f7ab5efe3a220cb1c50497e3a9edd7435de5965aff4a20f8f6f1b2ce7793',
 'PREREG_fed_cp_ot.md':'e3da87af2da1002b0635959d751dad4b885c59c985edc3b3a23612fa5bee0ecf',
 'fed_cp_ot_learning.html':'44e77a0c51476724947386a4fc9686af9caea4ccba9c37ae4ad61f50374f5fc7',
 'PIN.txt':'65032235646fb984f2b0a0b66f100b5257b239f4e66ac7c4a9f2f079aab419da',
 'GATE_THRESHOLDS_fed_cp_ot.md':'c15eb60cbe1467090fcc920b8f4e311dd14f7b3bbfd0437e21809355721a6c8a',
 'DATA_SPEC_for_app.md':'9c50a16e994cdb04e2598b270800e2941d027e314b375e33cbf5caa98f102c6c',
 'ENGINEERING_TICKET.md':'088d9f2e72a162daf25436b2c76c3b4cfe6b93abd0082d480b5f94befa86346d'}
REQUIRED_PINNED = ('PIN.txt', 'test_design_fed_cp_ot_v1.json', 'PREREG_fed_cp_ot.md',
                   'fed_cp_ot_learning.html', 'GATE_THRESHOLDS_fed_cp_ot.md',
                   'DATA_SPEC_for_app.md', 'ENGINEERING_TICKET.md')
APPROVAL_PATH = PREREG_DIR / 'APPROVAL_fed_cp_ot.txt'
APPROVAL_SHA256 = None
_issued = {}

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def fail(message):
    raise ProvenanceError(message + '. Nothing was logged or loaded')

@dataclass(frozen=True)
class Provenance:
    mode: str
    prereg_dir: str
    file_hashes: object
    pin: object
    oos_approved: bool
    verified_at_utc: str
    token: str

def validate_provenance(provenance, require_oos=False):
    if not isinstance(provenance, Provenance) or _issued.get(provenance.token) is not provenance:
        fail('A valid preflight Provenance is required')
    if require_oos and (provenance.mode != 'oos' or not provenance.oos_approved):
        raise OOSNotAuthorized('OOS approval required')
    return provenance

def check_oos_approval():
    if not APPROVAL_PATH.is_file():
        raise OOSNotAuthorized('Approval missing. Nothing was logged or loaded')
    if APPROVAL_SHA256 is None:
        raise OOSNotAuthorized('approval exists but is not pinned. Nothing was logged or loaded')
    if sha256(APPROVAL_PATH) != APPROVAL_SHA256:
        fail('Approval hash mismatch')
    if PINS['PIN.txt'] not in APPROVAL_PATH.read_text():
        raise OOSNotAuthorized('Approval must reference the PIN.txt sha256. Nothing was logged or loaded')
    return True

def preflight(mode):
    if mode not in {'burnin', 'oos'}:
        fail('Unknown preflight mode')
    hashes = {}
    for name in REQUIRED_PINNED:
        path = PREREG_DIR / name
        if not path.is_file() or sha256(path) != PINS[name]:
            fail('Missing or mismatched pinned file: ' + name)
        hashes[name] = sha256(path)
    try:
        pin = dict(token.split('=', 1) for token in (PREREG_DIR / 'PIN.txt').read_text().split())
        for key, name in [('design_sha256','test_design_fed_cp_ot_v1.json'),
                          ('prereg_sha256','PREREG_fed_cp_ot.md'), ('html_sha256','fed_cp_ot_learning.html')]:
            if pin.get(key) != PINS[name] or pin.get(key) != hashes[name]:
                fail('PIN.txt reference mismatch')
        design = json.loads((PREREG_DIR / 'test_design_fed_cp_ot_v1.json').read_text())
        if design['oos_authorized'] is not False:
            fail('oos_authorized is a record, not the switch')
        if design['trials']['confirmatory_oos_tests'] != EXPECTED_TRIALS:
            fail('Trial count mismatch')
        if tuple(design['windows']['burnin']) != BURNIN or tuple(design['windows']['oos']) != OOS:
            fail('Window mismatch')
        support = np.asarray(design['object']['support_log_days'])
        if support.shape != (6,) or not np.allclose(support, X_LOG, atol=1e-6, rtol=0):
            fail('Support mismatch')
    except (KeyError, ValueError, TypeError) as exc:
        fail(str(exc))
    approved = check_oos_approval() if mode == 'oos' else False
    result = Provenance(mode, os.path.relpath(PREREG_DIR, ROOT), MappingProxyType(hashes), MappingProxyType(pin), approved,
                        datetime.now(timezone.utc).isoformat(), uuid.uuid4().hex)
    _issued[result.token] = result
    return result
