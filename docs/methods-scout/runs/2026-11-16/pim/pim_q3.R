# Methods scout 2026-11-16 — probabilistic index models (pim) on public Q3 data. Descriptive; no forecasts.
suppressPackageStartupMessages({library(pim); library(jsonlite); library(sandwich)})
set.seed(20261116)
P0 <- read.csv('q3_pim_panel.csv')
NPERM <- as.integer(Sys.getenv('NPERM','499')); NBOOT <- as.integer(Sys.getenv('NBOOT','199'))
within_pairs <- function(yr){ do.call(rbind, lapply(split(seq_along(yr), yr), function(ix) if (length(ix)>1) t(combn(ix,2)) else NULL)) }
fit1 <- function(D, y, xs){
  f <- as.formula(paste(y,'~',paste(xs,collapse='+'))); cp <- within_pairs(D$year)
  m <- pim(f, data=D, compare=cp, link='logit', model='difference')
  list(coef=coef(m), se=sqrt(diag(vcov(m))), npairs=nrow(cp)) }
run <- function(label, D, y, xs, units=rep(1,length(xs)), perm=TRUE, boot=TRUE){
  D <- D[complete.cases(D[,c(y,xs,'year','id_rssd')]),]; D <- D[D$year %in% names(which(table(D$year)>1)),]
  t0 <- Sys.time(); F <- fit1(D,y,xs); rt <- as.numeric(difftime(Sys.time(),t0,units='secs'))
  out <- data.frame(analysis=label, outcome=y, covariate=xs, unit=units, n=nrow(D), firms=length(unique(D$id_rssd)), years=paste(range(D$year),collapse='-'), npairs=F$npairs,
                    beta=F$coef, se=F$se, PI=plogis(F$coef*units), p_sandwich=2*pnorm(-abs(F$coef/F$se)), fit_s=rt)
  if (perm){ zs <- replicate(NPERM, { Dp <- D; o <- unlist(lapply(split(seq_len(nrow(D)), D$year), function(ix) ix[sample.int(length(ix))]))
      ii <- unlist(split(seq_len(nrow(D)), D$year)); Dp[ii, xs] <- D[o, xs]; Fp <- tryCatch(fit1(Dp,y,xs), error=function(e) NULL); if (is.null(Fp)) rep(NA,length(xs)) else Fp$coef/Fp$se })
    zs <- matrix(zs, nrow=length(xs)); zo <- F$coef/F$se
    out$p_perm <- sapply(seq_along(xs), function(k) (1+sum(abs(zs[k,])>=abs(zo[k]), na.rm=TRUE))/(1+sum(!is.na(zs[k,])))) }
  if (boot){ firms <- unique(D$id_rssd); bs <- replicate(NBOOT, { s <- sample(firms, replace=TRUE)
      Db <- do.call(rbind, lapply(seq_along(s), function(k){ r <- D[D$id_rssd==s[k],]; r$id_rssd <- k; r }))
      Fb <- tryCatch(fit1(Db,y,xs), error=function(e) NULL); if (is.null(Fb)) rep(NA,length(xs)) else Fb$coef })
    bs <- matrix(bs, nrow=length(xs))
    out$PI_lo <- plogis(units*apply(bs,1,quantile,.025,na.rm=TRUE)); out$PI_hi <- plogis(units*apply(bs,1,quantile,.975,na.rm=TRUE)) }
  # standard comparison: OLS with year fixed effects, firm-clustered SE
  fe <- if (length(unique(D$year))>1) '+factor(year)' else ''; lmf <- lm(as.formula(paste(y,'~',paste(xs,collapse='+'),fe)), data=D); V <- vcovCL(lmf, cluster=~id_rssd)
  out$ols_b <- coef(lmf)[xs]; out$ols_t <- coef(lmf)[xs]/sqrt(diag(V)[xs])
  out }
res <- list(); R <- list()
E1 <- P0[P0$year<=2019,]; E2 <- P0[P0$year>=2021,]
# ---- B1: Q3.1/Q3.2 cross-section, within-year pairs
R[[length(R)+1]] <- run('B1 all years', P0, 'payout_rwa', 'drawdown')
R[[length(R)+1]] <- run('B1 all years', P0, 'payout_rwa', 'income_pretax_net_rate')
R[[length(R)+1]] <- run('B1 all years joint', P0, 'payout_rwa', c('drawdown','income_pretax_net_rate'))
R[[length(R)+1]] <- run('B1 2013-2019', E1, 'payout_rwa', 'drawdown')
R[[length(R)+1]] <- run('B1 2021-2025', E2, 'payout_rwa', 'drawdown')
R[[length(R)+1]] <- run('B1 SCB era', E2, 'payout_rwa', 'scb')
R[[length(R)+1]] <- run('B1 SCB era joint', E2, 'payout_rwa', c('scb','drawdown'))
R[[length(R)+1]] <- run('B1 timing: next-year payouts', P0[P0$year<=2024,], 'payout_rwa_next', 'drawdown')
R[[length(R)+1]] <- run('B1 payout/NI (unstable ratio)', P0, 'payout_ni', 'drawdown')
# ---- B2: Q3.4 Adverse vs Severely Adverse gap, 2014-2019
G <- P0[P0$year>=2014 & P0$year<=2019,]
R[[length(R)+1]] <- run('B2 SA drawdown + SA-A gap', G, 'payout_rwa', c('drawdown','gap_dd'))
R[[length(R)+1]] <- run('B2 Adverse drawdown only', G, 'payout_rwa', 'dd_A')
R[[length(R)+1]] <- run('B2 SA drawdown only (same rows)', G[!is.na(G$dd_A),], 'payout_rwa', 'drawdown')
R[[length(R)+1]] <- run('B2 gap, next-year payouts', G, 'payout_rwa_next', c('drawdown','gap_dd'))
R[[length(R)+1]] <- run('B2 pre-tax SA + A-SA gap', G, 'payout_rwa', c('income_pretax_net_rate','gap_pt'))
# ---- B3: Q3.5 composition (dividends vs buybacks)
for (nm in c('div_rwa','bb_rwa','div_share')){
  R[[length(R)+1]] <- run(paste('B3 2013-2019'), E1, nm, 'drawdown')
  R[[length(R)+1]] <- run(paste('B3 2021-2025'), E2, nm, 'drawdown')
  R[[length(R)+1]] <- run(paste('B3 SCB era'), E2, nm, 'scb') }
R[[length(R)+1]] <- run('B3 timing: next-year div share', P0[P0$year<=2024,], 'div_share_next', 'drawdown')
TAB <- do.call(rbind, R); rownames(TAB) <- NULL
iqr <- sapply(TAB$covariate, function(v) IQR(P0[[v]], na.rm=TRUE)); TAB$iqr <- iqr; TAB$PI_iqr <- plogis(TAB$beta*iqr)
write.csv(TAB, 'pim_results.csv', row.names=FALSE)
# Dec 2020: alternative severe vs severely adverse (one cross-section, 2021 payouts = payout_rwa_next of 2020 rows)
Z <- P0[P0$year==2020 & !is.na(P0$dd_alt) & !is.na(P0$payout_rwa_next),]; Z$gap_alt <- Z$dd_alt - Z$dd_sa_dec
res$dec2020 <- tryCatch(run('B2 Dec 2020 alt-severe gap (2021 payouts)', Z, 'payout_rwa_next', c('dd_sa_dec','gap_alt'), boot=FALSE), error=function(e) conditionMessage(e))
# OLS fragility on payout/NI vs PIM: drop the 2% most extreme payout/NI values and refit
Q <- P0[complete.cases(P0[,c('payout_ni','drawdown')]),]; cut <- quantile(abs(Q$payout_ni), .98); Qt <- Q[abs(Q$payout_ni)<=cut,]
res$fragility <- list(n=nrow(Q), n_trim=nrow(Qt), cut=cut,
  ols_full=coef(lm(payout_ni~drawdown+factor(year),Q))[['drawdown']], ols_trim=coef(lm(payout_ni~drawdown+factor(year),Qt))[['drawdown']],
  pim_full=plogis(fit1(Q,'payout_ni','drawdown')$coef[[1]]), pim_trim=plogis(fit1(Qt,'payout_ni','drawdown')$coef[[1]]),
  ols_rwa_full=coef(lm(payout_rwa~drawdown+factor(year),Q))[['drawdown']])
# home-field reproduction: PIM with one binary covariate reproduces the Wilcoxon-Mann-Whitney probabilistic index (FEVData ships with pim)
data(FEVData); m <- pim(FEV~Smoke, data=FEVData); w <- wilcox.test(FEV~Smoke, data=FEVData)
res$repro <- list(pim_PI=unname(plogis(coef(m))), wmw_PI=unname(1 - w$statistic/(sum(FEVData$Smoke==0)*sum(FEVData$Smoke==1))))
# timing vs pairs (synthetic, labelled)
res$timing <- do.call(rbind, lapply(c(200,500,1000), function(n){ d <- data.frame(year=rep(1:10,each=n/10), x=rnorm(n)); d$y <- d$x+rnorm(n); d$id_rssd <- seq_len(n); t <- system.time(F <- fit1(d,'y','x'))[['elapsed']]; data.frame(n=n, pairs=F$npairs, sec=t) }))
res$session <- capture.output(sessionInfo())
write_json(res, 'pim_extra.json', auto_unbox=TRUE, digits=6, pretty=TRUE)
print(TAB[,c('analysis','outcome','covariate','n','PI','p_sandwich','p_perm','PI_lo','PI_hi','ols_b','ols_t')], digits=3)
str(res[c('dec2020','fragility','repro','timing')])
