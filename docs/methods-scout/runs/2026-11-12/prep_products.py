#!/usr/bin/env python3
"""PROXY product-line panel for lphom (products as 'voting units').
Source: public FR Y-9C (FFIEC/NIC BHCF) trading panel, box copy built for tracks/y9c-trading-ot
(/workspace/rl_check/tracks/y9c-trading-ot/data/processed_v1_1/trading_panel.parquet).
Annual trading revenue by risk type = Q4 year-to-date value (HI Memo 9.a-e: interest rate, FX, equity,
commodity, credit). Six US dealer BHCs. Only aggregate shares are written; descriptive use only."""
import pandas as pd, numpy as np, json
p = pd.read_parquet('/workspace/rl_check/tracks/y9c-trading-ot/data/processed_v1_1/trading_panel.parquet')
BIG = {'JPM':1039502,'GS':2380443,'MS':2162966,'BAC':1073757,'C':1951350,'WFC':1120754}
inv = {v:k for k,v in BIG.items()}
p['quarter'] = p['quarter'].astype(str)
p = p[p.rssd_id.isin(BIG.values()) & p.quarter.str.endswith('Q4')].copy()
p['year'] = p.quarter.str[:4].astype(int); p['dealer'] = p.rssd_id.map(inv)
prods = {'rates':'trd_interest_rate_ytd','fx':'trd_fx_ytd','equity':'trd_equity_ytd','commodity':'trd_commodity_ytd','credit':'trd_credit_ytd'}
rows = []
for pr, col in prods.items():
    w = p.pivot_table(index='year', columns='dealer', values=col, aggfunc='sum')[list(BIG)]
    for y, r in w.iterrows():
        rows.append(dict(product=pr, year=int(y), **{d: float(r[d]) if pd.notna(r[d]) else np.nan for d in BIG}))
df = pd.DataFrame(rows).sort_values(['product','year'])
df['all_pos'] = (df[list(BIG)] > 0).all(axis=1)
df.to_csv('/workspace/scout/1112/data/products_annual_raw.csv', index=False)   # box only, not published
sh = df.copy(); sh[list(BIG)] = sh[list(BIG)].div(sh[list(BIG)].sum(axis=1), axis=0)
summ = {pr: {'years_all_pos': sh[(sh['product']==pr) & sh.all_pos].year.tolist(),
             'share_first_last': sh[(sh['product']==pr) & sh.all_pos].iloc[[0,-1]][['year']+list(BIG)].round(4).to_dict('records')}
        for pr in prods}
json.dump(summ, open('/workspace/scout/1112/data/products_summary.json','w'), indent=1)
print(df.groupby('product').all_pos.agg(['sum','count'])); print(json.dumps(summ, indent=0)[:3000])
