# L-moment RFA on SYNTHETIC mock budget-miss ratios. lmomRFA 3.8.
suppressMessages({library(lmomRFA); library(jsonlite)}); set.seed(20261122)
run <- function(f, holdout=FALSE){
  X <- read.csv(paste0(f,'_x.csv')); P <- read.csv(paste0(f,'_programs_regions.csv'), row.names=1)
  if (holdout){ ly <- max(X$fiscal_year); X <- X[X$fiscal_year<ly,]; nn <- table(X$program_id); keep <- names(nn)[nn>=4]; X <- X[X$program_id %in% keep,]; P <- P[keep,] }
  Tr <- read.csv(paste0(f,'_truth.csv'), row.names=1); P$reg_O <- Tr[rownames(P),'reg_O']  # answer key: reference region only
  ids <- rownames(P); xs <- split(X$x, X$program_id)[ids]
  L <- regsamlmu(xs); L$t_5[is.na(L$t_5)] <- 0   # t_5 undefined for n=4; not used by D, H or Z (checked: identical output)
  site <- data.frame(program_id=ids, n=L$n, l1=L$l_1, t=L$t, t3=L$t_3, t4=L$t_4)
  res <- list(); reg_out <- list()
  for (sch in c('reg_A','reg_B','reg_C','reg_D','reg_O')){
    lab <- P[[sch]]; site[[paste0('D_',sch)]] <- NA; site[[paste0('q90_',sch)]] <- NA; site[[paste0('q10_',sch)]] <- NA
    for (g in unique(lab)){
      idx <- which(lab==g); rd <- L[idx,]
      tt <- regtst(rd, nsim=500)
      site[idx, paste0('D_',sch)] <- tt$D
      zbest <- names(which.min(abs(tt$Z[1:4])))
      fit <- regfit(rd, 'gno'); rgc <- regquant(c(0.1,0.9), fit)
      site[idx, paste0('q90_',sch)] <- rd$l_1*rgc[2]; site[idx, paste0('q10_',sch)] <- rd$l_1*rgc[1]
      reg_out[[length(reg_out)+1]] <- data.frame(scheme=sch, region=g, N=length(idx), H1=tt$H[1], H2=tt$H[2], H3=tt$H[3], zbest=zbest, Zgno=tt$Z['gno'],
         rt=tt$rmom[2], rt3=tt$rmom[3], rt4=tt$rmom[4], maxD=max(tt$D), nD3=sum(tt$D>=3), Dcrit=tt$Dcrit[1], rgc90=rgc[2])
    }
  }
  tag <- if (holdout) '_wf' else ''
  write.csv(site, paste0(f,'_site',tag,'.csv'), row.names=FALSE)
  write.csv(do.call(rbind, reg_out), paste0(f,'_regions',tag,'.csv'), row.names=FALSE)
}
t0 <- proc.time()
for (f in c('Corning_mock','MorganStanley_mock')) { run(f); run(f, holdout=TRUE) }
cat('elapsed', (proc.time()-t0)[3], '\n')
