# SYNTHETIC mock ZBB (Q2): programs x fiscal years of actual spend, programs observed every year. Answer key used only to score.
import json, pandas as pd, numpy as np
for f in ['Corning_mock','MorganStanley_mock']:
    h=pd.read_csv(f'/workspace/q2-mock-zbb/output/{f}/history.csv'); W=h.pivot(index='program_id',columns='fiscal_year',values='actual_usd').dropna()
    (W/1000).round(0).astype(int).to_csv(f'mock_{f}.csv')
    g=json.load(open(f'/workspace/q2-mock-zbb/output/{f}/ground_truth.json'))
    key={c['cluster_id']:{m['program_id']:m['loading'] for m in c['members']} for c in g['latent_clusters'] if c['n_members']>=20}
    json.dump(key,open(f'mockkey_{f}_LOCAL_ONLY.json','w'))
    print(f, W.shape)
