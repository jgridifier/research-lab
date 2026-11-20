suppressMessages(library(NCA))
data(nca.example)
print(head(nca.example,3)); print(dim(nca.example))
set.seed(1)
m <- nca_analysis(nca.example, c(1,2), 3, ceilings=c("ce_fdh","cr_fdh"), test.rep=10000)
s <- m$summaries
out <- list()
for (nm in names(s)) { p <- s[[nm]]$params; print(nm); print(p) ; out[[nm]] <- p }
write.csv(nca.example, "nca_example.csv")
saveRDS(out,"home_params.rds")
sink("home_repro_out.txt"); print(m$summaries); sink()
