-- Unified SQL View for presentation metrics and Airflow DAGs
CREATE OR REPLACE VIEW view_eat_trade_empowerment_matrix AS
SELECT
    country,
    country_code,
    dbm_category,
    dbm_score,
    female_decision_score,
    crop_diversity_index,
    net_staple_import_dependency_pct,
    nutritional_resilience_index,
    source_years,
    data_years_mismatched
FROM integrated_eat_trade_matrix;