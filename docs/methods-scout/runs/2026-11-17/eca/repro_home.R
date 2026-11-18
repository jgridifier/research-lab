# Reproduce the two CoinCalc paper examples (Siegmund, Siegmund & Donges 2017; arXiv 1603.05038 Sec. 4.1-4.2)
suppressMessages(library(CoinCalc)); library(jsonlite)
data(CC.Example.Data1); data(CC.Example.Data2)
d1=CC.Example.Data1[CC.Example.Data1$YEAR>=1951 & CC.Example.Data1$YEAR<=2010,]
Fl=CC.binarize(data=d1$DOY_Lilac_Flowering, ev.def="percentile", thres=0.10, event="lower")
TT=CC.binarize(data=d1$April_Tmean, ev.def="percentile", thres=0.90, event="higher")
o1=CC.eca.ts(Fl,TT,sigtest="poisson"); print(o1)
d2=CC.Example.Data2
carb=CC.binarize(data=d2$SOCcontent, ev.def="percentile", thres=0.05, event="lower")
o2=CC.eca.ts(carb,d2$sorghum,sigtest="poisson"); print(o2)
write.csv(data.frame(Fl=Fl,TT=TT),"home_ex1_bin.csv",row.names=FALSE)
write.csv(data.frame(carb=carb,sorghum=d2$sorghum),"home_ex2_bin.csv",row.names=FALSE)
write_json(list(ex1=o1,ex2=o2),"home_repro.json",auto_unbox=TRUE,digits=10)
