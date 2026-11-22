suppressMessages(library(lmomRFA)); set.seed(20261122)
data(Cascades)
t0 <- proc.time(); r <- regtst(Cascades, nsim=500); el <- (proc.time()-t0)[3]
out <- list(elapsed=el, D=round(r$D,2), wmeans=round(r$rmom[2:4],4), kappa=round(r$rpara,4), H=round(r$H,2), Z=round(r$Z,2), t4fit=round(r$t4fit,3),
  vobs=round(r$vobs,4), vbar=round(r$vbar,4), vsd=round(r$vsd,4), gno=round(r$para$gno,3), pe3=round(r$para$pe3,3), wak=round(r$para$wak,3))
Hs <- t(sapply(1:20, function(i){set.seed(i); x<-regtst(Cascades,nsim=500); c(x$H,x$Z[1:4])}))
out$HZ_seeds_mean <- round(colMeans(Hs),3); out$HZ_seeds_sd <- round(apply(Hs,2,sd),3)
print(out)
write.csv(as.data.frame(Cascades), "cascades_regdata.csv", row.names=FALSE)
jsonlite::write_json(out, "home_repro_R.json", auto_unbox=TRUE, digits=10)
