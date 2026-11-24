"""Public aggregate series (lab copies on the box). Log first differences, standardised."""
import numpy as np, pandas as pd
W = pd.read_csv('/workspace/ms-1114/q1/weekly.csv', parse_dates=['date']).set_index('date')
N_MISSING_WEEKS = int(len(pd.date_range(W.index[0], W.index[-1], freq='W-WED')) - len(W))
W = W.reindex(pd.date_range(W.index[0], W.index[-1], freq='W-WED')).interpolate()  # missing weeks: linear interpolation of levels
M = pd.read_csv('/workspace/ms-1114/q1/monthly.csv'); M.index = pd.PeriodIndex(M.period, freq='M')
def dlog(s): return np.log(s).diff()
def wk(c): return dlog(W[c])
def mo(c): return dlog(M[c])
WEEKLY = {'fails': wk('fails_fin_ust'), 'dvp': wk('dvp_out'), 'tri': wk('tri_tvol')}
MONTHLY = {'pb': mo('Secured_Prime Broker'), 'rr': mo('Secured_Reverse Repo'), 'fails': mo('fails_fin_ust'),
           'dvp': mo('dvp_out'), 'tri': mo('tri_tvol')}
PAIRS = [('W1', 'weekly', 'fails', 'dvp'), ('W2', 'weekly', 'fails', 'tri'), ('W3', 'weekly', 'dvp', 'tri'),
         ('M1', 'monthly', 'pb', 'fails'), ('M2', 'monthly', 'pb', 'rr'), ('M3', 'monthly', 'pb', 'dvp'), ('M4', 'monthly', 'pb', 'tri')]
PARAM = {'weekly': dict(nper=52, nover=26, fband=(1 / 26, 1 / 4)), 'monthly': dict(nper=24, nover=12, fband=(1 / 12, 1 / 4))}
def pair(freq, a, b):
    D = WEEKLY if freq == 'weekly' else MONTHLY
    df = pd.concat([D[a], D[b]], axis=1, keys=[a, b]).dropna()
    # contiguity check: index steps must be uniform
    idx = df.index
    gaps = (np.diff(idx.to_timestamp().values).astype('timedelta64[D]').astype(int) if freq == 'monthly' else np.diff(idx.values).astype('timedelta64[D]').astype(int))
    df.attrs['max_gap_days'] = int(gaps.max())
    return (df - df.mean()) / df.std()
if __name__ == '__main__':
    for p in PAIRS:
        d = pair(*p[1:]); print(N_MISSING_WEEKS, p, len(d), d.index[0], d.index[-1], d.attrs['max_gap_days'])
