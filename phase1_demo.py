from pathlib import Path
from processing.load_shapefile import load_districts
from algorithms.compactness import calculate_scores
from visualization.map_compactness import plot_compactness

# Compute the repo root (two levels up from this file)
repo_root = Path(__file__).resolve().parents[1]
shapefile_path = repo_root / "src" / "data" / "tl_2023_41_cd118.shp"

if __name__ == "__main__":
    gdf = load_districts(shapefile_path)
    gdf_with_scores = calculate_scores(gdf)
    print(gdf_with_scores[['NAMELSAD', 'polsby_popper', 'perimeter_area_ratio']])
    plot_compactness(gdf_with_scores, score_column='polsby_popper')
