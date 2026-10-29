import pytest
from fed_cp_ot import pinned_inputs as pi


def fake_download(contents):
    def download(tag, name, dest):
        dest.mkdir(parents=True, exist_ok=True)
        (dest / name).write_bytes(contents[name])
        return dest / name
    return download


def test_hardcoded_tree_and_layout():
    assert str(pi.PINNED_HERE) == '/workspace/research/fed_cp_ot_prereg'
    assert {(n, s) for n, s, _ in pi.ASSETS} == {
        ('FRB_CP_xml.zip', 'raw'), ('fed_cp_volume_stats_by_maturity.csv', 'raw'), ('compute_cp_ot_burnin.py', '')}


def test_mismatch_fails(tmp_path):
    with pytest.raises(pi.PinnedAssetMismatch):
        pi.fetch_and_verify(tmp_path, download=fake_download({n: b'x' for n, _, _ in pi.ASSETS}))


def test_main_alerts_on_missing(monkeypatch, tmp_path):
    seen = []
    def boom(*a, **k): raise pi.MissingAssetError('gone')
    monkeypatch.setattr(pi, 'fetch_and_verify', boom)
    monkeypatch.setattr(pi, 'alert', lambda *a, **k: seen.append(a))
    assert pi.main([]) == 1 and seen
