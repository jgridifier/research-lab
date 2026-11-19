suppressMessages({library(netrankr);library(jsonlite)})
J <- fromJSON('posets_by_year.json'); res <- list()
for(y in names(J)){ M <- as.matrix(J[[y]]); t0 <- Sys.time(); e <- exact_rank_prob(M, force=TRUE)
  res[[y]] <- list(lin_ext=format(e$lin.ext,digits=17), expected=as.numeric(e$expected.rank), sec=as.numeric(Sys.time()-t0,units='secs')); cat(y, res[[y]]$sec, '\n') }
write_json(res,'parity_real_R.json',digits=NA,auto_unbox=TRUE)
