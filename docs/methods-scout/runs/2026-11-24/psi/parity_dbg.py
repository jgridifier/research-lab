import numpy as np, warnings; warnings.filterwarnings('ignore')
from mne_connectivity import phase_slope_index
from psi_core import segments, _psi_from
rng=np.random.default_rng(3); n=2048; a=rng.normal(size=n+4); x=a[4:]+.3*rng.normal(size=n); y=.8*a[2:-2]+.5*rng.normal(size=n)
nper,nover=64,32; ep=np.stack([segments(x,nper,nover),segments(y,nper,nover)],1)
f=np.fft.rfftfreq(nper)
for fmin,fmax in [(0.05,0.25),(0.0625,0.25)]:
    c=phase_slope_index(ep,indices=([0],[1]),sfreq=1.0,mode='fourier',fmin=fmin,fmax=fmax,verbose=False)
    print('mne',fmin,fmax,float(np.ravel(c.get_data())[0]),getattr(c,'freqs',None)[:3] if hasattr(c,'freqs') else '')
    X=np.fft.rfft(ep[:,0],axis=1);Y=np.fft.rfft(ep[:,1],axis=1)
    for lo_op in ['left','right']:
        lo=int(np.searchsorted(f,fmin,lo_op)); hi=int(np.searchsorted(f,fmax,'right'))
        print('  mine bins',lo,hi,_psi_from(X,Y,(lo,hi)), 'swapped sign', _psi_from(Y,X,(lo,hi)))
c=phase_slope_index(ep,indices=([0],[1]),sfreq=1.0,mode='fourier',fmin=0.05,fmax=0.25,verbose=False); t=float(np.ravel(c.get_data())[0])
X=np.fft.rfft(ep[:,0],axis=1);Y=np.fft.rfft(ep[:,1],axis=1)
for lo in range(1,10):
    for hi in range(lo+2,30):
        v=_psi_from(X,Y,(lo,hi))
        if abs(v-t)<1e-9: print('match bins',lo,hi,v,t)
