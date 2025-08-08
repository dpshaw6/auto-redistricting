from pathlib import Path
import argparse, geopandas as gpd
from src.algorithms.scoring import score_plan
import os

def main():
    os.environ.setdefault("OGR_GEOJSON_MAX_OBJ_SIZE", "0")

    p = argparse.ArgumentParser()
    p.add_argument("--plan", required=True, help="GeoJSON/Shapefile of districts (must include pop)")
    p.add_argument("--target", type=float, required=True)
    args = p.parse_args()

    g = gpd.read_file(Path(args.plan))
    plan_stats, per_d = score_plan(g, args.target)
    print("Plan:", plan_stats)
    print(per_d.to_string(index=False))

if __name__ == "__main__":
    main()
