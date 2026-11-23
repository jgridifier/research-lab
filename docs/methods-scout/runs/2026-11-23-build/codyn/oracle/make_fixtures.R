# SYNTHETIC fixture generator; codyn 2.0.6 as oracle. Writes oracle/fixture.json
suppressPackageStartupMessages({library(codyn); library(jsonlite)})
set.seed(20261123)
Tn <- 25; S <- 30
M <- matrix(round(rexp(Tn * S, 1/50) + 1), Tn, S)           # integer abundances -> many ties
M[sample(length(M), 60)] <- 0                              # zeros (present, abundance 0)
M[, 5] <- M[, 6]                                            # two identical species -> ties across
absent <- matrix(FALSE, Tn, S); absent[1:6, 3] <- TRUE; absent[10:12, 17] <- TRUE; absent[25, 30] <- TRUE
td <- do.call(rbind, lapply(seq_len(S), function(s) data.frame(t = seq_len(Tn), species = sprintf("sp%02d", s),
        abundance = as.numeric(M[, s]), absent = absent[, s])))
td <- td[!td$absent, ]; td$absent <- NULL                   # absent = no row
vr <- variance_ratio(td, "t", "species", "abundance", bootnumber = 5)$VR
rc <- as.numeric(rate_change(td, "t", "species", "abundance"))
rs <- rank_shift(td, "t", "species", "abundance")
# codyn orders pairs as factor/alphabetical strings; reorder numerically
rs$a <- as.integer(sub("-.*", "", rs$year_pair)); rs <- rs[order(rs$a), ]
Xna <- M; Xna[absent] <- NA
write_json(list(note = "SYNTHETIC", seed = 20261123, T = Tn, S = S,
  X = lapply(seq_len(Tn), function(i) ifelse(is.na(Xna[i, ]), NA, Xna[i, ])),
  vr = vr, rate_change = rc, rank_shift = rs$MRS, mrs_mean = mean(rs$MRS)),
  "oracle/fixture.json", digits = NA, na = "null", auto_unbox = TRUE)

# Real-panel oracle (aggregates only): raw VR, share rate_change, share MRS, plus
# a 999-draw codyn VR null timing for panel A
sh <- function(w){sp<-setdiff(names(w),"q"); w[sp] <- w[sp]/rowSums(w[sp]); w}
tidy <- function(w) {sp <- setdiff(names(w), "q"); do.call(rbind, lapply(sp, function(s)
  data.frame(t = seq_len(nrow(w)), species = s, abundance = w[[s]])))}
out <- list()
for (p in c("A", "E4")) {
  w <- read.csv(sprintf("/workspace/scout/1112-adhoc/data/panel_%s.csv", p), check.names = FALSE)
  rs <- rank_shift(tidy(sh(w)), "t", "species", "abundance")
  out[[p]] <- list(vr_raw = variance_ratio(tidy(w), "t", "species", "abundance", bootnumber = 5)$VR,
    rate_change_shares = as.numeric(rate_change(tidy(sh(w)), "t", "species", "abundance")),
    mrs_shares = mean(rs$MRS))
}
wA <- read.csv("/workspace/scout/1112-adhoc/data/panel_A.csv", check.names = FALSE)
set.seed(1)
tm <- system.time(v <- variance_ratio(tidy(wA), "t", "species", "abundance", bootnumber = 999))[["elapsed"]]
out$timing_R_A_999 <- tm
out$A_null_R <- as.list(v)
write_json(out, "oracle/panels_oracle.json", digits = NA, auto_unbox = TRUE)
