# The Double Burden: Linking Female Agency, Trade Vulnerability & Household Malnutrition

A Women in Data Datathon submission combining two real-data pipelines: a country-level
Nutritional Resilience Index (NRI) and a household-level Double Burden of Malnutrition
(DBM) analysis, tested against each other where they overlap — plus a simplified,
larger-sample robustness check on the NRI side.

## Why this exists

Growing up, one of us (Zayy) repeatedly noticed a pattern without a name for it: an
overweight or obese mother alongside a visibly undernourished child. A friend studying
pediatrics later gave it a name — the **double burden of malnutrition (DBM)** — the
coexistence of undernutrition and overweight/obesity within the same household.

Separately, the other of us (Buhle) was asking an upstream question: what makes a
country's food system able to absorb a shock — a bad harvest, a price spike — rather
than just measuring current hunger? The **Nutritional Resilience Index (NRI)** is a
first-pass composite meant to proxy that structural capacity.

This project joins both questions: can a country's structural food-system
characteristics (NRI) predict where household-level double burden is most likely?
We built real, independently-sourced pipelines for both halves, tested them against
each other for the 4 countries where they overlap, and then built a second, simplified
version of the NRI to check whether the same pattern (or lack of one) holds at a
larger sample size.

## Data sources — all real, no synthetic/placeholder data

| Table                                       | Source                                                                                                               | Coverage                                                                                           |
| ------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `integrated_eat_trade_matrix` (NRI inputs)  | FAOSTAT (import dependency, crop production), World Bank/DHS indicator SG.DMK.ALLD.FN.ZS (household decision-making) | 7 countries                                                                                         |
| `dbm_by_country` (categorical DBM)          | Food Systems Dashboard, Popkin et al. 2020                                                                           | 7 countries, classification based on 2010 survey data                                              |
| `dbm_by_country_household` (continuous DBM) | Bawuah et al. (2026), *Maternal & Child Nutrition*, 22(1), e70175                                                    | 22 sub-Saharan African countries, 103,497 DHS mother-child pairs                                   |
| `sa_food_insecurity_by_province`            | Statistics South Africa, GHS Report 03-10-28 (2025)                                                                  | South Africa, 2019/2022/2023 (Northern Cape only has all 3 years with the female-headed breakdown) |
| `country_nutritional_resilience_simplified` | FAOSTAT bulk extract + manually-sourced FAOSTAT Suite of Food Security Indicators (2021-2023 avg.)                   | 14 countries (of 21 in the Bawuah et al. sample with complete decision + import dependency data)   |

The Bawuah et al. and Stats SA tables are transcribed from published, cited tables
rather than pulled from a live API — the underlying DHS/MICS microdata is
access-gated and required registration we didn't have time to complete before the
deadline. This is stated here rather than hidden.

## Pipeline structure
src/
extract.py # NRI pipeline: real FAOSTAT/World Bank ingestion, fails loudly if a source file is missing
Also includes load_import_dependency_extended() and
load_female_decision_score_extended() for the simplified NRI check
transform.py # NRI pipeline: computes Nutritional Resilience Index (7-country, 3-variable)
load.py # NRI pipeline: loads into Postgres, rebuilds view_eat_trade_empowerment_matrix
visualize.py # NRI pipeline: renders data/nri_vs_dbm_chart.png

extract_household.py # Household pipeline: reads Bawuah et al. + Stats SA CSVs
transform_household.py # Household pipeline: cleans DBM survey rounds, computes gender gap, joins real NRI x real DBM (4-country overlap)
Also includes calculate_nri_simplified() and
build_country_analysis_table_simplified() for the 14-country robustness check
load_household.py # Household pipeline: loads into Postgres, rebuilds view_household_dbm_analysis

apply_schema.py # Applies src/schema.sql directly (optional; load.py already creates the view inline)
schema.sql # View definition for view_eat_trade_empowerment_matrix

dags/
food_insecurity_dag.py # Airflow 3.x TaskFlow DAG for the NRI pipeline (extract -> transform -> load).
Verified to build and parse correctly under apache-airflow-core 3.x
(uses airflow.sdk, not the deprecated airflow.decorators path).
No live scheduler run has been performed — see Known limitations.

tests/
test_pipeline.py # 5 smoke tests against the household extract/transform layer.
Verified passing (5/5) as of the latest commit.

data/
raw/ # Versioned, real source CSVs for both pipelines
external/ # Raw downloads from FAOSTAT / World Bank / Food Systems Dashboard
processed/ # Final integrated_eat_trade_matrix.csv
nri_vs_dbm_chart.png # NRI vs. DBM category chart

docker-compose.yml # Containerized Postgres (included; pipeline has been validated
against a local Postgres.app instance, not yet run through Docker)


## Running the NRI pipeline
pip install -r requirements.txt
cp .env.example .env # edit if your Postgres isn't on localhost:5432
createdb food_datathon

python3 src/extract.py
python3 src/transform.py
python3 src/load.py
python3 src/visualize.py


Verify it landed:
SELECT * 
FROM view_eat_trade_empowerment_matrix 
ORDER BY nutritional_resilience_index DESC;


## Running the household-DBM pipeline
python3 src/extract_household.py
python3 src/transform_household.py
python3 src/load_household.py


Verify it landed:
SELECT * 
FROM view_household_dbm_analysis 
ORDER BY nutritional_resilience_index;


Running `transform_household.py` directly (`python3 src/transform_household.py`) also
prints the 14-country simplified NRI robustness check table to the console — this
table is not currently loaded into Postgres, it's a standalone check.

## Running the tests
pip install pytest
python3 -m pytest tests/test_pipeline.py -v


Expected: 5 passed. These are lightweight smoke tests against the household
extract/transform layer and don't require a live Postgres connection.

## Checking the Airflow DAG
pip install "apache-airflow-core>=3.0,<4.0"
python3 dags/food_insecurity_dag.py


Expected: no output, no errors. This confirms the DAG parses and builds correctly.
It does not run a live scheduled pipeline — see Known limitations.

## The Nutritional Resilience Index (NRI)

NRI = (0.4 x Female Household Decision-Making Score)

- (0.4 x Crop Diversity Evenness x 100)

- (0.2 x Net Staple Import Dependency %)

- **Female Household Decision-Making Score**: World Bank/DHS indicator SG.DMK.ALLD.FN.ZS — measures
participation in the three major household decisions (own health care, major purchases, family
visits). This is a general household decision-making measure, **not** agriculture-specific.

- **Crop Diversity Evenness**: Shannon evenness index (0-1) computed from real FAOSTAT crop
production data, livestock/processed items excluded.

- **Net Staple Import Dependency %**: FAOSTAT cereal import dependency ratio; negative values
indicate net exporters.

- Weights (0.4/0.4/0.2) are an **illustrative first-pass allocation**, not derived from regression
or externally validated.

### Simplified NRI robustness check (14-country extension)

The full 3-variable NRI only covers 7 countries because crop diversity data
(FAOSTAT) wasn't extended beyond the original bulk extract. To check whether the
NRI-DBM relationship holds on a larger sample, we built a **simplified 2-variable
version** — dropping crop diversity, keeping only female decision-making score and
staple import dependency — across all 21 countries in the Bawuah et al. DBM dataset.
