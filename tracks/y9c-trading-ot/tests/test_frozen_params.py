"""prereg §6.3 test 10: trim set, s and B* are computed once at 2021Q4 and only read afterwards."""
import pandas as pd
import pytest
from trading_ot import walkforward as WF


def test_freeze_uses_burnin_only(panel, macro):
    a = WF.freeze_decisions(panel, macro, 'matched')
    b = WF.freeze_decisions(panel[panel.quarter.le(pd.Period('2021Q4'))], macro, 'matched')
    assert a == b
    assert a['freeze_origin'] == '2021Q4' and a['pseudo_targets'][0] == '2020Q2' and a['pseudo_targets'][-1] == '2021Q4'
    assert set(a['trimmed_members']) <= set(a['members']) and len(a['trimmed_members']) >= 2
    assert a['s'] in (1.0, 1.1, 1.2, 1.35, 1.5)


def test_oos_loop_never_refreezes(panel, macro, monkeypatch):
    frozen = WF.freeze_decisions(panel, macro, 'matched')
    def boom(*a, **k):
        raise AssertionError('freeze_decisions called inside the OOS loop')
    monkeypatch.setattr(WF, 'freeze_decisions', boom)
    out = WF.h1_oos(panel, macro, frozen, origins=pd.period_range('2021Q4', '2022Q2', freq='Q'))
    assert set(out.method) >= {'BARY', *frozen['members']}


def test_unregistered_policy_rejected(panel, macro):
    with pytest.raises(ValueError):
        WF.freeze_decisions(panel, macro, 'whatever')
