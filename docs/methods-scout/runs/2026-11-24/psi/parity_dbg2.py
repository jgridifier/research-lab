import numpy as np, warnings; warnings.filterwarnings('ignore')
from mne_connectivity import spectral_connectivity_epochs, phase_slope_index
from psi_core import segments
rng=np.random.default_rng(3); n=2048; a=rng.normal(size=n+4); x=a[4:]+.3*rng.normal(size=n); y=.8*a[2:-2]+.5*rng.normal(size=n)
nper,nover=64,32; ep=np.stack([segments(x,nper,nover),segments(y,nper,nover)],1)
c=spectral_connectivity_epochs(ep,method='cohy',indices=([0],[1]),sfreq=1.0,mode='fourier',fmin=0.05,fmax=0.25,faverage=False,verbose=False)
ch=np.ravel(c.get_data()); fr=np.array(c.freqs); print(fr[:3],len(fr),ch[:2])
X=np.fft.rfft(ep[:,0],axis=1);Y=np.fft.rfft(ep[:,1],axis=1); f=np.fft.rfftfreq(nper)
Sxy=(X*np.conj(Y)).mean(0); C=Sxy/np.sqrt((abs(X)**2).mean(0)*(abs(Y)**2).mean(0))
m=(f>0.05)&(f<0.25)
print(len(C[m]), C[m][:2], 'conj', np.conj(C[m])[:2])
print('max diff to mne', np.abs(C[m]-ch).max(), np.abs(np.conj(C[m])-ch).max())
