suppressMessages({library(netrankr); library(igraph); library(jsonlite)})
P <- matrix(c(0,0,1,1,1, 0,0,0,1,0, 0,0,0,0,1, rep(0,10)),5,5,byrow=TRUE)
r <- exact_rank_prob(P)
out <- list(ex5=list(P=P, lin_ext=r$lin.ext, expected=r$expected.rank, rank_prob=r$rank.prob, relative=r$relative.rank))
data("dbces11")
Pd <- neighborhood_inclusion(dbces11)
ri <- rank_intervals(Pd)
print(ri)
out$dbces11_intervals <- ri
rd <- exact_rank_prob(Pd)
out$dbces11 <- list(lin_ext=rd$lin.ext, expected=rd$expected.rank)
print(r$lin.ext); print(r$expected.rank); print(rd$lin.ext); print(round(rd$expected.rank,3))
# random posets for parity with Python brute force
set.seed(20261119)
rp <- list()
for(k in 1:20){ n <- sample(5:9,1); X <- matrix(runif(n*2),n,2)
  M <- matrix(0,n,n); for(i in 1:n) for(j in 1:n) if(i!=j && all(X[i,]<=X[j,]) && any(X[i,]<X[j,])) M[i,j] <- 1
  e <- exact_rank_prob(M); rp[[k]] <- list(P=M, expected=e$expected.rank, rank_prob=e$rank.prob, lin_ext=e$lin.ext) }
out$random <- rp
write_json(out,'home_repro_R.json',digits=NA,auto_unbox=TRUE,pretty=FALSE)
