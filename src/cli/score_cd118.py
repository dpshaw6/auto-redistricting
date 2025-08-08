from pathlib import Path
import argparse, geopandas as gpd
from src.algorithms.scoring import score_plan

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--state", choices=["OR","NY","TX"], required=True)
    args = p.parse_args()
    root = Path(__file__).resolve().parents[2]
    fips = {"OR":"41","NY":"36","TX":"48"}[args.state]
    cd = gpd.read_file(root / f"data/raw/{args.state}/districts/tl_2023_{fips}_cd118.shp")
    # try to find pop; if not present, just print count (we’ll wire pop join later)
    if "pop" not in cd.columns:
        print("Note: cd118 has no 'pop' column; compactness only.")
    cd["pp"] = cd.geometry.buffer(0).apply(lambda g: (4*3.14159*g.area)/(g.length**2) if g.length else 0)
    print(cd[["GEOID","NAMELSAD","pp"]].to_string(index=False))
if __name__ == "__main__":
    main()
