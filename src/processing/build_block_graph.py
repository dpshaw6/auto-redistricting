# src/processing/build_block_graph.py
from pathlib import Path
import geopandas as gpd
import pandas as pd
import networkx as nx

def load_blocks(blocks_path: Path) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(blocks_path)
    # Find a GEOID-like column
    id_col = next((c for c in gdf.columns if c.upper().startswith("GEOID")), None)
    if id_col is None:
        raise ValueError(f"No GEOID* column found in {blocks_path}. Columns: {list(gdf.columns)}")
    return gdf[[id_col, "geometry"]].rename(columns={id_col: "geoid"})

def _use_pop_if_present(blocks: gpd.GeoDataFrame) -> gpd.GeoDataFrame | None:
    pop_cols = ("P1_001N","P0010001","TOT_POP","TOTAL","POP")
    for name in pop_cols:
        cand = [c for c in blocks.columns if c.upper() == name]
        if cand:
            gdf = blocks.copy()
            gdf["pop"] = pd.to_numeric(gdf[cand[0]], errors="coerce").fillna(0).astype(int)
            return gdf[["geoid","geometry","pop"]]
    return None

def attach_population(blocks: gpd.GeoDataFrame, pl94_csv: Path) -> gpd.GeoDataFrame:
    # If the block shapefile already has pop, use it
    direct = _use_pop_if_present(blocks)
    if direct is not None:
        return direct

    pop = pd.read_csv(pl94_csv, dtype=str)
    # find or build geoid
    geoid_csv_col = next((c for c in pop.columns if c.lower()=="geoid" or c.upper().startswith("GEOID")), None)
    if geoid_csv_col is None:
        cols_lower = {c.lower(): c for c in pop.columns}
        needed = {"state","county","tract","block"}
        if needed.issubset(cols_lower.keys()):
            pop["geoid"] = (
                pop[[cols_lower["state"], cols_lower["county"], cols_lower["tract"], cols_lower["block"]]]
                .astype(str).agg("".join, axis=1)
            )
            geoid_csv_col = "geoid"
        else:
            raise ValueError(f"Can't find GEOID/state/county/tract/block in {pl94_csv}. Columns: {list(pop.columns)}")

    # find population column
    pop_col = None
    for name in ("pop","P1_001N","P0010001","TOT_POP","TOTAL"):
        if name in pop.columns: pop_col = name; break
        for c in pop.columns:
            if c.upper() == name: pop_col = c; break
        if pop_col: break
    if pop_col is None:
        raise ValueError(f"Can't find population column in {pl94_csv}. Columns: {list(pop.columns)}")

    pop["pop"] = pd.to_numeric(pop[pop_col], errors="coerce").fillna(0).astype(int)
    pop = pop[[geoid_csv_col, "pop"]].rename(columns={geoid_csv_col: "geoid"})

    gdf = blocks.merge(pop, on="geoid", how="left")
    gdf["pop"] = gdf["pop"].fillna(0).astype(int)
    return gdf

def build_adjacency(blocks: gpd.GeoDataFrame) -> nx.Graph:
    """
    Build contiguity graph: nodes are block GEOIDs; edges if polygons touch along a boundary.
    Uses the GeoPandas spatial index for speed.
    """
    # spatial index (requires shapely>=2 or rtree)
    sindex = blocks.sindex
    G = nx.Graph()
    geoms = blocks.geometry.values
    geoids = blocks["geoid"].values

    for i, geoid in enumerate(geoids):
        G.add_node(geoid)

    for i, geom in enumerate(geoms):
        # candidate neighbors via bbox intersection
        for j in sindex.intersection(geom.bounds):
            if j <= i: 
                continue
            other = geoms[j]
            # require shared boundary (avoid corner-only)
            if geom.touches(other) or geom.intersects(other):
                if geom.boundary.intersects(other.boundary):
                    G.add_edge(geoids[i], geoids[j])
    return G
