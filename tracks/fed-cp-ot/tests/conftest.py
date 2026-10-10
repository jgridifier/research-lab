import sys
from pathlib import Path
import shutil
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
TRACK = Path(__file__).resolve().parents[1]

@pytest.fixture(scope='session')
def pinned_dir(tmp_path_factory):
    from fed_cp_ot.preflight import REQUIRED_PINNED
    dest = tmp_path_factory.mktemp('prereg')
    for name in REQUIRED_PINNED: shutil.copyfile(TRACK/'prereg'/name,dest/name)
    return dest

@pytest.fixture
def pins(pinned_dir,tmp_path,monkeypatch):
    from fed_cp_ot import preflight as pf
    dest = tmp_path/'prereg'; shutil.copytree(pinned_dir,dest)
    monkeypatch.setattr(pf,'PREREG_DIR',dest)
    monkeypatch.setattr(pf,'APPROVAL_PATH',dest/'APPROVAL_fed_cp_ot.txt')
    return pf

@pytest.fixture
def provenance(pins): return pins.preflight('burnin')

@pytest.fixture
def approved(pins,monkeypatch):
    pins.APPROVAL_PATH.write_text('Jared approves '+pins.PINS['PIN.txt'])
    monkeypatch.setattr(pins,'APPROVAL_SHA256',pins.sha256(pins.APPROVAL_PATH))
    return pins.preflight('oos')

@pytest.fixture(scope='session')
def real_zip():
    from fed_cp_ot.paths import DATA_DIR, RAW_DIR, PINNED_RESEARCH_ZIP_SHA256
    from fed_cp_ot.preflight import sha256
    candidates = [RAW_DIR/'FRB_CP_xml.zip', *sorted((DATA_DIR/'vintages').glob('*.zip'))]
    for path in candidates:
        if path.exists() and sha256(path) == PINNED_RESEARCH_ZIP_SHA256:
            return path
    pytest.skip('Pinned zip absent (set FED_CP_OT_RAW_DIR or seed data/vintages)')

@pytest.fixture(scope='session')
def real_vol(real_zip):
    from fed_cp_ot.preflight import preflight
    from fed_cp_ot.parse import load_vol
    return load_vol(preflight('burnin'), real_zip)
