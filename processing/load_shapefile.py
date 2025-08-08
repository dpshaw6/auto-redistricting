import geopandas as gpd
import os

def load_districts(shapefile_path):
    """Load congressional district shapefile into a GeoDataFrame."""
    if not os.path.exists(shapefile_path):
        raise FileNotFoundError(f"Shapefile not found: {shapefile_path}")
    gdf = gpd.read_file(shapefile_path)
    return gdf
