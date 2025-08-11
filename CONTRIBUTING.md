## Setup
- Python 3.11+ recommended
- `pip install -r requirements.txt`

## Data
Fetch state data:
python -m src.cli.bootstrap_data --state OR --blocks --pl --cd

## Generate & Score
python -m src.cli.generate_plan --state OR --out data/outputs/OR_congress_seedgrow.gpkg
python -m src.cli.score_plan --plan data/outputs/OR_congress_seedgrow.gpkg --target <TARGET>

## TLS gotchas (Windows/Corp)
Set `CENSUS_VERIFY=0` if SSL breaks; see `fetch_census.py` for fallback notes.
