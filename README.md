# Food Insecurity & the Double Burden of Malnutrition — Data Pipeline

A small ETL pipeline supporting our Women in Data datathon submission. It
extracts, cleans, and loads two research-derived datasets into PostgreSQL,
orchestrated with an Airflow DAG — applying the ETL/DAG/Postgres workflow
from DataCamp's *Introduction to Data Engineering* course to this project's
own data.

## Why this exists

Our core finding links three things: rising food prices push households
toward cheap, energy-dense staples (the "substitution pathway"), post-harvest
loss is concentrated in the nutrient-dense foods that are already expensive,
and both are associated with the **double burden of malnutrition (DBM)** —
households where a child is undernourished while the mother is overweight
or obese. This pipeline puts the two DBM-relevant datasets behind that
finding into a queryable form instead of static spreadsheets, so any
downstream chart or dashboard reads from one source of truth.

## Data sources

| Table | Source | Notes |
|---|---|---|
| `dbm_by_country` | Bawuah et al. (2026), *Maternal & Child Nutrition*, Table 1 | 22 sub-Saharan African countries, 103,497 DHS mother-child pairs |
| `sa_food_insecurity_by_province` | Statistics South Africa, GHS Report 03-10-28 (2025) | South Africa, 2019/2022/2023 |

Both are transcribed from published, cited tables rather than pulled from a
live API — the underlying microdata (DHS/MICS) is access-gated and required
a formal registration process we didn't have time to complete before the
submission deadline. See the project's main report PDF for the full source
list and that limitation in context.

## Pipeline structure

```
src/
  extract.py   # reads the two raw CSVs, validates expected columns
  transform.py # cleans country-name inconsistencies, derives dbm_risk_tier,
               # computes the female-headed-household food-insecurity gap
  load.py      # writes analysis-ready tables to Postgres via pandas.to_sql
  etl.py       # ties extract -> transform -> load into one callable
dags/
  food_insecurity_dag.py  # Airflow TaskFlow DAG that runs etl()
data/raw/      # versioned source CSVs (see table above)
tests/         # smoke tests for extract/transform (no DB required)
```

## Running it

```bash
pip install -r requirements.txt
cp .env.example .env   # edit if your Postgres isn't on localhost:5432
createdb food_datathon
python src/etl.py
```

Verify it landed:

```sql
SELECT country, dbm_pct, dbm_risk_tier
FROM dbm_by_country
ORDER BY dbm_pct DESC
LIMIT 5;
```

## Running the DAG

```bash
export AIRFLOW_HOME=~/airflow_home
airflow standalone   # first run: initializes the metadata DB, prints a login
# copy dags/food_insecurity_dag.py into $AIRFLOW_HOME/dags/
```

The DAG is scheduled `@monthly` rather than daily. Our sources are
periodically-revised published research snapshots, not a live operational
feed — there's nothing new to extract at midnight every day. If this
pipeline is later pointed at a live-updating source (e.g. a FAOSTAT API
endpoint), the schedule can be changed back to a cron daily job.

## Known limitations

- **Sample size for the SA table is small** (11 rows) since it's a
  province-level summary, not row-level survey data — this pipeline
  demonstrates the ETL/orchestration pattern at the scale our available,
  ungated data actually supports, rather than simulating a bigger dataset.
- **`if_exists="replace"`** is used on load rather than `"append"`, since
  each run represents the latest known snapshot of these sources, not an
  incrementing log.
- No CI workflow is wired up yet (`tests/test_pipeline.py` runs locally with
  `python tests/test_pipeline.py`); adding a GitHub Actions job that runs it
  on every push would be the natural next step.
