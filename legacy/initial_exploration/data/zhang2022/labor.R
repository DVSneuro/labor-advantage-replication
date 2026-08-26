#########
# Code and data to reproduce analyses and figures in
#  Labor advantages drive the greater productivity of faculty at elite universities
#  by Sam Zhang, K. Hunter Wapman, Daniel B. Larremore, and Aaron Clauset
#########

# For matching, regressions, and clustering standard errors
library(MatchIt)
library(lme4)
library(sandwich)
library(fixest)
library(glmmTMB)
library(cobalt) # love.plot
library(Hmisc) # wtd.mean
library(lmtest) # coeftest

# For generating LaTeX tables
library(broom.mixed)
library(texreg)
library(xtable)

# For cross-validation
library(caret)

# For combining figures
library(patchwork)

# General tidyverse
library(ggplot2)
library(dplyr)
library(tidyverse)
library(directlabels) # for geom_dl

theme_set(theme_classic())
colors = c('#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854', '#ffd92f', '#e5c494', '#b3b3b3')

run.cv <- function(df, dvs, base.covariates, variants, k=10) {
  flds <- createFolds(df[, dvs[1]], k=10, list=TRUE, returnTrain=FALSE)
  col.dv <- c() 
  col.model <- c()
  col.variant <- c()
  col.mae <- c()
  
  for (i in 1:k) {
    train.X <- df[-flds[[i]], ] 
    test.X <- df[flds[[i]], ]
    
    for (dv in dvs) {
      test.Y <- df[flds[[i]], dv]
      
      for (variant in variants) {
        variant.name <- variant[[1]]
        variant.cols <- variant[[2]]
        
        form <- reformulate(unlist(c(base.covariates, variant.cols)), dv)
        mod.cv.pois <- fepois(form, train.X, cluster=c("Area"))
        mae.cv.mae <- mean(abs(test.Y - predict(mod.cv.pois, test.X)))
        
        col.dv <- c(col.dv, dv)
        col.model <- c(col.model, "pois")
        col.variant <- c(col.variant, variant.name)
        col.mae <- c(col.mae, mae.cv.mae)
      }
    }
  }

  cv.runs <- data.frame(list(dv=col.dv, model=col.model, variant=col.variant, mae=col.mae))
  cv.runs.avg <- cv.runs %>%
    group_by(dv, model, variant) %>%
    dplyr::summarize(mean_mae=mean(mae))
  
  cv.runs.avg.vs.base <- merge(cv.runs.avg %>% filter(variant == "base") %>% rename(mean_mae_base = "mean_mae") %>% select(-c("variant")), cv.runs.avg %>% filter(variant != "base"), by=c("dv", "model")) %>%
    mutate(perc_mae_decrease = 1 - mean_mae / mean_mae_base)
  
  cv.runs.avg.vs.base
}

################################
# Department regressions
#  (in the paper we renamed "Area" to "Discipline")
#
# area = strict linkage
################################

collab_norm_areas = c('Biological Sciences', 'Engineering', 'Medical Sciences',
                 'Psychological Sciences', 'Physical Sciences', 'Chemical Sciences',
                 'Computational Sciences', 'Health', 'Business', 'Earth Sciences',
                 'Agriculture', 'Architecture, Design, Planning')


area <- read.csv("./area-strict.csv")
area.nonstrict <- read.csv("./area-non-strict.csv") %>%
  mutate(AreaHasCollabNorm = Area %in% collab_norm_areas)

all_areas = unique(area.nonstrict$Area)
area_terms_to_omit <- paste("Area", all_areas, sep="")

ndepts_without_unfunded <- nrow(area_raw) - nrow(area)
prop_depts_without_unfunded <- (nrow(area_raw) - nrow(area)) / nrow(area)

# (Strict linkage data)
mod.area.collabs.pois.collabnorm.overall <- fepois(Productivity ~  scale_log_funded_per_faculty_p1 + scale_uniform_percentile100 + Area + scale_log_unfunded_per_faculty_p1 + scale_tt_headcount + CONTROL, area %>% filter(AreaHasCollabNorm==TRUE), cluster=c("Area"))
mod.area.collabs.pois.nocollabnorm.overall <- fepois(Productivity ~  scale_log_funded_per_faculty_p1 + scale_uniform_percentile100 + Area + scale_log_unfunded_per_faculty_p1 + scale_tt_headcount + CONTROL, area %>% filter(AreaHasCollabNorm==FALSE), cluster=c("Area"))
mod.area.collabs.pois.collabnorm <- fepois(ProductivityWithDeptCollabs ~  scale_log_funded_per_faculty_p1 + scale_uniform_percentile100 + Area + scale_log_unfunded_per_faculty_p1 + scale_tt_headcount + CONTROL, area %>% filter(AreaHasCollabNorm==TRUE), cluster=c("Area"))
mod.area.collabs.pois.nocollabnorm <- fepois(ProductivityWithDeptCollabs ~  scale_log_funded_per_faculty_p1 + scale_uniform_percentile100 + Area + scale_log_unfunded_per_faculty_p1 + scale_tt_headcount + CONTROL, area %>% filter(AreaHasCollabNorm==FALSE), cluster=c("Area"))
mod.area.collabs.pois.collabnorm.gs = fepois(WindowedGroupSize ~ scale_log_funded_per_faculty_p1 + scale_uniform_percentile100 + Area + scale_log_unfunded_per_faculty_p1 + scale_tt_headcount + CONTROL, area %>% filter(AreaHasCollabNorm==TRUE), cluster=c("Area"))
mod.area.collabs.pois.nocollabnorm.gs = fepois(WindowedGroupSize ~  scale_log_funded_per_faculty_p1 + scale_uniform_percentile100 + Area + scale_log_unfunded_per_faculty_p1 + scale_tt_headcount + CONTROL, area %>% filter(AreaHasCollabNorm==FALSE), cluster=c("Area"))

# Printing out tables for LaTeX
area.texreg.gs <- texreg(
  list(
    mod.area.collabs.pois.collabnorm.overall,
    mod.area.collabs.pois.collabnorm,
    mod.area.collabs.pois.collabnorm.gs,
    mod.area.collabs.pois.nocollabnorm.overall,
    mod.area.collabs.pois.nocollabnorm,
    mod.area.collabs.pois.nocollabnorm.gs
  ),
  custom.model.names=c("(p/c)", "(gp/c)", "(gs/c)", "(p/nc)", "(gp/nc)", "(gs/nc)"),
  custom.coef.map=list(CONTROL="Is private","scale_tt_headcount"="Num. faculty", "scale_uniform_percentile100"="Prestige", "scale_log_unfunded_per_faculty_p1"="Unfunded labor ratio", "scale_log_funded_per_faculty_p1"="Funded labor ratio"),
  omit.coef = area_terms_to_omit,
  include.aic=TRUE,
  include.bic=TRUE,
  include.pseudors=TRUE,
  include.loglik=FALSE,
  table=FALSE
)

# Regression on first and last author productivity
mod.area.collabs.pois.collabnorm.first = fepois(ProductivityFirstAuthor ~ scale_log_funded_per_faculty_p1 + scale_uniform_percentile100 + Area + scale_log_unfunded_per_faculty_p1 + scale_tt_headcount + CONTROL, area %>% filter(AreaHasCollabNorm==TRUE), cluster=c("Area"))
mod.area.collabs.pois.nocollabnorm.first = fepois(ProductivityFirstAuthor ~  scale_log_funded_per_faculty_p1 + scale_uniform_percentile100 + Area + scale_log_unfunded_per_faculty_p1 + scale_tt_headcount + CONTROL, area %>% filter(AreaHasCollabNorm==FALSE), cluster=c("Area"))
mod.area.collabs.pois.collabnorm.last = fepois(ProductivityLastAuthor ~ scale_log_funded_per_faculty_p1 + scale_uniform_percentile100 + Area + scale_log_unfunded_per_faculty_p1 + scale_tt_headcount + CONTROL, area %>% filter(AreaHasCollabNorm==TRUE), cluster=c("Area"))
mod.area.collabs.pois.nocollabnorm.last = fepois(ProductivityLastAuthor ~  scale_log_funded_per_faculty_p1 + scale_uniform_percentile100 + Area + scale_log_unfunded_per_faculty_p1 + scale_tt_headcount + CONTROL, area %>% filter(AreaHasCollabNorm==FALSE), cluster=c("Area"))

area.texreg.firstlast <- texreg(
  list(
    mod.area.collabs.pois.collabnorm.first,
    mod.area.collabs.pois.collabnorm.last,
    mod.area.collabs.pois.nocollabnorm.first,
    mod.area.collabs.pois.nocollabnorm.last
  ),
  custom.model.names=c("(first/c)", "(last/c)", "(first/nc)", "(last/nc)"),
  custom.coef.map=list(CONTROL="Is private","scale_tt_headcount"="Num. faculty", "scale_uniform_percentile100"="Prestige", "scale_log_unfunded_per_faculty_p1"="Unfunded labor ratio", "scale_log_funded_per_faculty_p1"="Funded labor ratio"),
  omit.coef = area_terms_to_omit,
  include.aic=TRUE,
  include.bic=TRUE,
  include.pseudors=TRUE,
  include.loglik=FALSE,
  table=FALSE
)

# Cross-validation
base.covariates <- c("scale_log_unfunded_per_faculty_p1", "scale_tt_headcount", "CONTROL", "Area")

variants <- list(
  list("base", list()),
  list("prestige", list("scale_uniform_percentile100")),
  list("labor", list("scale_log_funded_per_faculty_p1")),
  list("both", list("scale_uniform_percentile100", "scale_log_funded_per_faculty_p1"))
)

area.strict.cv <- run.cv(area %>% filter(AreaHasCollabNorm == TRUE), c("Productivity", "ProductivityWithDeptCollabs", "WindowedGroupSize", "ProductivityFirstAuthor", "ProductivityLastAuthor"), base.covariates, variants, k=10)
area.strict.cv.nocollab <- run.cv(area %>% filter(AreaHasCollabNorm == FALSE), c("Productivity", "ProductivityWithDeptCollabs", "WindowedGroupSize", "ProductivityFirstAuthor", "ProductivityLastAuthor"), base.covariates, variants, k=10)

# Non-strict linkage data
mod.area.nonstrict.collabs.pois.collabnorm.overall <- fepois(Productivity ~  scale_log_funded_per_faculty_p1 + scale_uniform_percentile100 + Area + scale_log_unfunded_per_faculty_p1 + scale_tt_headcount + CONTROL, area.nonstrict %>% filter(AreaHasCollabNorm==TRUE), cluster=c("Area"))
mod.area.nonstrict.collabs.pois.nocollabnorm.overall <- fepois(Productivity ~  scale_log_funded_per_faculty_p1 + scale_uniform_percentile100 + Area + scale_log_unfunded_per_faculty_p1 + scale_tt_headcount + CONTROL, area.nonstrict %>% filter(AreaHasCollabNorm==FALSE), cluster=c("Area"))
mod.area.nonstrict.collabs.pois.collabnorm <- fepois(ProductivityWithDeptCollabs ~  scale_log_funded_per_faculty_p1 + scale_uniform_percentile100 + Area + scale_log_unfunded_per_faculty_p1 + scale_tt_headcount + CONTROL, area.nonstrict %>% filter(AreaHasCollabNorm==TRUE), cluster=c("Area"))
mod.area.nonstrict.collabs.pois.nocollabnorm <- fepois(ProductivityWithDeptCollabs ~  scale_log_funded_per_faculty_p1 + scale_uniform_percentile100 + Area + scale_log_unfunded_per_faculty_p1 + scale_tt_headcount + CONTROL, area.nonstrict %>% filter(AreaHasCollabNorm==FALSE), cluster=c("Area"))
mod.area.nonstrict.collabs.pois.collabnorm.gs = fepois(WindowedGroupSize ~ scale_log_funded_per_faculty_p1 + scale_uniform_percentile100 + Area + scale_log_unfunded_per_faculty_p1 + scale_tt_headcount + CONTROL, area.nonstrict %>% filter(AreaHasCollabNorm==TRUE), cluster=c("Area"))
mod.area.nonstrict.collabs.pois.nocollabnorm.gs = fepois(WindowedGroupSize ~  scale_log_funded_per_faculty_p1 + scale_uniform_percentile100 + Area + scale_log_unfunded_per_faculty_p1 + scale_tt_headcount + CONTROL, area.nonstrict %>% filter(AreaHasCollabNorm==FALSE), cluster=c("Area"))

area.nostrict.cv <- run.cv(area %>% filter(AreaHasCollabNorm == TRUE), c("Productivity", "ProductivityWithDeptCollabs", "WindowedGroupSize"), base.covariates, variants, k=10)
area.nostrict.cv.nocollab <- run.cv(area.nocollabnorm, c("Productivity", "ProductivityWithDeptCollabs", "WindowedGroupSize"), base.covariates, variants, k=10)

area.nonstrict.texreg.gs <- texreg(
  list(
    mod.area.nonstrict.collabs.pois.collabnorm.overall,
    mod.area.nonstrict.collabs.pois.collabnorm,
    mod.area.nonstrict.collabs.pois.collabnorm.gs,
    mod.area.nonstrict.collabs.pois.nocollabnorm.overall,
    mod.area.nonstrict.collabs.pois.nocollabnorm,
    mod.area.nonstrict.collabs.pois.nocollabnorm.gs
  ),
  custom.model.names=c("(p/c)", "(gp/c)", "(gs/c)", "(p/nc)", "(gp/nc)", "(gs/nc)"),
  custom.coef.map=list(CONTROL="Is private","scale_tt_headcount"="Num. faculty", "scale_uniform_percentile100"="Prestige", "scale_log_unfunded_per_faculty_p1"="Unfunded labor ratio", "scale_log_funded_per_faculty_p1"="Funded labor ratio"),
  omit.coef = area_terms_to_omit,
  include.aic=TRUE,
  include.bic=TRUE,
  include.pseudors=TRUE,
  include.loglik=TRUE,
  table=FALSE
)

#####################
## Matching
#####################

do.matching <- function(df) {
  matchit(as.factor(UpwardMove) ~ (log(Productivity_x + 1)) + (log(ProductivityWithDeptCollabs_x + 1)) + (uniform_percentile_x)  + log(funded_per_faculty_x + 1) + (log(WindowedGroupSize_x + 1)) + Gender + Title_x + Area , df, method="full", exact=~Area, discard="both", reestimate=TRUE)
}

make.love.plot <- function(match.mod) {
  v = data.frame(old=c("log(Productivity_x + 1)",
                       "log(ProductivityWithDeptCollabs_x + 1)",
                       "uniform_percentile_x",
                       "log(WindowedGroupSize_x + 1)",
                       "log(funded_per_faculty_x + 1)"
                       ),
    new=c("Productivity",
          "Group prod.",
          "Prestige",
          "Group size",
          "Funded labor availability"))
  love.plot(bal.tab(match.mod), thresholds = c(m = .1), var.names=v) +
    labs(title="", y="Covariate") +
    theme(legend.position=c(0.7, 0.2), legend.background = element_blank(), legend.key = element_blank()) +
    scale_fill_manual(values = c(colors[4], colors[1])) +
    scale_color_manual(values = c(colors[4], colors[1]))
}

summarize.gs <- function(m.data) {
  m.data %>%
    pivot_longer(cols=c("WindowedGroupSize_x", "WindowedGroupSize_y"), names_to="WindowedGroupSize") %>%
    group_by(UpwardMove, WindowedGroupSize) %>%
    dplyr::summarize(
      mu=wtd.mean(value, weights=weights, normwt=TRUE),
      sigma=sqrt(wtd.var(value, weights=weights, normwt=TRUE)),
      se=sigma/sqrt(sum(weights))
    ) %>% mutate(
      Time = recode_factor(WindowedGroupSize, WindowedGroupSize_x="Before\nmove", WindowedGroupSize_y="After\nmove"),
      Direction = recode_factor(UpwardMove, "0"="Move to less labor", "1"="Move to more labor")
    )
}

summarize.gp <- function(m.data) {
  m.data %>%
    pivot_longer(cols=c("ProductivityWithDeptCollabs_x", "ProductivityWithDeptCollabs_y"), names_to="ProductivityWithDeptCollabs") %>%
    group_by(UpwardMove, ProductivityWithDeptCollabs) %>%
    dplyr::summarize(
      mu=wtd.mean(value, weights=weights, normwt=TRUE),
      sigma=sqrt(wtd.var(value, weights=weights, normwt=TRUE)),
      se=sigma/sqrt(sum(weights))
    ) %>% mutate(
      Time = recode_factor(ProductivityWithDeptCollabs, ProductivityWithDeptCollabs_x="Before\nmove", ProductivityWithDeptCollabs_y="After\nmove"),
      Direction = recode_factor(UpwardMove, "0"="Move to less labor", "1"="Move to more labor")
    )
}

plot.matching.results <- function(m.data.summary, ylab) {
  ggplot(m.data.summary, aes(x=Time, y=mu, color=Direction, linetype=Direction)) +
    geom_point() +
    geom_errorbar(aes(ymin=mu-se, ymax=mu+se, group=Direction), width=0.1) +
    geom_line(aes(group=Direction)) +
    labs(x="", y=ylab) +
    theme(legend.position = c(0.35, 0.15), legend.background = element_rect(fill = NA), legend.key = element_blank()) +
    guides(color=guide_legend(reverse=TRUE, title=NULL), linetype=guide_legend(reverse=TRUE, title=NULL)) +
    labs(color  = "Direction", linetype = "Direction") +
    scale_color_manual(name="Direction", values = c(colors[2], "black")) +
    scale_linetype_manual(name="Direction", values = c("dashed", "solid"))
}

moves3_4 = read.csv("./moves.csv")
m.out.y3_4 =  moves3_4 %>% do.matching()

# Diagnostic plots
plot(m.out.y3_4, type = "jitter", interactive = FALSE)

balance.y3_4 <- make.love.plot(m.out.y3_4)
balance.dist.y3_4 <- bal.plot(m.out.y3_4, which="both") + labs(title="Distributional Balance", x="Overall score")
balance.fund.y3_4 <- bal.plot(m.out.y3_4, var.name="log(funded_per_faculty_x + 1)", which="both") + labs(title='', x="Funded labor ratio", y='')
balance.pi.y3_4 <- bal.plot(m.out.y3_4, var.name="uniform_percentile_x", which="both") + labs(title='', x="Prestige", y='')
balance.y3_4 / wrap_elements(full=(balance.dist.y3_4 / balance.fund.y3_4 / balance.pi.y3_4
                                   + plot_annotation(tag_levels=list(c('B', 'C', 'D')))
                                   )) + plot_layout(heights=c(1, 2)) +
  plot_annotation(tag_levels=list(c("A", " ")))

ggsave("./matching_balance_y3_4.pdf", height=12, width=8)

# Matching results
m.data.y3_4 <- match.data(m.out.y3_4)
matching.data.y3_4 <- summarize.gs(m.data.y3_4) 
matching.data.y3_4.gp <- summarize.gp(m.data.y3_4) 

# Group productivity panel for supplement
plot.matching.results(matching.data.y3_4.gp, "Group productivity")
ggsave("figures/panels/matching.gp.pdf", width=4, height=4)

plot.matching.y3_4 <- plot.matching.results(matching.data.y3_4, "Group size")

#########
# Making combined figures
#########

extract.coefs <-function(mod) {
  tidy(coeftest(mod, vcov. = vcovCL, cluster=~Area)) %>%
    filter(substr(term, 1, 4) != 'Area') %>%
    filter(term != "(Intercept)") %>%
    mutate(term=recode_factor(term,
                              CONTROL="Private inst.",
                              scale_tt_headcount="Log dept. size",
                              scale_log_unfunded_per_faculty_p1="Unfunded labor\navailability",
                              scale_uniform_percentile100="Prestige",
                              scale_log_funded_per_faculty_p1="Funded labor\navailability"),
           signif=p.value < 0.05)
}

make.coefs.plot <- function(coefs) {
  coefs %>%
  mutate(dv=recode_factor(dv, "Total\nproductivity" = "Total productivity", "Group\nproductivity" = "Group productivity", "Group size" = "Group size")) %>%
  ggplot() +
    geom_vline(xintercept=0, linetype="dotted") +
    geom_errorbarh(aes(y=term, xmin=estimate - 1.96*std.error, xmax=estimate + 1.96*std.error, color=signif, size=signif, group=collabs), height=0) +
    geom_point(aes(y=term, x=estimate, size=signif, color=signif, shape=signif, fill=signif, group=collabs), size=3) +
    facet_grid(collabs ~ dv) +
    scale_color_manual(name="Signif", values = c("black", colors[4])) +
    scale_shape_manual(name="Signif", values = c(21, 16)) +
    scale_size_manual(name="Signif", values = c(1, 1.5)) +
    scale_fill_manual(name="Signif", values = c("white", colors[4])) +
    guides( color="none", size="none", shape="none", fill="none" ) +
    theme_bw() +
    theme(plot.margin=ggplot2::margin(6, 25, 6, 0), panel.spacing.x = unit(6, "mm"), panel.spacing.y=unit(3, "mm")) +
    labs(x="Standardized estimate", y=" ") 
}

coefs.collabs.overall <- extract.coefs(mod.area.collabs.pois.collabnorm.overall) %>% mutate(collabs="With collab norms", dv="Total\nproductivity")
coefs.nocollabs.overall <- extract.coefs(mod.area.collabs.pois.nocollabnorm.overall) %>% mutate(collabs="Without collab norms", dv="Total\nproductivity")
coefs.collabs <- extract.coefs(mod.area.collabs.pois.collabnorm) %>% mutate(collabs="With collab norms", dv="Group\nproductivity")
coefs.nocollabs <- extract.coefs(mod.area.collabs.pois.nocollabnorm) %>% mutate(collabs="Without collab norms", dv="Group\nproductivity")
coefs.collabs.gs <- extract.coefs(mod.area.collabs.pois.collabnorm.gs) %>% mutate(collabs="With collab norms", dv="Group size")
coefs.nocollabs.gs <- extract.coefs(mod.area.collabs.pois.nocollabnorm.gs) %>% mutate(collabs="Without collab norms", dv="Group size")
all.coefs <- rbind(coefs.collabs.overall, coefs.nocollabs.overall, coefs.collabs, coefs.nocollabs, coefs.collabs.gs, coefs.nocollabs.gs)

plot.coefs <- make.coefs.plot(all.coefs)
plot.coefs
ggsave("./coefs.pdf", width=7, height=5, dpi=300)

# Panel for group size vs. cumulative prod by prestige
prod_vs_gs <- read.csv("./gs_vs_cumprod.csv") %>%
  mutate(N = (std/sem)**2)

plot.prod_vs_gs <- 
  prod_vs_gs %>%
  mutate(prestige_top_half = as.factor(prestige_top_half)) %>%
  ggplot() +
    geom_line(aes(x=CumulativeGroupSize, y=mean, color=prestige_top_half, linetype=prestige_top_half)) +
    geom_ribbon(aes(x=CumulativeGroupSize, ymin=mean - 1.96 * sem, ymax = mean + 1.96 * sem, fill=prestige_top_half), alpha=0.3) +
  labs(x="Cumulative group size", y="Cumulative group prod.") +
  scale_fill_manual(name="Prestige", labels = c("Low prestige", "High prestige"), values = c("black", colors[2])) +
  scale_color_manual(name="Prestige", labels = c("Low prestige", "High prestige"), values = c("black", colors[2])) +
  scale_linetype_manual(name="Prestige", labels = c("Low prestige", "High prestige"), values = c("solid", "dashed")) +
  theme(legend.justification=c(0, 0), legend.position=c(0.1, 0.6), legend.background = element_blank(), legend.key = element_blank()) +
  guides(fill = guide_legend(title = NULL), color=guide_legend(title=NULL), linetype=guide_legend(title=NULL))


wrap_elements(full=plot.coefs) /
  wrap_elements(full=(plot.matching.y3_4 + plot.prod_vs_gs + plot_annotation(tag_levels=list(c('B', 'C'))))) +
  plot_layout(heights=c(4, 3)) +
  plot_annotation(tag_levels=list(c("A", "")))

ggsave("fig2_v9.2.pdf", width=7, height=7)

################################
# Descriptive statistics
#  (Figure 1)
################################

fac_nonfac_decile <- read.csv("./prod_by_decile.csv")
people_decile_decomp <- read.csv("./decomp_by_decile.csv")

plot_facnonfac <-
  ggplot(fac_nonfac_decile) +
  geom_point(aes(x=prestige_segment, color=job, fill=job, y=avg_prod, shape=job), size=3) +
  geom_line(aes(x=prestige_segment, color=job, fill=job, y=avg_prod)) +
  geom_ribbon(aes(x=prestige_segment, color=job, fill=job, ymin=avg_prod - 2*avg_prod_se, ymax=avg_prod + 2*avg_prod_se), alpha=0.2, size=0) +
  labs(x="Prestige decile", y="Average annual productivity\n(publications/year)") +
  scale_fill_manual(labels = c("Faculty", "Non-faculty\ngroup member"), values=c(colors[4], "black")) +
  scale_color_manual(labels = c("Faculty", "Non-faculty\ngroup member"), values=c(colors[4], "black")) +
  scale_shape_manual(labels = c("Faculty", "Non-faculty\ngroup member"), values=c(15, 16)) +
  guides(
    color=guide_legend(title=NULL, ncol=2),
    fill = guide_legend(title = NULL, ncol=2),
    shape = guide_legend(title = NULL, ncol=2)
  ) +
  theme(legend.position=c(0.5, 0.92), legend.background = element_blank(), legend.key = element_blank()) +
  scale_x_continuous(limits=c(1, 10), expand=c(0, 0.2), breaks=(1:10)) +
  scale_y_continuous(limits=c(0, 2.6), expand=c(0, 0), breaks=c(0, 0.5, 1, 1.5, 2, 2.5)) +
  geom_text(data=data.frame(x=8, y=0.15, text=paste("More prestigious", '\u2192')), aes(x=x,y=y,label=text),alpha=0.5)

bracket_wo_min <- min((people_decile_decomp %>%  filter(pi_decile == 10 & name=="ProductivityWithoutDeptCollabs"))$avg_prod)
bracket_wo_max <- max((people_decile_decomp %>%  filter(pi_decile == 10 & name=="ProductivityWithoutDeptCollabs"))$avg_prod)
bracket_w_min <- min((people_decile_decomp %>%  filter(pi_decile == 10 & name=="ProductivityWithDeptCollabs"))$avg_prod)
bracket_w_max <- max((people_decile_decomp %>%  filter(pi_decile == 10 & name=="ProductivityWithDeptCollabs"))$avg_prod)

plot_decomp <- 
  ggplot(people_decile_decomp) +
  geom_point(aes(x=pi_decile, color=AreaHasCollabNorm, fill=AreaHasCollabNorm, shape=AreaHasCollabNorm, y=avg_prod), size=3) +
  geom_line(aes(x=pi_decile, linetype=name, color=AreaHasCollabNorm, fill=AreaHasCollabNorm, y=avg_prod)) +
  geom_ribbon(aes(x=pi_decile, linetype=name, color=AreaHasCollabNorm, fill=AreaHasCollabNorm, ymin=avg_prod - 2*avg_prod_se, ymax=avg_prod + 2*avg_prod_se), alpha=0.2, size=0) +
  scale_fill_manual(labels = c("Disciplines without\ncollab norms", "Disciplines with\ncollab norms"), values=c(colors[1], colors[2])) +
  scale_color_manual(labels = c("Disciplines without\ncollab norms", "Disciplines with\ncollab norms"), values=c(colors[1], colors[2])) +
  scale_shape_manual(labels = c("Disciplines without\ncollab norms", "Disciplines with\ncollab norms"), values=c(4, 17)) +
  guides(
    color=guide_legend(title=NULL, ncol=2, reverse=TRUE),
    fill=guide_legend(title = NULL, ncol=2, reverse=TRUE),
    shape=guide_legend(title = NULL, ncol=2, reverse=TRUE),
    linetype="none") +
  theme(legend.justification=c(0, 0), legend.position=c(0.1, 0.85), legend.background = element_blank(), legend.key = element_blank()) +
  labs(x="Prestige decile") +
  labs(y="Average annual faculty productivity\n(publications/year)") +
  coord_cartesian(xlim=c(1, 10), clip="off") +
  scale_x_continuous(expand=c(0, 0), breaks=(1:10)) +
  scale_y_continuous(limits=c(0, 1.82), expand=c(0, 0), breaks=c(0, 0.5, 1, 1.5)) +
  theme(plot.margin=ggplot2::margin(6, 100, 6, 6)) +
  geom_path(data=data.frame(
    x=c(10.4, 12.3, 12.3, 10.4),
    y=c(bracket_wo_min, bracket_wo_min, bracket_wo_max, bracket_wo_max)
  ), aes(x=x, y=y), linetype="dotted") +
  geom_path(data=data.frame(
    x=c(10.4, 12.7, 12.7, 10.4),
    y=c(bracket_w_min, bracket_w_min, bracket_w_max, bracket_w_max)
  ), aes(x=x, y=y)) +
  geom_text(data=data.frame(
    x=c(10.45, 10.45),
    y=c(bracket_wo_max + 0.1, bracket_w_max + 0.1),
    labels=c("Individual\nproductivity", "Group\nproductivity")
  ), aes(x=x, y=y, label=labels), hjust="left", lineheight=0.85, size=3)

funding_by_segment <- read.csv("./funding_by_segment_clean.csv") 

overall_averages <- funding_by_segment %>%
  group_by(AreaHasCollabNorm, prestige_segment_equispaced) %>%
  dplyr::summarize(funded_tt_ratio = sum(ft_funded) / sum(tt_headcount)) %>%
  mutate(average.label = "Average")

plot.collab.labor <- 
  funding_by_segment %>% 
  filter(AreaHasCollabNorm == TRUE) %>%
  ggplot(aes(x=prestige_segment_equispaced, y=funded_tt_ratio)) +
  geom_line(aes(linetype=Area), color=colors[2], size=0.8) +
  guides(linetype = "none")  +
  scale_x_continuous(limits=c(1, 10), expand=c(0, 0), breaks=(1:10)) +
  geom_dl(aes(label=Area), method=list('last.bumpup', dl.trans(x=x + 0.1)), color=colors[2]) +
  geom_text(data=data.frame(x=2, y=6, text="Disciplines with collab norms"), aes(x=x,y=y,label=text),alpha=0.5, hjust="left") +
  labs(x="Prestige decile", y="Funded graduate researchers\nand postdocs per faculty")+
  layer(
    data=overall_averages %>% filter(AreaHasCollabNorm == TRUE),
    mapping=aes(x=prestige_segment_equispaced, y=funded_tt_ratio),
    geom="line", stat="identity", position="identity",
    params=list(size=2, color="black")
  )  +
  ylim(0, 6.5) +
  theme(plot.margin=ggplot2::margin(6, 85, 6, 30)) +
  coord_cartesian(xlim=c(1, 10), clip="off") 

plot.nocollab.labor <- 
  funding_by_segment %>% 
  filter(AreaHasCollabNorm == FALSE) %>%
  ggplot(aes(x=prestige_segment_equispaced, y=funded_tt_ratio)) +
  geom_line(aes(linetype=Area), color=colors[1], size=0.8) +
  guides(linetype = "none")  +
  scale_x_continuous(limits=c(1, 10), expand=c(0, 0), breaks=(1:10)) +
  geom_dl(aes(label=Area), method=list('last.bumpup', dl.trans(x=x + 0.1)), color=colors[1]) +
  geom_text(data=data.frame(x=2, y=6, text="Disciplines without collab norms"), aes(x=x,y=y,label=text),alpha=0.5, hjust="left") +
  labs(x="Prestige decile", y="Funded graduate researchers\nand postdocs per faculty") +
  ylim(0, 6.5) +
  layer(
    data=overall_averages %>% filter(AreaHasCollabNorm == FALSE),
    mapping=aes(x=prestige_segment_equispaced, y=funded_tt_ratio),
    geom="line", stat="identity", position="identity",
    params=list(size=2, color="black")
  ) +
  theme(plot.margin=ggplot2::margin(6, 60, 6, 0)) +
  coord_cartesian(xlim=c(1, 10), clip="off")

overall_averages <- funding_by_segment %>%
  group_by(AreaHasCollabNorm, prestige_segment_equispaced) %>%
  dplyr::summarize(funded_tt_ratio = sum(ft_funded) / sum(tt_headcount)) %>%
  mutate(average.label = "Average")

plot.collab.labor <- 
  funding_by_segment %>% 
  filter(AreaHasCollabNorm == TRUE) %>%
  ggplot(aes(x=prestige_segment_equispaced, y=funded_tt_ratio)) +
  geom_line(aes(linetype=Area), color=colors[2], size=0.8) +
  guides(linetype = "none")  +
  scale_x_continuous(limits=c(1, 10), expand=c(0, 0), breaks=(1:10)) +
  geom_dl(aes(label=Area), method=list('last.bumpup', dl.trans(x=x + 0.1)), color=colors[2]) +
  geom_text(data=data.frame(x=2, y=6, text="Disciplines with collab norms"), aes(x=x,y=y,label=text),alpha=0.5, hjust="left") +
  labs(x="Prestige decile", y="Funded graduate researchers\nand postdocs per faculty")+
  layer(
    data=overall_averages %>% filter(AreaHasCollabNorm == TRUE),
    mapping=aes(x=prestige_segment_equispaced, y=funded_tt_ratio),
    geom="line", stat="identity", position="identity",
    params=list(size=2, color="black")
  )  +
  ylim(0, 6.5) +
  theme(plot.margin=ggplot2::margin(6, 85, 6, 30)) +
  coord_cartesian(xlim=c(1, 10), clip="off") 

plot.nocollab.labor <- 
  funding_by_segment %>% 
  filter(AreaHasCollabNorm == FALSE) %>%
  ggplot(aes(x=prestige_segment_equispaced, y=funded_tt_ratio)) +
  geom_line(aes(linetype=Area), color=colors[1], size=0.8) +
  guides(linetype = "none")  +
  scale_x_continuous(limits=c(1, 10), expand=c(0, 0), breaks=(1:10)) +
  geom_dl(aes(label=Area), method=list('last.bumpup', dl.trans(x=x + 0.1)), color=colors[1]) +
  geom_text(data=data.frame(x=2, y=6, text="Disciplines without collab norms"), aes(x=x,y=y,label=text),alpha=0.5, hjust="left") +
  labs(x="Prestige decile", y="Funded graduate researchers\nand postdocs per faculty") +
  ylim(0, 6.5) +
  layer(
    data=overall_averages %>% filter(AreaHasCollabNorm == FALSE),
    mapping=aes(x=prestige_segment_equispaced, y=funded_tt_ratio),
    geom="line", stat="identity", position="identity",
    params=list(size=2, color="black")
  ) +
  theme(plot.margin=ggplot2::margin(6, 60, 6, 0)) +
  coord_cartesian(xlim=c(1, 10), clip="off")

# Mac OSX specific workaround to save unicode arrow in "More prestigious"
quartz(type = 'pdf', file = './labor_advantage_with_decomp.pdf', width=10, height=7, dpi=300)
((plot_facnonfac | plot_decomp) /
  (plot.collab.labor | plot.nocollab.labor)) +
  plot_annotation(tag_levels = 'A')
dev.off()
