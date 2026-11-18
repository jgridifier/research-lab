suppressMessages(library(ade4)); library(jsonlite); out=list()
for(nm in c('w1','w2')){
 D=read.csv(sprintf('bal_%s.csv',nm),row.names=1); K=ncol(D)/7
 kt=ktab.data.frame(D,blocks=rep(7,K),tabnames=paste0('t',1:K))
 # standardise each table's columns (normed PCA), as in withinpca-free statis on scaled ranks
 for(k in 1:K){ kt[[k]]=as.data.frame(scale(kt[[k]])*sqrt(nrow(D)/(nrow(D)-1))) }
 st=statis(kt,scannf=FALSE,nf=3)
 out[[nm]]=list(RV=st$RV, tabw=st$RV.tabw, C.eig=st$C.eig, n=nrow(D), K=K, Cli=as.matrix(st$C.li), Tli=as.matrix(st$C.Co))
}
write_json(out,'ade4_statis.json',digits=12,auto_unbox=TRUE)
