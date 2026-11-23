# P4: size and power of the synergy rule at the observed P1 shape (n=132), Gaussian sims.
import sys, json, numpy as np
sys.path.insert(0,'pid'); from pidcore import mmi_from_cov, idep_from_corr, copnorm
rng=np.random.default_rng(42)
def Sm(z): return mmi_from_cov(np.cov(z.T),len(z))['S']
def run(a,b,c,n=132,sims=300,NP=199,NB=300):
    C=np.array([[1,a,c],[a,1,b],[c,b,1.]]); L=np.linalg.cholesky(C); rej=0; rej_ci=0; rej_both=0; idep_ci=0
    for _ in range(sims):
        z=rng.standard_normal((n,3))@L.T; z=np.column_stack([copnorm(z[:,i]) for i in range(3)])
        s=Sm(z); I1=mmi_from_cov(np.cov(z.T),n)
        si,wi=(2,1) if I1['I2']>=I1['I1'] else (1,2)
        beta=np.polyfit(z[:,si],z[:,wi],1); res=z[:,wi]-np.polyval(beta,z[:,si]); cnt=0
        for _ in range(NP):
            zp=z.copy(); zp[:,wi]=np.polyval(beta,z[:,si])+rng.permutation(res)
            cnt+= Sm(zp)>=s
        p=(cnt+1)/(NP+1); bs=[]; bd=[]
        for _ in range(NB):
            zb=z[rng.integers(0,n,n)]; bs.append(Sm(zb)); R=np.corrcoef(zb.T); bd.append(idep_from_corr(R[1,2],R[0,1],R[0,2])['S'])
        lo=np.quantile(bs,.025); lod=np.quantile(bd,.025)
        rej+=p<0.05; rej_ci+=lo>0; rej_both+=(p<0.05)&(lo>0); idep_ci+=lod>1e-9
    return dict(abc=[a,b,c],true_mmi=mmi_from_cov(C),true_idep=idep_from_corr(b,a,c),fl_rate=rej/sims,ci_rate=rej_ci/sims,rule_rate=rej_both/sims,idep_ci_rate=idep_ci/sims,sims=sims)
out={'null_S0':run(-0.898*0.386,0.898,-0.386),'observed_shape':run(-0.198,0.898,-0.386),'half_effect':run(-0.27,0.898,-0.386)}
for k,v in out.items(): print(k,{kk:(round(vv,4) if isinstance(vv,float) else vv) for kk,vv in v.items() if kk not in('true_mmi','true_idep')},'trueS mmi',round(v['true_mmi']['S'],4),'idep',round(v['true_idep']['S'],4))
json.dump(out,open('pid/power_P1.json','w'),indent=1,default=float)
