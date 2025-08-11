import os
import csv
import requests
import zipfile
from io import BytesIO
from pathlib import Path
import urllib3

# Honour CENSUS_VERIFY=0 to skip SSL verification
VERIFY_SSL = os.environ.get("CENSUS_VERIFY", "1") != "0"

_session = requests.Session()
_session.verify = VERIFY_SSL  # <-- dynamically set verification
if _session.verify is False:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _download_and_extract(url, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[+] Downloading from {url} (SSL verify={_session.verify})...")
    r = _session.get(url, timeout=180)
    r.raise_for_status()

    with zipfile.ZipFile(BytesIO(r.content)) as zf:
        zf.extractall(out_dir)

# State postal -> FIPS (add more as you expand)
_STATE_FIPS = {"OR": "41", "NY": "36", "TX": "48"}
def get_state_fips(state_or_fips: str) -> str | None:
    s = state_or_fips.upper()
    if s.isdigit() and len(s) in (2, 3):  # accept "41" or "041"
        return s.zfill(2)
    return _STATE_FIPS.get(s)

# ---------- counties ----------
def list_counties_in_state(state_fips: str) -> list[str]:
    """
    Returns 3-digit county FIPS codes for the state via Census API.
    """
    url = f"https://api.census.gov/data/2020/dec/pl?get=NAME&for=county:*&in=state:{state_fips}"
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    rows = r.json()
    # rows[0] is header; county code at index -1
    return sorted({row[-1].zfill(3) for row in rows[1:]})

# ---------- TIGER downloads ----------
def download_tabblock20(state_fips: str, out_dir: Path):
    """
    Downloads and extracts 2022-posted tabblock20 (2020 blocks) for a state.
    You can switch to TIGER2020 if you prefer: TIGER2020/TABBLOCK20/tl_2020_{fips}_tabblock20.zip
    """
    url = f"https://www2.census.gov/geo/tiger/TIGER2022/TABBLOCK20/tl_2022_{state_fips}_tabblock20.zip"
    _download_and_extract(url, out_dir)

def download_cd118(state_fips: str, out_dir: Path):
    """
    Downloads and extracts 118th Congress districts for a state.
    """
    url = f"https://www2.census.gov/geo/tiger/TIGER2023/CD/tl_2023_{state_fips}_cd118.zip"
    _download_and_extract(url, out_dir)

# ---------- PL94-171 (Total pop per block) ----------
def fetch_pl_block_pop_state(state_fips: str, counties: list[str], out_csv: Path):
    """
    Writes CSV: state,county,tract,block,geoid,pop
    Uses PL 2020 API: P1_001N = Total population.
    """
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["state","county","tract","block","geoid","pop"])

        for co in counties:
            # IMPORTANT: only request variables in 'get='. Geo fields come from for/in.
            url = (
                "https://api.census.gov/data/2020/dec/pl"
                f"?get=P1_001N&for=block:*&in=state:{state_fips}&in=county:{co}"
            )
            r = _session.get(url, timeout=240)
            r.raise_for_status()
            rows = r.json()
            if not rows or len(rows) < 2:
                continue

            header = rows[0]
            idx = {name: i for i, name in enumerate(header)}
            # Expect names: 'P1_001N', 'state', 'county', 'tract', 'block'
            for row in rows[1:]:
                try:
                    p1 = row[idx["P1_001N"]]
                    st = row[idx["state"]]
                    cnty = row[idx["county"]]
                    tr = row[idx["tract"]]
                    bl = row[idx["block"]]
                except KeyError:
                    # If the API ever renames fields, dump header for debugging
                    raise RuntimeError(f"Unexpected PL header: {header}")

                geoid = f"{st}{cnty}{tr}{bl}"
                w.writerow([st, cnty, tr, bl, geoid, p1])

