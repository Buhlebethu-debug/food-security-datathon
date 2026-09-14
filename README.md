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
# also includes load_import_dependency_extended() and
# load_female_decision_score_extended() for the simplified NRI check
transform.py # NRI pipeline: computes Nutritional Resilience Index (7-country, 3-variable)
load.py # NRI pipeline: loads into Postgres, rebuilds view_eat_trade_empowerment_matrix
visualize.py # NRI pipeline: renders data/nri_vs_dbm_chart.png

extract_household.py # Household pipeline: reads Bawuah et al. + Stats SA CSVs
transform_household.py # Household pipeline: cleans DBM survey rounds, computes gender gap, joins real NRI x real DBM (4-country overlap)
# also includes calculate_nri_simplified() and
# build_country_analysis_table_simplified() for the 14-country robustness check
load_household.py # Household pipeline: loads into Postgres, rebuilds view_household_dbm_analysis

apply_schema.py # Applies src/schema.sql directly (optional; load.py already creates the view inline)
schema.sql # View definition for view_eat_trade_empowerment_matrix

dags/
food_insecurity_dag.py # Airflow 3.x TaskFlow DAG for the NRI pipeline (extract -> transform -> load).
# Verified to build and parse correctly under apache-airflow-core 3.x
# (uses airflow.sdk, not the deprecated airflow.decorators path).
# No live scheduler run has been performed — see Known limitations.

tests/
test_pipeline.py # 5 smoke tests against the household extract/transform layer.
# Verified passing (5/5) as of the latest commit.

data/
raw/ # Versioned, real source CSVs for both pipelines
external/ # Raw downloads from FAOSTAT / World Bank / Food Systems Dashboard
processed/ # Final integrated_eat_trade_matrix.csv
nri_vs_dbm_chart.png # NRI vs. DBM category chart

docker-compose.yml # Containerized Postgres (included; pipeline has been validated
# against a local Postgres.app instance, not yet run through Docker)


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
python3 dags/food_insecurity_dag.pyz


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

NRI_simplified = (0.5 x Female Household Decision-Making Score)
- (0.5 x Net Staple Import Dependency %)


- Import dependency data for the 11 countries outside the original 7 was sourced
manually from FAOSTAT's Suite of Food Security Indicators (2021-2023 average) — not
pulled from the bulk extract, since that only covered the original 7 TARGET_COUNTRIES.
- 7 of the 21 DBM countries (Benin, Cote d'Ivoire, Gabon, Liberia, Madagascar, Sierra
Leone, Uganda) are still missing import dependency data and are **excluded, not
imputed**. This leaves 14 countries with complete data.
- **`nri_simplified` is on a different scale than the full 3-variable
`nutritional_resilience_index`** (roughly -30 to +30, vs. 0-100) — the two are not
directly comparable and should not be plotted on the same axis without rescaling.

## What we found

**7-country NRI landscape (categorical DBM, 2010 data):** No clear relationship between NRI and
DBM classification at this sample size and DBM resolution.

**4-country real overlap test (continuous DBM, Bawuah et al. 2026):** Burkina Faso, Ghana, Malawi,
and Tanzania are the only countries present in both the NRI dataset and the Bawuah et al. sample.
The observed relationship runs **opposite** to our hypothesis — higher NRI paired with higher DBM
prevalence, not lower. All four countries sit in a narrow, low-DBM band (3.2%-6.9%, below Bawuah
et al.'s 22-country mean of 6.7%). With n=4, this is not strong evidence against the hypothesis —
it demonstrates the pipeline can run a genuine test, and that a larger, wider-range country sample
is the clear next step.

**14-country simplified NRI robustness check:** Extending the (simplified, 2-variable) NRI to a
larger sample shows essentially no correlation with DBM prevalence (r ≈ -0.05). This doesn't
confirm or refute the hypothesis either — but combined with the 4-country full-NRI result above,
both independent tests point toward the same conclusion: a larger, higher-resolution dataset with
all three original NRI variables is needed before drawing conclusions about the NRI-DBM
relationship in either direction.

**Household mechanism (Bawuah et al., 22 countries):** the richest households have 57% lower odds
of child stunting than the poorest, but 391% higher odds of maternal overweight — the same
economic advantage that protects against one form of malnutrition exposes the mother to the other.

**Northern Cape, South Africa:** the gap between food insecurity in female-headed vs. all
households nearly tripled in four years (3.0pp in 2019, 5.8pp in 2022, 7.3pp in 2023). This is a
single-province finding — other provinces only have single-year 2023 data without this breakdown.

## Known limitations

- NRI weights (both the full 3-variable and simplified 2-variable versions) are first-pass
modeling choices, not validated or externally benchmarked.
- The 4-country real NRI-x-DBM overlap, and the 14-country simplified NRI check, are both too
small/coarse to confirm or refute the hypothesis either way.
- The simplified 2-variable NRI drops crop diversity entirely and uses different weights than the
full NRI — it's a robustness check, not a replacement, and its scores aren't on the same scale as
`nutritional_resilience_index`.
- Female decision-making measure is household-general, not agriculture-specific.
- Categorical DBM data (7-country test) is from 2010; more recent continuous DBM data only
covers the 4-country sub-Saharan African overlap (or 14, for the simplified check).
- Bawuah et al. and Stats SA data are transcribed from published tables, not raw microdata
(DHS/MICS microdata is access-gated; registration wasn't completed before the deadline).
- The food-price-substitution / post-harvest-loss pathway linking to DBM is a stated hypothesis,
not yet quantitatively tested against loss-rate data.
- `docker-compose.yml` is included but the pipeline has only been validated end-to-end against
a local Postgres.app instance, not through the container.
- The Airflow DAG has been verified to parse and build correctly under Airflow 3.x
(`apache-airflow-core>=3.0,<4.0`) — no live scheduler run has been performed.

## Sources

- FAOSTAT / Food Systems Dashboard — Cereal Import Dependency Ratio, Crop Production, DBM Classification
- FAOSTAT Suite of Food Security Indicators — manually sourced cereal import dependency
(2021-2023 avg.) for 11 countries outside the original bulk extract, used in the simplified NRI check
- World Bank / DHS — Women's Household Decision-Making (SG.DMK.ALLD.FN.ZS)
- Bawuah et al. (2026), *Maternal & Child Nutrition*, 22(1), e70175
- Statistics South Africa, GHS Report 03-10-28 (2025)
- FAO, SOFI 2026
- Dieffenbach & Stein (2012), *Journal of Nutrition*

Submitted by Buhlebethu Biyela & Zayy Ackerman for the Women in Data Datathon.