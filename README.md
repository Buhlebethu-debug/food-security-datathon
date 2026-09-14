# The Double Burden: Linking Female Agency, Trade Vulnerability & Household Malnutrition

A Women in Data Datathon submission combining two real-data pipelines: a country-level
Nutritional Resilience Index (NRI) and a household-level Double Burden of Malnutrition
(DBM) analysis, tested against each other where they overlap.

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
We built real, independently-sourced pipelines for both halves, and tested them
against each other for the 4 countries where they overlap.

## Data sources — all real, no synthetic/placeholder data

| Table | Source | Coverage |
|---|---|---|
| `integrated_eat_trade_matrix` (NRI inputs) | FAOSTAT (import dependency, crop production), World Bank/DHS indicator SG.DMK.ALLD.FN.ZS (household decision-making) | 7 countries |
| `dbm_by_country` (categorical DBM) | Food Systems Dashboard, Popkin et al. 2020 | 7 countries, classification based on 2010 survey data |
| `dbm_by_country_household` (continuous DBM) | Bawuah et al. (2026), *Maternal & Child Nutrition*, 22(1), e70175 | 22 sub-Saharan African countries, 103,497 DHS mother-child pairs |
| `sa_food_insecurity_by_province` | Statistics South Africa, GHS Report 03-10-28 (2025) | South Africa, 2019/2022/2023 (Northern Cape only has all 3 years with the female-headed breakdown) |

The Bawuah et al. and Stats SA tables are transcribed from published, cited tables
rather than pulled from a live API — the underlying DHS/MICS microdata is
access-gated and required registration we didn't have time to complete before the
deadline. This is stated here rather than hidden.

## Pipeline structure

```text
src/
  extract.py              # NRI pipeline: real FAOSTAT/World Bank ingestion, fails loudly if a source file is missing
  transform.py             # NRI pipeline: computes Nutritional Resilience Index
  load.py                   # NRI pipeline: loads into Postgres, rebuilds view_eat_trade_empowerment_matrix
  visualize.py               # NRI pipeline: renders data/nri_vs_dbm_chart.png

  extract_household.py    # Household pipeline: reads Bawuah et al. + Stats SA CSVs
  transform_household.py   # Household pipeline: cleans DBM survey rounds, computes gender gap, joins real NRI x real DBM (4-country overlap)
  load_household.py         # Household pipeline: loads into Postgres, rebuilds view_household_dbm_analysis

  apply_schema.py          # Applies src/schema.sql directly (optional; load.py already creates the view inline)
  schema.sql                 # View definition for view_eat_trade_empowerment_matrix

dags/
  food_insecurity_dag.py  # Airflow TaskFlow DAG for the NRI pipeline (extract -> transform -> load), validated standalone

data/
  raw/                      # Versioned, real source CSVs for both pipelines
  external/                 # Raw downloads from FAOSTAT / World Bank / Food Systems Dashboard
  processed/                 # Final integrated_eat_trade_matrix.csv
  nri_vs_dbm_chart.png       # NRI vs. DBM category chart

docker-compose.yml          # Containerized Postgres (included; pipeline has been validated
                             # against a local Postgres.app instance, not yet run through Docker)
```

## Running the NRI pipeline

```bash
pip install -r requirements.txt
cp .env.example .env   # edit if your Postgres isn't on localhost:5432
createdb food_datathon

python3 src/extract.py
python3 src/transform.py
python3 src/load.py
python3 src/visualize.py
```

Verify it landed:

```sql
SELECT * FROM view_eat_trade_empowerment_matrix ORDER BY nutritional_resilience_index DESC;
```

## Running the household-DBM pipeline

```bash
python3 src/extract_household.py
python3 src/transform_household.py
python3 src/load_household.py
```

Verify it landed:

```sql
SELECT * FROM view_household_dbm_analysis ORDER BY nutritional_resilience_index;
```

## The Nutritional Resilience Index (NRI)
NRI = (0.4 x Female Household Decision-Making Score)
+ (0.4 x Crop Diversity Evenness x 100)
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

**Household mechanism (Bawuah et al., 22 countries):** the richest households have 57% lower odds
of child stunting than the poorest, but 391% higher odds of maternal overweight — the same
economic advantage that protects against one form of malnutrition exposes the mother to the other.

**Northern Cape, South Africa:** the gap between food insecurity in female-headed vs. all
households nearly tripled in four years (3.0pp in 2019, 5.8pp in 2022, 7.3pp in 2023). This is a
single-province finding — other provinces only have single-year 2023 data without this breakdown.

## Known limitations

- NRI weights are a first-pass modeling choice, not validated or externally benchmarked.
- The 4-country real NRI-x-DBM overlap is too small to confirm or refute the hypothesis either way.
- Female decision-making measure is household-general, not agriculture-specific.
- Categorical DBM data (7-country test) is from 2010; more recent continuous DBM data only
  covers the 4-country sub-Saharan African overlap.
- Bawuah et al. and Stats SA data are transcribed from published tables, not raw microdata
  (DHS/MICS microdata is access-gated; registration wasn't completed before the deadline).
- The food-price-substitution / post-harvest-loss pathway linking to DBM is a stated hypothesis,
  not yet quantitatively tested against loss-rate data.
- `docker-compose.yml` is included but the pipeline has only been validated end-to-end against
  a local Postgres.app instance, not through the container.
- No live Airflow scheduler run has been validated; the DAG has been reviewed for correctness
  and each stage runs successfully standalone.

## Sources

- FAOSTAT / Food Systems Dashboard — Cereal Import Dependency Ratio, Crop Production, DBM Classification
- World Bank / DHS — Women's Household Decision-Making (SG.DMK.ALLD.FN.ZS)
- Bawuah et al. (2026), *Maternal & Child Nutrition*, 22(1), e70175
- Statistics South Africa, GHS Report 03-10-28 (2025)
- FAO, SOFI 2026
- Dieffenbach & Stein (2012), *Journal of Nutrition*

Submitted by Buhlebethu Biyela & Zayy Ackerman for the Women in Data Datathon.
