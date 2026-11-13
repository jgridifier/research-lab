## A3 variant: slope relative to same-group peers (segment x function), then ebnm with mode 0.
suppressMessages({library(ebnm); library(jsonlite)}); D <- "/workspace/scout/1113/data/"
out <- list()
for (firm in c("Corning_mock","MorganStanley_mock")) {
  F <- read.csv(paste0(D, firm, "_features.csv")); L <- read.csv(paste0(D, firm, "_KEY_labels.csv"))
  ok0 <- !is.na(F$slope); F <- F[ok0,]
  gmed <- ave(F$slope, F$group, FUN=median); gn <- ave(F$slope, F$group, FUN=length)
  F$rel <- F$slope - ifelse(gn>=4, gmed, median(F$slope))
  ok <- F$stated_intent %in% c("grow","transform")
  x <- F$rel[ok]; s <- F$sigma[ok]/sqrt(F$sxx[ok]); id <- F$program_id[ok]
  lab <- L$mismatch[match(id,L$program_id)]; pos <- !is.na(lab) & lab=="stated_growth_actually_declining"
  f <- ebnm(x, s, prior_family="normal_scale_mixture", mode=0, output=ebnm_output_all())
  auc <- function(score) { r <- rank(score); (sum(r[pos]) - sum(pos)*(sum(pos)+1)/2)/(sum(pos)*sum(!pos)) }
  pr <- function(fl) c(flagged=sum(fl), hits=sum(fl&pos), precision=if(sum(fl)) sum(fl&pos)/sum(fl) else NA, recall=sum(fl&pos)/sum(pos))
  zt <- x/s
  # top-k by posterior mean (k = number planted): precision at k
  k <- sum(pos); topk <- function(score) sum(pos[order(score)][1:k])/k
  tab <- rbind("Naive one-sided t, p<0.05"=pr(pnorm(zt)<0.05), "Naive + BH"=pr(p.adjust(pnorm(zt),"BH")<0.05), "ebnm: post.mean<0 & lfsr<0.05"=pr(f$posterior$mean<0 & f$posterior$lfsr<0.05))
  out[[firm]] <- list(table=as.data.frame(tab), auc=list(raw=auc(-x), naive_z=auc(-zt), ebnm=auc(-f$posterior$mean)), prec_at_k=list(k=k, raw=topk(x), naive_z=topk(zt), ebnm=topk(f$posterior$mean)),
     planted_stated_intent=as.list(table(F$stated_intent[F$program_id %in% L$program_id[L$mismatch %in% "stated_growth_actually_declining"]])))
  cat("==",firm,"\n"); print(tab); print(unlist(out[[firm]]$auc)); print(unlist(out[[firm]]$prec_at_k)); print(out[[firm]]$planted_stated_intent)
}
write_json(out, "/workspace/scout/1113/out/m1c_relative.json", auto_unbox=TRUE, digits=NA)
