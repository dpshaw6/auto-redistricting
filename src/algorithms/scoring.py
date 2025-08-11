# src/algorithms/scoring.py
import math
import geopandas as gpd
import pandas as pd

def polsby_popper(geom):
    A = geom.area
    P = geom.length
    if P == 0: return 0.0
    return (4*math.pi*A)/(P*P)

def population_deviation(pop_series, target):
    # returns (max dev %, mean dev %)
    dev = (pop_series - target).abs() / target
    return float(dev.max()), float(dev.mean())

def score_plan(districts_gdf: gpd.GeoDataFrame, target: float):
    g = districts_gdf.copy()
    if "pop" not in g.columns:
        raise ValueError("districts_gdf must include a 'pop' column")
    g["pp"] = g.geometry.apply(polsby_popper)
    max_dev, mean_dev = population_deviation(g["pop"], target)
    plan = {
        "n_districts": len(g),
        "pop_target": target,
        "pop_max_dev": max_dev,
        "pop_mean_dev": mean_dev,
        "pp_mean": float(g["pp"].mean()),
        "pp_min": float(g["pp"].min()),
    }
    return plan, g[["district","pop","pp"]]
