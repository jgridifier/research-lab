import time, sys, importlib.util, json
t0=time.time()
src=open('pid/q3_pid.py').read().split("R={}")[0]
exec(src)
S21=D[D.year>=2021]; t1=time.time(); analyse(S21,'payout_rwa','scb','drawdown','timing P1'); t2=time.time()
json.dump(dict(seconds_one_triplet=t2-t1,NP=NP,NB=NB),open('pid/time_loop.json','w')); print('sec',t2-t1)
