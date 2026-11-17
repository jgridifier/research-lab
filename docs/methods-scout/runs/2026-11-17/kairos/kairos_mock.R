suppressMessages({library(kairos);library(tabula);library(dimensio);library(jsonlite)}); set.seed(20261117)
res <- list()
for (f in c('Corning_mock','MorganStanley_mock')) {
  X <- as.matrix(read.csv(paste0('mock_',f,'.csv'), row.names=1, check.names=FALSE))
  ser <- seriate_average(X, margin=c(1,2), axes=1); sig <- assess(ser, axes=1, n=1000, progress=FALSE)
  cax <- ca(X); rc <- get_coordinates(cax, margin=1)[,1]
  write.csv(data.frame(program_id=rownames(X), ca1=rc, ser_rank=match(seq_len(nrow(X)), order_rows(ser))), paste0('mockscore_',f,'_LOCAL_ONLY.csv'), row.names=FALSE)
  png(paste0('mock_eppm_',f,'.png'), width=900, height=1400, res=130); seriograph(X[order_rows(ser),]); dev.off()
  res[[f]] <- list(n_programs=nrow(X), years=colnames(X), porcic_observed=sig$observed, porcic_random_q05=unname(quantile(sig$random,.05)),
     porcic_p=(1+sum(sig$random<=sig$observed))/(1+length(sig$random)), ca1_pct=unname(get_eigenvalues(cax)[1,2]))
  cat(f,'done\n') }
write_json(res,'kairos_mock_results.json',auto_unbox=TRUE,pretty=TRUE,digits=6)
