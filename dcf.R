require(tidyverse)

diskontsatz=0.025

cf = data.frame(year=seq(2020,2119), cf=rep(5, 100))
cf %>% summarize(s=sum(cf*1/((1+diskontsatz)^(year-2020))))

