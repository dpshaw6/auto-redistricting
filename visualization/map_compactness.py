import matplotlib.pyplot as plt

def plot_compactness(gdf, score_column='polsby_popper', cmap='viridis'):
    """Plot districts color-coded by a compactness score."""
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    gdf.plot(column=score_column, cmap=cmap, legend=True, ax=ax)
    ax.set_title(f"District Compactness by {score_column}")
    plt.show()
