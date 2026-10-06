"""prereg §6.3 test 4: the ex-ante bank set uses burn-in data (<= 2021Q4) only."""
import numpy as np
import pandas as pd
from trading_ot import sets


def test_post_burnin_changes_do_not_move_set(panel):
    a = sets.exante_bank_set(panel)
    p = panel.copy()
    later = p.quarter.gt(pd.Period('2021Q4'))
    p.loc[later, 'trading_revenue_q'] = 0.0
    p = p[~(later & p.rssd_id.isin(a[:3]))]            # also delete some members' later rows (exits)
    assert sets.exante_bank_set(p) == a


def test_burnin_changes_do_move_set(panel):
    a = sets.exante_bank_set(panel)
    p = panel.copy()
    p.loc[p.rssd_id.eq(a[0]) & p.quarter.eq(pd.Period('2019Q2')), 'trading_revenue_q'] = 1.0
    assert a[0] not in sets.exante_bank_set(p)


def test_balanced_is_sensitivity_and_uses_full_sample(panel):
    b = sets.balanced_set(panel)
    assert set(b) <= set(sets.exante_bank_set(panel))
