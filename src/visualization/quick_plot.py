import matplotlib.pyplot as plt

def plot_districts(gdf, label_col="district"):
    ax = gdf.plot(edgecolor="black", linewidth=0.2, figsize=(8,8))
    ax.set_axis_off()
    plt.title("Generated Districts")
    plt.show()
