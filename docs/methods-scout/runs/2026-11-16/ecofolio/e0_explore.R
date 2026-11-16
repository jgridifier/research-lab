suppressPackageStartupMessages({library(ecofolio); library(jsonlite)})
SRC <- '/workspace/q2-mock-zbb/output/'
load_firm <- function(f){
  h <- read.csv(paste0(SRC,f,'/history.csv')); p <- read.csv(paste0(SRC,f,'/programs.csv'))
  yrs <- sort(unique(h$fiscal_year)); w <- reshape(h[,c('program_id','fiscal_year','actual_usd')], idvar='fiscal_year', timevar='program_id', direction='wide')
  w <- w[order(w$fiscal_year),]; colnames(w) <- sub('actual_usd.','',colnames(w)); X <- as.matrix(w[,-1]); rownames(X) <- w$fiscal_year
  X <- X[, colSums(is.na(X))==0]; list(X=X, p=p[match(colnames(X), p$program_id),], g=fromJSON(paste0(SRC,f,'/ground_truth.json'), simplifyVector=FALSE))
}
for (f in c('Corning_mock','MorganStanley_mock')){
  D <- load_firm(f); X <- D$X/1e6; cat('\n==',f,dim(X),'\n')
  for (ty in c('linear','linear_detrended')) { cat(ty,'PEmv', unlist(pe_mv(X,type=ty,ci=TRUE)),'\n') }
  cat('avgCV', pe_avg_cv(X), pe_avg_cv(X,detrending='linear_detrended'),'\n')
  cat('taylor raw', unlist(fit_taylor(X,ci=TRUE)),'\n')
  Xd <- apply(X,2,function(y) residuals(lm(y~seq_along(y)))); m<-colMeans(X); v<-apply(Xd,2,var); print(coef(summary(lm(log(v)~log(m)))))
  cat('synchrony raw',synchrony(X),' detr',synchrony(Xd),'\n')
  cat('mean prog $M', mean(m), 'total', mean(rowSums(X)),'\n')
  for (s in unique(D$p$segment)){ i <- D$p$segment==s; cat(sprintf('%-40s n=%4d z=%.2f PEmv_d=%.2f PEcv_d=%.2f sync_d=%.3f\n', s, sum(i), fit_taylor(Xd[,i]+0)$z, pe_mv(X[,i],type='linear_detrended'), pe_avg_cv(X[,i],detrending='linear_detrended'), synchrony(Xd[,i]))) }
}
