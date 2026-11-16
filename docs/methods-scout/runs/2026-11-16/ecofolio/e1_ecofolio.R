# Methods scout 2026-11-16 — ecofolio (mean-variance portfolio effect, Taylor's power law) on SYNTHETIC mock ZBB data (Q2)
suppressPackageStartupMessages({library(ecofolio); library(jsonlite)})
set.seed(20261116)
SRC <- '/workspace/q2-mock-zbb/output/'
detr <- function(X){ t <- seq_len(nrow(X)); Z <- cbind(1,t); M <- diag(nrow(X)) - Z %*% solve(crossprod(Z), t(Z)); M %*% X }
# fast mean-variance PE (linear Taylor fit on linearly detrended variances) = ecofolio::pe_mv(type='linear_detrended'); parity checked below
pe_fast <- function(X){ R <- detr(X); m <- colMeans(X); v <- colSums(R^2)/(nrow(X)-1); lm_ <- .lm.fit(cbind(1,log(m)), log(v))$coefficients
  tot <- rowSums(X); mt <- mean(tot); sdp <- sqrt(sum(detr(matrix(tot))^2)/(nrow(X)-1)); (sqrt(exp(lm_[1]+lm_[2]*log(mt)))/mt)/(sdp/mt) }
sync_fast <- function(X){ R <- detr(X); var(rowSums(R))/(sum(sqrt(colSums(R^2)/(nrow(X)-1))))^2 }
load_firm <- function(f){
  h <- read.csv(paste0(SRC,f,'/history.csv')); p <- read.csv(paste0(SRC,f,'/programs.csv'))
  mk <- function(col){ w <- reshape(h[,c('program_id','fiscal_year',col)], idvar='fiscal_year', timevar='program_id', direction='wide')
    w <- w[order(w$fiscal_year),]; colnames(w) <- sub(paste0(col,'.'),'',colnames(w),fixed=TRUE); X <- as.matrix(w[,-1]); rownames(X) <- w$fiscal_year; X }
  A <- mk('actual_usd'); B <- mk('budget_usd'); keep <- colSums(is.na(A))==0
  A <- A[,keep]/1e6; B <- B[,colnames(A)]/1e6
  g <- fromJSON(paste0(SRC,f,'/ground_truth.json'), simplifyVector=FALSE)
  T <- sapply(colnames(A), function(id) sapply(rownames(A), function(y) g$true_levels_by_program_year[[id]][[y]]$true_usd))/1e6
  list(A=A, B=B, T=T, p=p[match(colnames(A), p$program_id),], g=g, n_all=length(unique(h$program_id)))
}
taylor_d <- function(X){ m <- colMeans(X); v <- apply(detr(X),2,var); f <- lm(log(v)~log(m)); list(a=coef(f)[[1]], z=coef(f)[[2]], z_se=coef(summary(f))[2,2], r2=summary(f)$r.squared, resid=residuals(f)) }
res <- list()
for (f in c('Corning_mock','MorganStanley_mock')){
  D <- load_firm(f); X <- D$A; R <- list(n_balanced=ncol(X), n_programs=D$n_all, years=rownames(X))
  # ---------- A1: portfolio effect, mean-variance vs average-CV (and finance diversification ratio)
  t0 <- Sys.time()
  R$A1 <- list(
    taylor_raw = fit_taylor(X, ci=TRUE), taylor_detr = taylor_d(X)[c('a','z','z_se','r2')],
    taylor_true_detr = taylor_d(D$T)[c('a','z','z_se','r2')], taylor_budget_detr = taylor_d(D$B)[c('a','z','z_se','r2')],
    pe_mv_linear = pe_mv(X,'linear',ci=TRUE), pe_mv_detr = pe_mv(X,'linear_detrended',ci=TRUE),
    pe_mv_robust = pe_mv(X,'linear_robust'), pe_mv_quad = pe_mv(X,'quadratic'),
    pe_mv_detr_true = pe_mv(D$T,'linear_detrended'),
    pe_cv_raw = pe_avg_cv(X, ci=TRUE, boot_reps=500), pe_cv_detr = pe_avg_cv(X, detrending='linear_detrended'),
    pe_cv_detr_true = pe_avg_cv(D$T, detrending='linear_detrended'),
    sync_detr = synchrony(detr(X)), div_ratio_detr = 1/sqrt(synchrony(detr(X))),
    mean_program = mean(colMeans(X)), max_program = max(colMeans(X)), mean_total = mean(rowSums(X)))
  R$A1$extrap_decades <- log10(R$A1$mean_total/R$A1$max_program)
  R$A1$parity_fast_vs_pkg <- abs(pe_fast(X)-pe_mv(X,'linear_detrended')); R$A1$time_fast_ms <- 1000*system.time(for(k in 1:20) pe_fast(X))[['elapsed']]/20; R$A1$time_pkg_ms <- 1000*system.time(for(k in 1:5) pe_mv(X,'linear_detrended'))[['elapsed']]/5
  R$A1$runtime_ms <- 1000*as.numeric(difftime(Sys.time(),t0,units='secs'))
  # LOYO stability of z
  R$A1$z_loyo <- sapply(seq_len(nrow(X)), function(k) taylor_d(X[-k,])$z)
  # segment table
  segs <- unique(D$p$segment)
  R$A1$segments <- do.call(rbind, lapply(segs, function(s){ i <- D$p$segment==s; Xs <- X[,i]
    data.frame(segment=s, n=sum(i), z=taylor_d(Xs)$z, pe_mv=pe_mv(Xs,'linear_detrended'), pe_cv=pe_avg_cv(Xs,detrending='linear_detrended'),
      div_ratio=1/sqrt(synchrony(detr(Xs))), pe_mv_true=pe_mv(D$T[,i],'linear_detrended')) }))
  # ---------- A2: nulls and structure screen
  # (i) year-shuffle null: permute each program's years independently (kills synchrony, keeps each program's mean/variance)
  t1 <- Sys.time()
  nullp <- replicate(999, { Xp <- apply(X,2,sample); pe_fast(Xp) })
  R$A2 <- list(shuffle_null = list(obs=pe_mv(X,'linear_detrended'), null_median=median(nullp), null_q05=unname(quantile(nullp,.05)), null_q95=unname(quantile(nullp,.95)), p_low=(1+sum(nullp<=pe_mv(X,'linear_detrended')))/1000),
               shuffle_runtime_s = as.numeric(difftime(Sys.time(),t1,units='secs')))
  # (ii) group screen: subsegment, stated_driver, function; matched random-set null (same size, same firm)
  yoy <- diff(log(X)); 
  grp_stat <- function(idx){ Xs <- X[,idx,drop=FALSE]; cc <- cor(yoy[,idx]); c(pe=pe_fast(Xs), rho=mean(cc[upper.tri(cc)]), dr=1/sqrt(sync_fast(Xs))) }
  clus <- D$g$latent_clusters; memb <- list(); for (cl in clus) for (m in cl$members) memb[[m$program_id]] <- c(cluster=cl$cluster_id, type=cl$type, loading=m$loading)
  incl <- colnames(X) %in% names(memb)
  screen <- NULL
  for (gv in c('subsegment','stated_driver','function')){
    for (lv in unique(D$p[[gv]])){ idx <- which(D$p[[gv]]==lv); if (length(idx) < 8) next
      ob <- grp_stat(idx); nl <- replicate(299, grp_stat(sample.int(ncol(X), length(idx))))
      screen <- rbind(screen, data.frame(grouping=gv, level=lv, n=length(idx), pe=ob[['pe']], pe_pct=mean(nl['pe',]<=ob[['pe']]),
         rho=ob[['rho']], rho_pct=mean(nl['rho',]<=ob[['rho']]), dr=ob[['dr']], dr_pct=mean(nl['dr',]<=ob[['dr']]), share_cluster=mean(incl[idx]))) } }
  R$A2$screen <- screen
  # planted clusters as positive controls (balanced members only); tradeoff clusters split by loading sign
  pc <- NULL
  for (cl in clus){ ids <- sapply(cl$members, `[[`, 'program_id'); ld <- sapply(cl$members, `[[`, 'loading')
    sets <- list(all=ids); if (cl$type=='tradeoff'){ sets$pos <- ids[ld>0]; sets$neg <- ids[ld<0] }
    for (nm in names(sets)){ idx <- which(colnames(X) %in% sets[[nm]]); if (length(idx)<8) next
      ob <- grp_stat(idx); nl <- replicate(299, grp_stat(sample.int(ncol(X), length(idx))))
      pc <- rbind(pc, data.frame(cluster=cl$cluster_id, type=cl$type, subset=nm, n=length(idx), pe=ob[['pe']], pe_pct=mean(nl['pe',]<=ob[['pe']]), rho=ob[['rho']], rho_pct=mean(nl['rho',]<=ob[['rho']]), dr=ob[['dr']], dr_pct=mean(nl['dr',]<=ob[['dr']]))) } }
  R$A2$planted <- pc
  # ---------- A3: Taylor residual as a size-aware volatility flag vs CV (standard)
  td <- taylor_d(X); cvd <- apply(detr(X),2,sd)/colMeans(X)
  # truth: share of each program's detrended TRUE variance relative to its observed; "real movers" = cluster members with |loading| x factor range in top tercile, or category-drift programs
  fr <- sapply(clus, function(cl) diff(range(unlist(cl$factor_by_year)))); names(fr) <- sapply(clus, `[[`, 'cluster_id')
  amp <- sapply(colnames(X), function(id) if (!is.null(memb[[id]])) abs(as.numeric(memb[[id]][['loading']]))*fr[[memb[[id]][['cluster']]]] else 0)
  drift <- colnames(X) %in% sapply(D$g$category_drift, `[[`, 'program_id')
  true_cv <- apply(detr(D$T),2,sd)/colMeans(D$T); true_resid <- taylor_d(D$T)$resid
  auc <- function(s, lab){ r <- rank(s); n1 <- sum(lab); n0 <- sum(!lab); (sum(r[lab]) - n1*(n1+1)/2)/(n1*n0) }
  mover <- amp >= quantile(amp[amp>0], 1/3) & amp>0
  R$A3 <- list(n_movers=sum(mover), n_drift=sum(drift),
    auc_mover = c(taylor_resid=auc(td$resid, mover), cv=auc(cvd, mover), var=auc(apply(detr(X),2,var), mover)),
    spearman_with_true = c(taylor_resid_vs_true_resid = cor(td$resid, true_resid, method='spearman'), cv_vs_true_cv=cor(cvd, true_cv, method='spearman'),
                           taylor_resid_vs_true_cv = cor(td$resid, true_cv, method='spearman'), cv_vs_true_resid=cor(cvd,true_resid,method='spearman')),
    size_corr = c(taylor_resid=cor(td$resid, log(colMeans(X)), method='spearman'), cv=cor(cvd, log(colMeans(X)), method='spearman')),
    top50_movers = c(taylor_resid=sum(mover[order(-td$resid)[1:50]]), cv=sum(mover[order(-cvd)[1:50]])),
    top50_mean_size = c(taylor_resid=mean(colMeans(X)[order(-td$resid)[1:50]]), cv=mean(colMeans(X)[order(-cvd)[1:50]]), all=mean(colMeans(X))))
  write.csv(data.frame(log_mean=log(colMeans(X)), log_var_detr=log(apply(detr(X),2,var)), resid=td$resid, cv=cvd, segment=D$p$segment, mover=mover, cluster=sapply(colnames(X), function(id) if(is.null(memb[[id]])) '' else memb[[id]][['cluster']])),
            paste0('points_',f,'.csv'), row.names=FALSE)
  res[[f]] <- R; cat('done',f,'\n')
}
# home-field reproduction: pinkbr vignette values (pe_mv 1.412, pe_avg_cv 1.517, z near 2)
data(pinkbr); res$repro <- list(pe_mv=pe_mv(pinkbr[,-1]), pe_avg_cv=pe_avg_cv(pinkbr[,-1]), taylor=fit_taylor(pinkbr[,-1]), vignette=list(pe_mv=1.412, pe_avg_cv=1.517))
res$session <- capture.output(sessionInfo())
write_json(res, 'e1_results.json', auto_unbox=TRUE, digits=6, pretty=TRUE)
