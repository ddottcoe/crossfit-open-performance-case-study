-- Example analytical queries for the case study

-- 1. Yearly Open performance summary
SELECT year, overall_rank
FROM athlete_year_open_poc
ORDER BY year;

-- 2. Best and worst event finishes relative to yearly rank
SELECT year, workout_code, performance_vs_year_rank_pct
FROM open_event_training_fit_summary
ORDER BY performance_vs_year_rank_pct DESC;

-- 3. Correlation summary by movement exposure
SELECT metric, corr_to_rel_perf, n
FROM open_event_training_fit_correlations
ORDER BY corr_to_rel_perf DESC;
