# src/cli/generate_plan.py
from pathlib import Path
import argparse
from src.processing.build_block_graph import load_blocks, attach_population, build_adjacency
from src.algorithms.seed_grow import grow_regions
import geopandas as gpd
import yaml
from src.algorithms.repair_swap import border_swaps
import pickle

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_FIPS = {"OR":"41","NY":"36","TX":"48"}

def run(state_code: str, blocks_path: Path, pl94_csv: Path, out_path: Path, configs_path=REPO_ROOT/"configs/states.yaml"):
    print(f"[run] state={state_code}")
    print(f"[run] blocks_path={blocks_path}")
    print(f"[run] pl94_csv={pl94_csv}")
    if not blocks_path.exists():
        raise FileNotFoundError(f"Blocks shapefile not found: {blocks_path}")
    if not pl94_csv.exists():
        raise FileNotFoundError(f"PL94 CSV not found: {pl94_csv}")

    cfg = yaml.safe_load(Path(configs_path).read_text())[state_code]
    k = cfg["districts_congress"]; tol = cfg["pop_tolerance"]

    # Load & attach pop with defensive logging
    print("[run] loading blocks…")
    blocks = load_blocks(blocks_path)
    print(f"[run] blocks loaded: {len(blocks)} rows, cols={list(blocks.columns)}")

    print("[run] attaching population…")
    blocks = attach_population(blocks, pl94_csv)
    if "pop" not in blocks.columns:
        raise RuntimeError("Population column 'pop' missing after attach_population()")
    total_pop = int(blocks["pop"].sum())
    target = total_pop / k
    print(f"[run] total_pop={total_pop:,}, target≈{int(target):,}")

    print("[run] building adjacency… (first time on big states can be slow)")
    G = build_adjacency(blocks)
    print(f"[run] graph nodes={G.number_of_nodes()}, edges={G.number_of_edges()}")

    geoid_to_pop = dict(zip(blocks["geoid"], blocks["pop"]))
    print("[run] growing regions…")
    assignment, region_pop = grow_regions(G, geoid_to_pop, k, target, tol)

    # Optional repair step if you added it:
    try:
        from src.algorithms.repair_swap import border_swaps
        print("[run] repair swaps…")
        assignment = border_swaps(G, assignment, geoid_to_pop, target, tol)
        # recompute pops
        from collections import defaultdict
        acc = defaultdict(int)
        for n, d in assignment.items():
            acc[d] += geoid_to_pop[n]
        region_pop = [acc[i] for i in range(k)]
    except Exception:
        pass

    print("[run] dissolving to districts…")
    blocks["district"] = blocks["geoid"].map(assignment)
    districts = blocks.dissolve(by="district", aggfunc={"pop":"sum"}).reset_index()

    # Write based on extension
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ext = out_path.suffix.lower()
    print(f"[run] writing {out_path} …")
    if ext == ".gpkg":
        districts.to_file(out_path, layer="districts", driver="GPKG")
    elif ext in (".geojson", ".json"):
        districts.to_file(out_path, driver="GeoJSON")
    else:
        districts.to_file(out_path)  # let GeoPandas infer

    return total_pop, region_pop, target, out_path

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
