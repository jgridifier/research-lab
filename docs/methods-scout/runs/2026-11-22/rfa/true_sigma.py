# Re-derive the generator's per-program noise sigma (answer key; scoring only) by re-running its deterministic draws up to the history step.
import sys, json, numpy as np, pandas as pd
sys.path.insert(0,'/workspace/q2-mock-zbb/output'); import generate_q2_mock_zbb as G
out={}
for firm,name in [('GLW','Corning_mock'),('MS','MorganStanley_mock')]:
    rng=np.random.default_rng(G.SEED if firm=='GLW' else G.SEED+1)
    progs=G._build_from_archetypes(rng,firm); G.plant_mismatches_and_drift(rng,progs); hist=G.simulate_history(rng,progs,firm)
    sig={p.program_id:p.sigma_noise for p in progs}
    # validation: log(actual/budget) before raking == file (raking preserves the ratio)
    h=pd.read_csv(f'/workspace/q2-mock-zbb/output/{name}/history.csv')
    mine={(r.program_id,r.fiscal_year):np.log(r.actual_usd/r.budget_usd) for rows in hist.values() for r in rows}
    d=np.array([np.log(a/b)-mine[(p,y)] for p,y,a,b in zip(h.program_id,h.fiscal_year,h.actual_usd,h.budget_usd)])
    print(name,len(sig),'rows',len(h),'max |dlog ratio| vs file',np.abs(d).max())
    pd.Series(sig,name='sigma').rename_axis('program_id').to_csv(f'{name}_true_sigma.csv')
    out[name]=dict(n=len(sig),max_abs_diff=float(np.abs(d).max()),sigma_values=sorted(set(round(v,4) for v in sig.values())))
json.dump(out,open('true_sigma_meta.json','w'),indent=1); print(out)
