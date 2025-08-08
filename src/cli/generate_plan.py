# src/cli/generate_plan.py
from pathlib import Path
import argparse
from src.processing.build_block_graph import load_blocks, attach_population, build_adjacency
from src.algorithms.seed_grow import grow_regions
import geopandas as gpd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_FIPS = {"OR":"41","NY":"36","TX":"48"}

def run(state_code: str, blocks_path: Path, pl94_csv: Path, out_geojson: Path, configs_path=REPO_ROOT/"configs/states.yaml"):
    cfg = yaml.safe_load(Path(configs_path).read_text())[state_code]
    k = cfg["districts_congress"]; tol = cfg["pop_tolerance"]

    blocks = load_blocks(blocks_path)
    blocks = attach_population(blocks, pl94_csv)
    total_pop = int(blocks["pop"].sum())
    target = total_pop / k

    G = build_adjacency(blocks)
    geoid_to_pop = dict(zip(blocks["geoid"], blocks["pop"]))
    assignment, region_pop = grow_regions(G, geoid_to_pop, k, target, tol)

    blocks["district"] = blocks["geoid"].map(assignment)
    districts = blocks.dissolve(by="district", aggfunc={"pop":"sum"}).reset_index()

    out_geojson.parent.mkdir(parents=True, exist_ok=True)
    districts.to_file(out_geojson, driver="GeoJSON")
    return total_pop, region_pop, target, out_geojson

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--state", choices=["OR","NY","TX"], default="OR")
    p.add_argument("--blocks", help="Path to tabblock20 .shp (defaults based on state)")
    p.add_argument("--pl", help="Path to PL94 CSV (defaults based on state)")
    p.add_argument("--out", help="Output GeoJSON path (defaults based on state)")
    args = p.parse_args()

    st = args.state
    fips = STATE_FIPS[st]
    blocks_path = Path(args.blocks) if args.blocks else REPO_ROOT / f"data/raw/{st}/blocks/tl_2022_{fips}_tabblock20.shp"
    pl94_csv    = Path(args.pl)     if args.pl     else REPO_ROOT / f"data/raw/{st}/pl94/{st.lower()}_pl94_blocks.csv"
    out_geojson = Path(args.out)    if args.out    else REPO_ROOT / f"data/outputs/{st}_congress_seedgrow.geojson"

    total_pop, region_pop, target, out_path = run(st, blocks_path, pl94_csv, out_geojson)
    print(f"{st}: total pop={total_pop:,}, target per district ≈ {int(target):,}")
    print("Achieved pops per district:", [int(p) for p in region_pop])
    print(f"Wrote: {out_path}")

if __name__ == "__main__":
    main()
