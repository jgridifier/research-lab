import json
import pytest
from fed_cp_ot import preflight as pf
from fed_cp_ot.errors import ProvenanceError, OOSNotAuthorized
from fed_cp_ot import trials

@pytest.mark.parametrize('name',pf.REQUIRED_PINNED)
@pytest.mark.parametrize('action',['tamper','missing'])
def test_pins(pins,name,action):
    path=pins.PREREG_DIR/name
    if action=='tamper': path.write_bytes(path.read_bytes()+b'!')
    else: path.unlink()
    with pytest.raises(ProvenanceError,match='Nothing was logged or loaded'): pins.preflight('burnin')

def repin(pins,monkeypatch,name):
    updated=dict(pins.PINS); updated[name]=pins.sha256(pins.PREREG_DIR/name)
    monkeypatch.setattr(pins,'PINS',updated)

def test_pin_references(pins,monkeypatch):
    (pins.PREREG_DIR/'PIN.txt').write_text('design_sha256=bad prereg_sha256=bad html_sha256=bad')
    repin(pins,monkeypatch,'PIN.txt')
    with pytest.raises(ProvenanceError,match='reference mismatch'): pins.preflight('burnin')

@pytest.mark.parametrize('change',['flag','trials','windows','support'])
def test_design_semantics(pins,monkeypatch,change):
    path=pins.PREREG_DIR/'test_design_fed_cp_ot_v1.json'; d=json.loads(path.read_text())
    if change=='flag': d['oos_authorized']=True
    elif change=='trials': d['trials']['confirmatory_oos_tests']=4
    elif change=='windows': d['windows']['oos'][0]='2008-12-26'
    else: d['object']['support_log_days'][0]=9
    path.write_text(json.dumps(d)); repin(pins,monkeypatch,path.name)
    pin=pins.PREREG_DIR/'PIN.txt'
    pin.write_text(' '.join(k+'='+pins.PINS[n] for k,n in [('design_sha256',path.name),('prereg_sha256','PREREG_fed_cp_ot.md'),('html_sha256','fed_cp_ot_learning.html')]))
    repin(pins,monkeypatch,'PIN.txt')
    with pytest.raises(ProvenanceError,match='record, not the switch' if change=='flag' else None): pins.preflight('burnin')

@pytest.mark.parametrize('kind',['missing','unpinned','wrong_sha','missing_reference'])
def test_approval_refusal(pins,monkeypatch,kind):
    if kind!='missing': pins.APPROVAL_PATH.write_text('approved '+(pins.PINS['PIN.txt'] if kind!='missing_reference' else 'wrong'))
    if kind=='wrong_sha': monkeypatch.setattr(pins,'APPROVAL_SHA256','bad')
    if kind=='missing_reference': monkeypatch.setattr(pins,'APPROVAL_SHA256',pins.sha256(pins.APPROVAL_PATH))
    with pytest.raises(ProvenanceError): pins.preflight('oos')

def test_approval_and_trials(approved,tmp_path):
    path=tmp_path/'trials.jsonl'
    assert approved.oos_approved and trials.trial_count(path)==0
    for label,config in trials.CONFIRMATORY_TRIALS: trials.log_trial(config,label,approved,path)
    assert trials.trial_count(path)==3
    rows=[json.loads(s) for s in path.read_text().splitlines()]
    assert len({r['config_hash'] for r in rows})==3

def test_no_trial_without_approval(provenance,tmp_path):
    path=tmp_path/'trials.jsonl'
    with pytest.raises(OOSNotAuthorized): trials.log_trial({},'test',provenance,path)
    assert not path.exists()

@pytest.mark.parametrize('broken_pin',[False,True])
def test_run_oos_order(pins,monkeypatch,tmp_path,broken_pin):
    if broken_pin: (pins.PREREG_DIR/'PIN.txt').unlink()
    calls=[]
    monkeypatch.setattr(trials,'log_trial',lambda *a,**k:calls.append('log'))
    monkeypatch.setattr(trials,'load_vol',lambda *a,**k:calls.append('load'))
    with pytest.raises(ProvenanceError): trials.run_oos()
    assert calls==[] and not (tmp_path/'trials.jsonl').exists()

def test_harness_stub_before_logging(approved,monkeypatch):
    calls=[]
    monkeypatch.setattr(trials,'preflight',lambda mode:approved)
    monkeypatch.setattr(trials,'log_trial',lambda *a:calls.append('log'))
    monkeypatch.setattr(trials,'load_vol',lambda *a:calls.append('load'))
    with pytest.raises(NotImplementedError): trials.run_oos()
    assert not calls

def test_committed_preflight():
    from fed_cp_ot.paths import TRACK
    assert pf.PREREG_DIR == TRACK/'prereg'
    provenance = pf.preflight('burnin')
    assert provenance.prereg_dir == 'tracks/fed-cp-ot/prereg'
    assert len(provenance.file_hashes) == 7
    with pytest.raises(OOSNotAuthorized): pf.preflight('oos')


def _flag_true_and_repinned(pins,monkeypatch):
    path=pins.PREREG_DIR/'test_design_fed_cp_ot_v1.json'; d=json.loads(path.read_text()); d['oos_authorized']=True
    path.write_text(json.dumps(d)); repin(pins,monkeypatch,path.name)
    (pins.PREREG_DIR/'PIN.txt').write_text(' '.join(k+'='+pins.PINS[n] for k,n in [('design_sha256',path.name),('prereg_sha256','PREREG_fed_cp_ot.md'),('html_sha256','fed_cp_ot_learning.html')]))
    repin(pins,monkeypatch,'PIN.txt')

def test_oos_fails_if_design_flag_true_even_with_valid_approval(pins,monkeypatch,tmp_path):
    """Like Y-9C: oos_authorized=true in the design is a preflight FAILURE, never the switch, even with a pinned approval."""
    _flag_true_and_repinned(pins,monkeypatch)
    pins.APPROVAL_PATH.write_text('Jared approves PIN.txt sha256 '+pins.PINS['PIN.txt'])
    monkeypatch.setattr(pins,'APPROVAL_SHA256',pins.sha256(pins.APPROVAL_PATH))
    calls=[]
    monkeypatch.setattr(trials,'preflight',pins.preflight)
    monkeypatch.setattr(trials,'log_trial',lambda *a,**k:calls.append('log'))
    monkeypatch.setattr(trials,'load_vol',lambda *a,**k:calls.append('load'))
    with pytest.raises(ProvenanceError,match='record, not the switch'): pins.preflight('oos')
    with pytest.raises(ProvenanceError,match='record, not the switch'): trials.run_oos()
    assert calls==[]

def test_approval_requires_pinned_hash_in_code():
    """APPROVAL_SHA256 stays None until Jared approves and a reviewed commit pins the file's hash."""
    assert pf.APPROVAL_SHA256 is None
    assert pf.APPROVAL_PATH.name=='APPROVAL_fed_cp_ot.txt' and not pf.APPROVAL_PATH.exists()

def test_unpinned_approval_file_is_refused(pins):
    pins.APPROVAL_PATH.write_text('Jared approves PIN.txt sha256 '+pins.PINS['PIN.txt'])
    with pytest.raises(OOSNotAuthorized,match='not pinned'): pins.preflight('oos')
