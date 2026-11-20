suppressMessages(library(NCA)); d<-read.csv("nca_input.csv"); set.seed(2)
m<-nca_analysis(d, c("x_dd","x_pt","x_loss","x_cet1min"), "payout_rwa", ceilings=c("ce_fdh","cr_fdh"), test.rep=10000)
o<-sapply(m$summaries,function(s) c(d_ce=s$params[2,1], p_ce=s$params[6,1], d_cr=s$params[2,2], p_cr=s$params[6,2]))
print(o); write.csv(t(o),"parity_R.csv")
