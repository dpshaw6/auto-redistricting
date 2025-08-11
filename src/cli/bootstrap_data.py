from pathlib import Path
import argparse

# repo root resolver (works no matter where you run it from)
REPO_ROOT = Path(__file__).resolve().parents[2]

# local imports
from src.processing.fetch_census import (
    get_state_fips, list_counties_in_state,
    download_tabblock20, download_cd118,
    fetch_pl_block_pop_state
)

def main():
    p = argparse.ArgumentParser(description="Bootstrap Census/TIGER data for a state.")
    p.add_argument("--state", required=True, help="State postal (OR, NY, TX) or FIPS (41, 36, 48)")
    p.add_argument("--blocks", action="store_true", help="Download tabblock20 and unzip")
    p.add_argument("--pl", action="store_true", help="Fetch PL94-171 block population CSV")
    p.add_argument("--cd", action="store_true", help="Download congressional districts (cd118) and unzip")
    args = p.parse_args()

    state = args.state.upper()
    fips = get_state_fips(state)
    if not fips:
        raise SystemExit(f"Unknown state: {state}")

    # folders
    raw_dir = REPO_ROOT / "data" / "raw"
    state_dir = raw_dir / state
    blocks_dir = state_dir / "blocks"
    pl_dir = state_dir / "pl94"
    cd_dir = state_dir / "districts"
    blocks_dir.mkdir(parents=True, exist_ok=True)
    pl_dir.mkdir(parents=True, exist_ok=True)
    cd_dir.mkdir(parents=True, exist_ok=True)

    if args.blocks:
        print(f"[+] Downloading tabblock20 for {state} ({fips})...")
        download_tabblock20(fips, out_dir=blocks_dir)

    if args.pl:
        print(f"[+] Fetching PL94-171 block population via API for {state}...")
        counties = list_counties_in_state(fips)   # auto list (no hardcoding)
        out_csv = pl_dir / f"{state.lower()}_pl94_blocks.csv"
        fetch_pl_block_pop_state(fips, counties, out_csv)

    if args.cd:
        print(f"[+] Downloading 118th Congress districts (cd118) for {state}...")
        download_cd118(fips, out_dir=cd_dir)

    print("[✓] Done.")

if __name__ == "__main__":
    main()
