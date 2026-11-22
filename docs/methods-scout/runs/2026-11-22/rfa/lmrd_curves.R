suppressMessages(library(lmom))
t3 <- seq(-0.3,0.6,by=0.01)
# Hosking polynomial approximations for t4(t3) are what lmrd() plots; reproduce via lmom's own fitted parameters
f <- function(pel,lmr){ sapply(t3, function(s){ p <- tryCatch(pel(c(1,0.1,s,0)), error=function(e) NA); if(any(is.na(p))) return(NA); lmr(p,nmom=4)[4] }) }
out <- data.frame(t3=t3, GLO=f(pelglo,lmrglo), GEV=f(pelgev,lmrgev), GNO=f(pelgno,lmrgno), PE3=f(pelpe3,lmrpe3), GPA=f(pelgpa,lmrgpa))
write.csv(out,'lmrd_curves.csv',row.names=FALSE)
