-- Unified SQL View for presentation metrics and Airflow DAGs
CREATE OR REPLACE VIEW view_eat_trade_empowerment_matrix AS
SELECT 
    country,
    country_code,
    dbm_pct AS double_burden_malnutrition_pct,
    dbm_risk_tier,
    female_ag_decision_score,
    crop_diversity_index,
    dietary_diversity_score,
    net_staple_import_dependency_pct,
    food_price_volatility_index,
    nutritional_resilience_index
FROM integrated_eat_trade_matrix