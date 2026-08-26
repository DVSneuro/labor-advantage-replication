#########
# Extension 6: Underperformers and overperformers
#
# This script builds two complementary scorecards:
#   1. A named institution-level scorecard using NSF GSS graduate labor data
#      plus NIH F31/F32/T32 award data.
#   2. An anonymized department-level productivity residual scorecard using the
#      Zhang et al. department data, which do not expose institution names.
#
# The named institution scorecard is a training-output proxy, not a publication
# productivity residual. That distinction matters: the local Zhang data can model
# productivity, but it cannot identify Temple or any other institution by name.
#########

suppressPackageStartupMessages({
  library(dplyr)
  library(ggplot2)
  library(haven)
  library(MASS)
  library(readr)
  library(stringr)
  library(tidyr)
})

DATA_DIR <- "data"
ZHANG_DIR <- "code-and-data"
OUT_DIR <- file.path("outputs", "under_overperformers")
FIG_DIR <- "figures"
dir.create(OUT_DIR, recursive = TRUE, showWarnings = FALSE)
dir.create(FIG_DIR, recursive = TRUE, showWarnings = FALSE)

GSS_YEAR <- 2024
RECENT_YEARS <- 2020:2024
TEMPLE_KEY <- "TEMPLE UNIVERSITY"

safe_div <- function(num, den) {
  ifelse(is.na(den) | den <= 0, NA_real_, num / den)
}

zscore <- function(x) {
  s <- sd(x, na.rm = TRUE)
  if (is.na(s) || s == 0) {
    return(rep(0, length(x)))
  }
  (x - mean(x, na.rm = TRUE)) / s
}

canonical_org <- function(x) {
  x <- toupper(x)
  x <- str_replace_all(x, "&", " AND ")
  x <- str_replace_all(x, "\\bUNIV\\.?\\b", "UNIVERSITY")
  x <- str_replace_all(x, "\\bCOLL\\b", "COLLEGE")
  x <- str_replace_all(x, "D/B/A|D B A", " ")
  x <- str_replace_all(x, "[^A-Z0-9 ]", " ")
  x <- str_squish(x)

  x <- case_when(
    str_detect(x, "TEMPLE") ~ "TEMPLE UNIVERSITY",
    str_detect(x, "HARVARD") ~ "HARVARD UNIVERSITY",
    str_detect(x, "COLUMBIA") & !str_detect(x, "TEACHERS") ~ "COLUMBIA UNIVERSITY",
    str_detect(x, "WEILL") & str_detect(x, "CORNELL") ~ "CORNELL UNIVERSITY",
    str_detect(x, "CORNELL UNIVERSITY") ~ "CORNELL UNIVERSITY",
    str_detect(x, "UNIVERSITY OF MICHIGAN") ~ "UNIVERSITY OF MICHIGAN",
    str_detect(x, "UNIVERSITY OF NORTH CAROLINA") & str_detect(x, "CHAPEL") ~
      "UNIVERSITY OF NORTH CAROLINA CHAPEL HILL",
    str_detect(x, "UNIVERSITY OF PITTSBURGH") ~ "UNIVERSITY OF PITTSBURGH",
    str_detect(x, "NORTHWESTERN UNIVERSITY") & !str_detect(x, "STATE") ~
      "NORTHWESTERN UNIVERSITY",
    str_detect(x, "WASHINGTON UNIVERSITY") ~ "WASHINGTON UNIVERSITY IN ST LOUIS",
    str_detect(x, "UNIVERSITY OF UTAH") ~ "UNIVERSITY OF UTAH",
    str_detect(x, "OHIO STATE") ~ "OHIO STATE UNIVERSITY",
    str_detect(x, "BOSTON UNIVERSITY") ~ "BOSTON UNIVERSITY",
    str_detect(x, "RUTGERS") ~ "RUTGERS THE STATE UNIVERSITY OF NEW JERSEY",
    str_detect(x, "UNIVERSITY OF MIAMI") ~ "UNIVERSITY OF MIAMI",
    str_detect(x, "NEW YORK UNIVERSITY") ~ "NEW YORK UNIVERSITY",
    str_detect(x, "UNIVERSITY OF COLORADO") ~ "UNIVERSITY OF COLORADO",
    str_detect(x, "UNIVERSITY OF CALIFORNIA") ~ str_replace_all(x, "\\bAT\\b", ""),
    str_detect(x, "COLORADO STATE") ~ "COLORADO STATE UNIVERSITY",
    str_detect(x, "ARIZONA STATE") ~ "ARIZONA STATE UNIVERSITY",
    str_detect(x, "VIRGINIA POLYTECHNIC|VIRGINIA TECH") ~
      "VIRGINIA POLYTECHNIC INSTITUTE AND STATE UNIVERSITY",
    TRUE ~ x
  )

  x %>%
    str_replace_all("\\bTHE\\b", "") %>%
    str_replace_all("\\bAT\\b", "") %>%
    str_replace_all(
      "\\bCAMPUS\\b|SCHOOL OF MEDICINE|MEDICAL SCHOOL|SCHOOL OF PUBLIC HEALTH|HEALTH SCIENCES|MEDICAL CENTER|MED CTR",
      ""
    ) %>%
    str_squish()
}

extract_gss_sas <- function(year = GSS_YEAR) {
  nsf_zip <- file.path(DATA_DIR, "NSFdata.zip")
  if (!file.exists(nsf_zip)) {
    stop("Missing ", nsf_zip, ". The GSS extraction is needed for the named institution scorecard.")
  }

  temp_dir <- tempfile("gss_extract_")
  dir.create(temp_dir)
  inner_zip_name <- sprintf("graduate_students_postdocs_%s.zip", year)
  utils::unzip(nsf_zip, files = inner_zip_name, exdir = temp_dir)
  inner_zip_path <- file.path(temp_dir, inner_zip_name)

  inner_listing <- utils::unzip(inner_zip_path, list = TRUE)
  sas_name <- inner_listing$Name[
    str_detect(tolower(inner_listing$Name), sprintf("gss%s_code\\.sas7bdat$", year))
  ][1]
  if (is.na(sas_name)) {
    stop("Could not find the GSS SAS file for ", year, " inside ", inner_zip_name)
  }

  utils::unzip(inner_zip_path, files = sas_name, exdir = temp_dir)
  file.path(temp_dir, sas_name)
}

load_gss_institutions <- function() {
  message("Loading NSF GSS ", GSS_YEAR, " from data/NSFdata.zip...")
  sas_path <- extract_gss_sas(GSS_YEAR)
  needed_cols <- c(
    "institution_id", "UNITID", "year", "Institution_Name", "institution_state",
    "carnegie_code_2021", "dr_ft_tot_all_races_v", "dr_ft_ra_all_v",
    "dr_ft_fel_all_v", "dr_ft_trn_all_v", "dr_ft_ta_all_v", "dr_ft_ots_all_v",
    "dr_ft_tot_fed_all_v", "dr_ft_tot_nfed_inst_v", "pd_tot_all_v",
    "pd_tot_fed_all_v"
  )

  read_sas(sas_path, col_select = all_of(needed_cols)) %>%
    mutate(org_key = canonical_org(Institution_Name)) %>%
    group_by(org_key) %>%
    summarise(
      display_name = first(Institution_Name),
      institution_state = first(institution_state),
      carnegie_code_2021 = first(carnegie_code_2021),
      across(
        c(
          dr_ft_tot_all_races_v, dr_ft_ra_all_v, dr_ft_fel_all_v,
          dr_ft_trn_all_v, dr_ft_ta_all_v, dr_ft_ots_all_v,
          dr_ft_tot_fed_all_v, dr_ft_tot_nfed_inst_v, pd_tot_all_v,
          pd_tot_fed_all_v
        ),
        ~ sum(.x, na.rm = TRUE)
      ),
      .groups = "drop"
    ) %>%
    mutate(
      total_dr_ft = dr_ft_tot_all_races_v,
      ra_share = safe_div(dr_ft_ra_all_v, total_dr_ft),
      fellow_trainee_share = safe_div(dr_ft_fel_all_v + dr_ft_trn_all_v, total_dr_ft),
      ta_other_share = safe_div(dr_ft_ta_all_v + dr_ft_ots_all_v, total_dr_ft),
      federal_support_share = safe_div(dr_ft_tot_fed_all_v, total_dr_ft),
      institutional_support_share = safe_div(dr_ft_tot_nfed_inst_v, total_dr_ft),
      postdocs_per_100_doctoral = safe_div(100 * pd_tot_all_v, total_dr_ft),
      car_group = case_when(
        carnegie_code_2021 == 15 ~ "temple_carnegie_code",
        carnegie_code_2021 %in% c(16, 17, 18, 19, 20, 21) ~ "other_doctoral",
        TRUE ~ "other"
      )
    )
}

load_nih_training <- function() {
  message("Loading NIH F31/F32/T32 awards for ", min(RECENT_YEARS), "-", max(RECENT_YEARS), "...")
  files <- tibble(
    activity_code = c("F31", "F32", "T32"),
    path = file.path(DATA_DIR, c(
      "F31_awards_2008_2024.csv",
      "F32_awards_2008_2024.csv",
      "T32_awards_2008_2024.csv"
    ))
  )
  missing_files <- files$path[!file.exists(files$path)]
  if (length(missing_files) > 0) {
    stop("Missing NIH award files: ", paste(missing_files, collapse = ", "))
  }

  bind_rows(lapply(seq_len(nrow(files)), function(i) {
    read_csv(files$path[i], show_col_types = FALSE) %>%
      mutate(activity_code = files$activity_code[i])
  })) %>%
    filter(fiscal_year %in% RECENT_YEARS) %>%
    mutate(
      org_key = canonical_org(org_name),
      project_core = str_extract(project_num, paste0(activity_code, "[A-Z]{2}[0-9]+")),
      project_core = if_else(is.na(project_core), project_num, project_core)
    )
}

build_institution_scorecard <- function(gss_inst, nih) {
  nih_inst <- nih %>%
    group_by(org_key) %>%
    summarise(
      f_award_years = sum(activity_code %in% c("F31", "F32")),
      f31_award_years = sum(activity_code == "F31"),
      f32_award_years = sum(activity_code == "F32"),
      t32_award_years = sum(activity_code == "T32"),
      f_unique_projects = n_distinct(project_core[activity_code %in% c("F31", "F32")]),
      t32_unique_projects = n_distinct(project_core[activity_code == "T32"]),
      f_total_cost = sum(award_amount[activity_code %in% c("F31", "F32")], na.rm = TRUE),
      t32_total_cost = sum(award_amount[activity_code == "T32"], na.rm = TRUE),
      .groups = "drop"
    )

  scores <- gss_inst %>%
    left_join(nih_inst, by = "org_key") %>%
    mutate(
      across(
        c(
          f_award_years, f31_award_years, f32_award_years, t32_award_years,
          f_unique_projects, t32_unique_projects, f_total_cost, t32_total_cost
        ),
        ~ coalesce(.x, 0)
      ),
      f_awards_per_100_doctoral = safe_div(100 * f_award_years, total_dr_ft),
      t32_awards_per_100_doctoral = safe_div(100 * t32_award_years, total_dr_ft)
    )

  model_df <- scores %>%
    filter(total_dr_ft >= 50)

  fit <- glm.nb(
    f_award_years ~
      log1p(total_dr_ft) +
      log1p(dr_ft_ra_all_v) +
      log1p(dr_ft_fel_all_v + dr_ft_trn_all_v) +
      log1p(t32_award_years) +
      postdocs_per_100_doctoral +
      car_group,
    data = model_df
  )

  model_df <- model_df %>%
    mutate(
      expected_f_award_years = predict(fit, type = "response"),
      f_training_residual = residuals(fit, type = "pearson"),
      f_training_ratio = safe_div(f_award_years + 0.5, expected_f_award_years + 0.5),
      f_training_residual_rank_over = rank(-f_training_residual, ties.method = "min"),
      f_training_residual_percentile = 100 * percent_rank(f_training_residual)
    )

  scores <- scores %>%
    left_join(
      model_df %>%
        dplyr::select(
          org_key, expected_f_award_years, f_training_residual, f_training_ratio,
          f_training_residual_rank_over, f_training_residual_percentile
        ),
      by = "org_key"
    )

  temple <- scores %>% filter(org_key == TEMPLE_KEY)
  if (nrow(temple) != 1) {
    stop("Could not identify a single Temple row in the GSS scorecard.")
  }

  peer_scores <- scores %>%
    filter(
      carnegie_code_2021 == temple$carnegie_code_2021[1],
      total_dr_ft >= 100
    ) %>%
    mutate(
      ra_share_peer_z = zscore(ra_share),
      ta_other_share_peer_z = zscore(ta_other_share),
      ra_share_percentile = 100 * percent_rank(ra_share),
      ta_other_share_percentile = 100 * percent_rank(ta_other_share),
      obligation_risk_z = ta_other_share_peer_z - ra_share_peer_z,
      obligation_risk_rank_over = rank(-obligation_risk_z, ties.method = "min"),
      obligation_risk_percentile = 100 * percent_rank(obligation_risk_z)
    )

  scores <- scores %>%
    left_join(
      peer_scores %>%
        dplyr::select(
          org_key, ra_share_peer_z, ta_other_share_peer_z, ra_share_percentile,
          ta_other_share_percentile, obligation_risk_z, obligation_risk_rank_over,
          obligation_risk_percentile
        ),
      by = "org_key"
    )

  list(scores = scores, model = fit, peer_scores = peer_scores)
}

build_zhang_residuals <- function() {
  message("Building anonymized Zhang department productivity residuals...")
  area_path <- file.path(ZHANG_DIR, "area-strict.csv")
  if (!file.exists(area_path)) {
    stop("Missing ", area_path)
  }

  area <- read_csv(area_path, show_col_types = FALSE) %>%
    mutate(
      anonymous_department_id = sprintf("dept_%03d", row_number()),
      log_productivity = log1p(Productivity)
    )

  fit <- lm(
    log_productivity ~
      scale_log_funded_per_faculty_p1 +
      scale_log_unfunded_per_faculty_p1 +
      scale_tt_headcount +
      scale_uniform_percentile100 +
      CONTROL +
      Area,
    data = area
  )

  area %>%
    mutate(
      expected_productivity = exp(predict(fit, newdata = area)) - 1,
      productivity_residual = log_productivity - predict(fit, newdata = area),
      productivity_residual_z = as.numeric(scale(productivity_residual)),
      productivity_ratio = safe_div(Productivity + 0.05, expected_productivity + 0.05),
      productivity_direction = case_when(
        productivity_residual_z >= 1.5 ~ "anonymous_overperformer",
        productivity_residual_z <= -1.5 ~ "anonymous_underperformer",
        TRUE ~ "near_expected"
      )
    ) %>%
    dplyr::select(
      anonymous_department_id, Area, Productivity, expected_productivity,
      productivity_residual, productivity_residual_z, productivity_ratio,
      funded_per_faculty, unfunded_per_faculty, tt_headcount, uniform_percentile100,
      CONTROL, AreaHasCollabNorm, productivity_direction
    )
}

plot_labor_mix <- function(scores, peer_scores) {
  temple <- scores %>% filter(org_key == TEMPLE_KEY)
  peer_summary <- peer_scores %>%
    summarise(
      ra_share = median(ra_share, na.rm = TRUE),
      fellow_trainee_share = median(fellow_trainee_share, na.rm = TRUE),
      ta_other_share = median(ta_other_share, na.rm = TRUE)
    )

  plot_df <- bind_rows(
    temple %>%
      transmute(group = "Temple", ra_share, fellow_trainee_share, ta_other_share),
    peer_summary %>%
      mutate(group = "Peer median")
  ) %>%
    pivot_longer(
      cols = c(ra_share, fellow_trainee_share, ta_other_share),
      names_to = "mechanism",
      values_to = "share"
    ) %>%
    mutate(
      mechanism = recode(
        mechanism,
        ra_share = "Research assistantship",
        fellow_trainee_share = "Fellowship/traineeship",
        ta_other_share = "TA/other"
      ),
      mechanism = factor(
        mechanism,
        levels = c("Research assistantship", "Fellowship/traineeship", "TA/other")
      )
    )

  ggplot(plot_df, aes(mechanism, share, fill = group)) +
    geom_col(position = position_dodge(width = 0.72), width = 0.62) +
    scale_y_continuous(labels = function(x) paste0(round(100 * x), "%")) +
    scale_fill_manual(values = c("Temple" = "#d95f02", "Peer median" = "#1b9e77")) +
    labs(
      x = NULL,
      y = "Share of full-time doctoral students",
      fill = NULL,
      title = "Temple's Doctoral Funding Mix vs. Same-Carnegie Peers",
      subtitle = "NSF GSS 2024; peers have Temple's Carnegie code and >=100 full-time doctoral students"
    ) +
    theme_classic(base_size = 11) +
    theme(legend.position = "top")

  ggsave(
    file.path(FIG_DIR, "under_over_temple_labor_mix.png"),
    width = 8.5,
    height = 5,
    dpi = 150
  )
}

plot_training_residuals <- function(scores) {
  model_scores <- scores %>%
    filter(!is.na(f_training_residual))

  temple <- model_scores %>% filter(org_key == TEMPLE_KEY)
  plot_df <- bind_rows(
    model_scores %>% arrange(desc(f_training_residual)) %>% slice_head(n = 12),
    model_scores %>% arrange(f_training_residual) %>% slice_head(n = 12),
    temple
  ) %>%
    distinct(org_key, .keep_all = TRUE) %>%
    mutate(
      label = if_else(org_key == TEMPLE_KEY, paste0(display_name, " *"), display_name),
      direction = if_else(f_training_residual >= 0, "Over expected", "Under expected")
    )

  ggplot(plot_df, aes(x = reorder(label, f_training_residual), y = f_training_residual)) +
    geom_col(aes(fill = direction), width = 0.72) +
    geom_hline(yintercept = 0, linewidth = 0.3) +
    coord_flip() +
    scale_fill_manual(values = c("Over expected" = "#1b9e77", "Under expected" = "#d95f02")) +
    labs(
      x = NULL,
      y = "Pearson residual from negative-binomial model",
      fill = NULL,
      title = "Named Institution F31/F32 Over- and Underperformers",
      subtitle = "Observed 2020-2024 NIH F31/F32 award-years minus model expectation"
    ) +
    theme_classic(base_size = 10) +
    theme(legend.position = "top")

  ggsave(
    file.path(FIG_DIR, "under_over_fellowship_residuals.png"),
    width = 9,
    height = 7,
    dpi = 150
  )
}

plot_zhang_residuals <- function(zhang_residuals) {
  ggplot(
    zhang_residuals,
    aes(expected_productivity + 0.05, Productivity + 0.05)
  ) +
    geom_abline(slope = 1, intercept = 0, linewidth = 0.35, linetype = "dashed") +
    geom_point(aes(color = productivity_direction), alpha = 0.78, size = 2) +
    scale_x_log10() +
    scale_y_log10() +
    scale_color_manual(
      values = c(
        anonymous_overperformer = "#1b9e77",
        anonymous_underperformer = "#d95f02",
        near_expected = "#7570b3"
      )
    ) +
    labs(
      x = "Expected productivity + 0.05",
      y = "Observed productivity + 0.05",
      color = NULL,
      title = "Anonymous Department Productivity Residuals",
      subtitle = "Zhang data identify fields and covariates, but not institution names"
    ) +
    theme_classic(base_size = 11) +
    theme(legend.position = "top")

  ggsave(
    file.path(FIG_DIR, "under_over_zhang_anonymous_residuals.png"),
    width = 8,
    height = 6,
    dpi = 150
  )
}

write_markdown_summary <- function(scores, peer_scores, zhang_residuals, model) {
  temple <- scores %>% filter(org_key == TEMPLE_KEY)
  peers_n <- nrow(peer_scores)

  peer_medians <- peer_scores %>%
    summarise(
      ra_share = median(ra_share, na.rm = TRUE),
      fellow_trainee_share = median(fellow_trainee_share, na.rm = TRUE),
      ta_other_share = median(ta_other_share, na.rm = TRUE),
      institutional_support_share = median(institutional_support_share, na.rm = TRUE),
      postdocs_per_100_doctoral = median(postdocs_per_100_doctoral, na.rm = TRUE)
    )

  top_over <- scores %>%
    filter(!is.na(f_training_residual)) %>%
    arrange(desc(f_training_residual)) %>%
    slice_head(n = 10) %>%
    transmute(
      line = sprintf(
        "- %s: observed %.0f, expected %.1f, ratio %.2fx, residual %.2f",
        display_name, f_award_years, expected_f_award_years,
        f_training_ratio, f_training_residual
      )
    ) %>%
    pull(line)

  top_under <- scores %>%
    filter(!is.na(f_training_residual)) %>%
    arrange(f_training_residual) %>%
    slice_head(n = 10) %>%
    transmute(
      line = sprintf(
        "- %s: observed %.0f, expected %.1f, ratio %.2fx, residual %.2f",
        display_name, f_award_years, expected_f_award_years,
        f_training_ratio, f_training_residual
      )
    ) %>%
    pull(line)

  anonymous_counts <- zhang_residuals %>%
    count(productivity_direction) %>%
    mutate(line = sprintf("- %s: %s departments", productivity_direction, n)) %>%
    pull(line)

  lines <- c(
    "# Under/Overperformer Extension Summary",
    "",
    sprintf("Generated by `06_under_overperformers.R` using NSF GSS %s and NIH F31/F32/T32 %s-%s award files.", GSS_YEAR, min(RECENT_YEARS), max(RECENT_YEARS)),
    "",
    "## Interpretive Caveat",
    "",
    "The named institution scorecard below is an NIH individual-fellowship output proxy, not a named publication-productivity residual. The Zhang et al. department data can estimate productivity residuals, but those department rows are anonymized and cannot name Temple or any other institution without an external institution-publication link.",
    "",
    "## Temple",
    "",
    sprintf("- Full-time doctoral students in GSS SEH fields: %.0f", temple$total_dr_ft),
    sprintf("- Research assistantship share: %.1f%% (peer median %.1f%%; %.0fth percentile among %s same-Carnegie peers)", 100 * temple$ra_share, 100 * peer_medians$ra_share, temple$ra_share_percentile, peers_n),
    sprintf("- Fellowship/traineeship share: %.1f%% (peer median %.1f%%)", 100 * temple$fellow_trainee_share, 100 * peer_medians$fellow_trainee_share),
    sprintf("- TA/other share: %.1f%% (peer median %.1f%%; %.0fth percentile)", 100 * temple$ta_other_share, 100 * peer_medians$ta_other_share, temple$ta_other_share_percentile),
    sprintf("- Labor-obligation risk score: %.2f z units; %.0fth percentile; rank %s of %s by risk within same-Carnegie peers", temple$obligation_risk_z, temple$obligation_risk_percentile, temple$obligation_risk_rank_over, peers_n),
    sprintf("- NIH F31/F32 award-years, %s-%s: %.0f observed vs %.1f expected; %.2fx expected; residual %.2f; overperformance rank %s of %s modeled institutions", min(RECENT_YEARS), max(RECENT_YEARS), temple$f_award_years, temple$expected_f_award_years, temple$f_training_ratio, temple$f_training_residual, temple$f_training_residual_rank_over, sum(!is.na(scores$f_training_residual))),
    "",
    "Plain-language read: Temple has a somewhat less RA-centered funding mix than peers, so the user's mechanism is measurable. But the available local named data do not support Temple as a training-output underperformer; Temple is above expected on F31/F32 production.",
    "",
    "## Top F31/F32 Overperformers",
    "",
    top_over,
    "",
    "## Top F31/F32 Underperformers",
    "",
    top_under,
    "",
    "## Anonymous Zhang Productivity Residuals",
    "",
    anonymous_counts,
    "",
    "Files written:",
    "",
    "- `outputs/under_overperformers/institution_training_scorecard.csv`",
    "- `outputs/under_overperformers/temple_summary.csv`",
    "- `outputs/under_overperformers/zhang_department_residuals_anonymized.csv`",
    "- `figures/under_over_temple_labor_mix.png`",
    "- `figures/under_over_fellowship_residuals.png`",
    "- `figures/under_over_zhang_anonymous_residuals.png`"
  )

  writeLines(lines, file.path(OUT_DIR, "under_overperformer_summary.md"))

  model_table <- coef(summary(model)) %>%
    as.data.frame() %>%
    tibble::rownames_to_column("term")
  write_csv(model_table, file.path(OUT_DIR, "fellowship_model_coefficients.csv"))
}

main <- function() {
  gss_inst <- load_gss_institutions()
  nih <- load_nih_training()

  institution_results <- build_institution_scorecard(gss_inst, nih)
  scores <- institution_results$scores
  peer_scores <- institution_results$peer_scores

  zhang_residuals <- build_zhang_residuals()

  write_csv(scores, file.path(OUT_DIR, "institution_training_scorecard.csv"))
  write_csv(
    scores %>% filter(org_key == TEMPLE_KEY),
    file.path(OUT_DIR, "temple_summary.csv")
  )
  write_csv(
    zhang_residuals,
    file.path(OUT_DIR, "zhang_department_residuals_anonymized.csv")
  )

  plot_labor_mix(scores, peer_scores)
  plot_training_residuals(scores)
  plot_zhang_residuals(zhang_residuals)
  write_markdown_summary(scores, peer_scores, zhang_residuals, institution_results$model)

  temple <- scores %>% filter(org_key == TEMPLE_KEY)
  message("")
  message("Temple quick read:")
  message(sprintf(
    "  Direct RA share: %.1f%%; TA/other share: %.1f%%; obligation-risk percentile among peers: %.0f",
    100 * temple$ra_share, 100 * temple$ta_other_share, temple$obligation_risk_percentile
  ))
  message(sprintf(
    "  F31/F32 output: %.0f observed vs %.1f expected (%.2fx); residual %.2f; rank %s of %s overperformers",
    temple$f_award_years, temple$expected_f_award_years, temple$f_training_ratio,
    temple$f_training_residual, temple$f_training_residual_rank_over,
    sum(!is.na(scores$f_training_residual))
  ))
  message("")
  message("Wrote outputs to ", OUT_DIR, " and figures to ", FIG_DIR, ".")
}

main()
