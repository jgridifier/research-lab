suppressMessages(library(CoinCalc)); library(jsonlite)
E=read.csv('events_q90.csv'); out=list()
pairs=list(c('fails','spread'),c('spread','fails'),c('fails','levbuild'),c('fails','levunwind'),c('spread','levbuild'),c('spread','levunwind'),c('dvp','fails'),c('fails','dvp'))
for(p in pairs){ S=E; if(any(grepl('lev',p))) S=E[as.Date(E$date)<=as.Date('2025-12-31'),]; S=S[complete.cases(S[,p]),]
 for(tau in c(0,2,4)){ o=CC.eca.ts(S[[p[1]]],S[[p[2]]],delT=1,tau=tau,sigtest='poisson')
  out[[length(out)+1]]=list(A=p[1],B=p[2],tau=tau,rp=o[['precursor coincidence rate']],rt=o[['trigger coincidence rate']],pp=o[['p-value precursor']],pt=o[['p-value trigger']])}}
write_json(out,'parity_ours_R.json',auto_unbox=TRUE,digits=12)
