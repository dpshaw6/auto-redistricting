import geopandas as gpd
from pathlib import Path

def load_districts(shapefile_path):
    shapefile_path = Path(shapefile_path)
    if not shapefile_path.exists():
        raise FileNotFoundError(f"Shapefile not found: {shapefile_path}")
    return gpd.read_file(shapefile_path)
