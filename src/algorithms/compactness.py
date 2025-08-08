import geopandas as gpd
import math

def polsby_popper_score(geom):
    """Calculate Polsby–Popper compactness score for a polygon."""
    area = geom.area
    perimeter = geom.length
    if perimeter == 0:
        return 0
    return (4 * math.pi * area) / (perimeter ** 2)

def perimeter_area_ratio(geom):
    """Calculate perimeter-to-area ratio for a polygon."""
    area = geom.area
    perimeter = geom.length
    if area == 0:
        return float('inf')
    return perimeter / area

def calculate_scores(gdf):
    """Add compactness metrics to a GeoDataFrame."""
    gdf = gdf.copy()
    gdf['polsby_popper'] = gdf.geometry.apply(polsby_popper_score)
    gdf['perimeter_area_ratio'] = gdf.geometry.apply(perimeter_area_ratio)
    return gdf
