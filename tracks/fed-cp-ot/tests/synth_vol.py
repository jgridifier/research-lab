"""Synthetic long-format VOL frame (the parse_vol output schema) with mix dynamics, for harness tests."""
import numpy as np
import pandas as pd
from fed_cp_ot.weekly import TYPES, MATS

def make_vol(start, end, seed=0, extra=None):
    """Weekdays from start to end for the 4 types x 6 buckets x (D, N). `extra` = (dates, factor) rows appended with extreme values."""
    rng = np.random.default_rng(seed)
    days = pd.bdate_range(start, end)
    base = {t: rng.dirichlet(np.ones(6) * 3) for t in TYPES}
    rows = []
    for t in TYPES:
        p = base[t].copy()
        for d in days:
            if d.dayofweek == 0: p = np.abs(0.8 * p + 0.2 * rng.dirichlet(np.ones(6) * 2)); p /= p.sum()
            tot = 5000 * rng.uniform(0.5, 1.5)
            n = np.maximum((p * 60).round(), 1)
            for j, m in enumerate(MATS):
                rows.append((f'{t}.{m}.AMT', t, m, 'D', d, True, float(round(tot * p[j]))))
                rows.append((f'{t}.{m}.VOL', t, m, 'N', d, True, float(n[j])))
    df = pd.DataFrame(rows, columns=['series', 'cp_type', 'mat', 'vt', 'date', 'valid', 'value'])
    if extra is not None:
        dates, factor = extra
        add = df[df.date == df.date.max()].copy()
        parts = []
        for d in dates:
            x = add.copy(); x['date'] = pd.Timestamp(d); x['value'] = x.value * factor; parts.append(x)
        df = pd.concat([df] + parts, ignore_index=True)
    return df
