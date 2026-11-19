# Home-field checks: (R1) Blomberg et al. 2003 expectation K ~ 1 under Brownian motion; lambda ~ 1. Star/white noise: K, lambda ~ 0.
suppressMessages({library(ape);library(phylobase);library(phylosignal);library(phytools);library(jsonlite)})
set.seed(20261119)
res <- list(bm=list(),wn=list())
for(s in 1:200){
  tr <- rcoal(100); x <- fastBM(tr); w <- rnorm(100); names(w) <- tr$tip.label
  p4 <- phylo4d(tr, tip.data=data.frame(bm=x[tr$tip.label], wn=w[tr$tip.label]))
  ps <- phyloSignal(p4, methods=c("K","Lambda"), reps=9)
  res$bm[[s]] <- c(K=ps$stat["bm","K"], L=ps$stat["bm","Lambda"]); res$wn[[s]] <- c(K=ps$stat["wn","K"], L=ps$stat["wn","Lambda"])
}
bm <- do.call(rbind,res$bm); wn <- do.call(rbind,res$wn)
out <- list(n_sims=200, n_tips=100, bm_K_mean=mean(bm[,1]), bm_K_median=median(bm[,1]), bm_lambda_median=median(bm[,2]),
            wn_K_mean=mean(wn[,1]), wn_lambda_median=median(wn[,2]))
# phytools cross-check of K on one sim
out$phytools_vs_phylosignal_K_maxdiff <- local({ tr <- rcoal(60); x <- fastBM(tr); p4 <- phylo4d(tr, tip.data=data.frame(x=x[tr$tip.label]))
  abs(as.numeric(phylosig(tr,x,method="K")) - as.numeric(phyloSignal(p4,methods="K",reps=9)$stat[1,1])) })
print(out); write_json(out,'home_repro.json',auto_unbox=TRUE,digits=NA)
