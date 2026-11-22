# Size/power of H1 vs Brown-Forsythe (Levene, median) for regions shaped like ours: N sites, record lengths 4-6, lognormal budget-miss ratios.
suppressMessages({library(lmomRFA); library(jsonlite)}); set.seed(20261122)
bf <- function(xs){ y <- unlist(lapply(xs, function(v) abs(log(v)-median(log(v))))); g <- factor(rep(seq_along(xs), sapply(xs,length))); anova(lm(y~g))[1,5] }
sim_region <- function(N, sig1, sig2, nrec){ s <- ifelse(seq_len(N) <= N/2, sig1, sig2); lapply(seq_len(N), function(i) exp(rnorm(nrec[i], 0.02-0.255*s[i]^2, 1.22066*s[i]))) }
X <- read.csv('Corning_mock_x.csv'); nrec_pool <- as.vector(table(X$program_id))
grid <- expand.grid(N=c(20,50,150), pair=c('0.085/0.085','0.085/0.105','0.085/0.15','0.085/0.18','0.105/0.18'), stringsAsFactors=FALSE)
res <- list(); raw <- list()
for (k in seq_len(nrow(grid))){
  N <- grid$N[k]; sg <- as.numeric(strsplit(grid$pair[k],'/')[[1]]); h <- c(); p <- c()
  for (r in 1:200){ nrec <- sample(nrec_pool, N, replace=TRUE); xs <- sim_region(N, sg[1], sg[2], nrec)
    L <- regsamlmu(xs); L$t_5[is.na(L$t_5)] <- 0; h <- c(h, regtst(L, nsim=200)$H[1]); p <- c(p, bf(xs)) }
  res[[k]] <- data.frame(N=N, pair=grid$pair[k], H1ge2=mean(h>=2), H1ge1=mean(h>=1), BF05=mean(p<0.05), medH1=median(h)); raw[[k]] <- data.frame(N=N,pair=grid$pair[k],H1=h,BFp=p)
  print(res[[k]])
}
R <- do.call(rbind,res); write.csv(R,"power_q2.csv",row.names=FALSE); write.csv(do.call(rbind,raw),"power_q2_raw.csv",row.names=FALSE)
