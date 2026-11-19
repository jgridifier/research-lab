suppressMessages({library(ape);library(phylobase);library(phylosignal);library(adephylo);library(jsonlite)})
set.seed(20261119)
args <- commandArgs(TRUE); f <- args[1]
d <- read.csv(paste0(f,'_q2.csv'), stringsAsFactors=FALSE); rownames(d) <- d$tip
out <- list()
for(tn in c('label','text')){
  tr <- read.tree(paste0(f,'_',tn,'.nwk')); tr <- collapse.singles(tr)
  if(tn=='text') tr$edge.length <- pmax(tr$edge.length,1e-6)
  dd <- d[tr$tip.label,]
  p4 <- phylo4d(tr, tip.data=dd[,c('slope','slope_true','slope_early','slope_late')])
  t0 <- Sys.time()
  ps <- phyloSignal(p4, methods=c("Cmean","I","K","Lambda"), reps=999)
  out[[tn]] <- list(stat=ps$stat, pvalue=ps$pvalue, sec=as.numeric(Sys.time()-t0,units='secs'), ultrametric=is.ultrametric(tr), ntip=Ntip(tr))
  print(tn); print(ps$stat); print(ps$pvalue)
  if(tn=='label'){
    t0 <- Sys.time()
    L <- lipaMoran(p4, trait=c('slope','slope_early','slope_late'), reps=999, alternative='two-sided', prox.phylo='patristic')
    lip <- data.frame(tip=tr$tip.label, L$lipa, p=L$p.value); names(lip) <- c('tip','lipa','lipa_early','lipa_late','p','p_early','p_late')
    # neighbour mean (patristic proximity, same weights) for walk-forward and peer comparisons
    W <- proxTips(tr, method='patristic'); diag(W) <- 0; W <- W/rowSums(W)
    lip$nb_slope <- as.numeric(W %*% dd$slope); lip$nb_slope_tr <- as.numeric(W %*% dd$slope_tr); lip$nb_gprev <- as.numeric(W %*% dd$g_prev)
    lip$nb_early <- as.numeric(W %*% dd$slope_early); lip$nb_late <- as.numeric(W %*% dd$slope_late)
    write.csv(lip, paste0(f,'_lipa.csv'), row.names=FALSE)
    out$lipa_sec <- as.numeric(Sys.time()-t0,units='secs')
  }
}
write_json(out, paste0(f,'_signal.json'), auto_unbox=TRUE, digits=NA)
