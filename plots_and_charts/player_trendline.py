import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from constants import Constants


def plot_player_trendline(
    player: str,
    game_id: int,
    df: pd.DataFrame,
    title_stat: str,
    y_stat: str,
    directory: str,
    figsize: tuple[int, int] = (16, 10),
):
    # Create the plot
    fig, ax = plt.subplots(figsize=figsize)
    fig.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
    ax.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
    plt.rcParams["font.family"] = Constants.FONT

    x = range(len(df))

    # Add vertical direction lines first (so they appear behind other elements)
    for i, value in enumerate(df[y_stat]):
        ax.vlines(
            x=i,
            ymin=0,  # Start from bottom
            ymax=value,
            color=Constants.OFF_WHITE_COLOR,
            alpha=0.15,
            linestyle="-",
            linewidth=1,
            zorder=1,  # Put them behind other elements
        )

    # Plot the main performance line
    ax.plot(
        x,
        df[y_stat],
        color=Constants.OFF_WHITE_COLOR,
        linestyle="--",
        alpha=0.7,
        linewidth=3,
        zorder=2,
    )

    # Add scatter points
    ax.scatter(
        x,
        df[y_stat],
        color=Constants.DARK_BACKGROUND_COLOR,
        edgecolors=Constants.OFF_WHITE_COLOR,
        s=100,
        zorder=3,
    )

    # Add trend line
    x_array = np.array(x)
    y_array = np.array(df[y_stat])
    slope, intercept, r_value, p_value, std_err = stats.linregress(x_array, y_array)
    line = slope * x_array + intercept

    ax.plot(
        x_array,
        line,
        color=Constants.COLORS["yellow"],
        linestyle="-",
        linewidth=2,
        alpha=0.8,
        label=f"Trend (R² = {r_value**2:.3f})",
        zorder=2,
    )

    # Highlight selected match
    match_df = df[df["match_id"] == game_id]
    ax.scatter(
        match_df.index,
        match_df[y_stat],
        color=Constants.DARK_BACKGROUND_COLOR,
        edgecolors=Constants.COLORS["yellow"],
        s=1000,
        zorder=2,  # Put on top of everything
        linewidth=3,
    )

    # Add legend
    # ax.legend(
    #     loc='upper right',
    #     fontsize=12,
    #     facecolor=Constants.DARK_BACKGROUND_COLOR,
    #     edgecolor='none',
    #     labelcolor=Constants.COLORS["white"]
    # )

    # Rest of the styling remains the same
    fig.suptitle(
        player,
        fontsize=36,
        color=Constants.COLORS["white"],
        ha="center",
        y=1.06,
    )
    fig.text(
        0.5,
        0.97,
        f"{title_stat}",
        fontsize=26,
        color=Constants.COLORS["white"],
        ha="center",
    )
    ax.set_xlabel("Opponent", fontsize=26, color=Constants.COLORS["white"])
    ax.set_ylabel(f"{y_stat}", fontsize=26, color=Constants.COLORS["white"])
    ax.set_xticks(x)
    ax.set_xticklabels(
        df["opponent"],
        rotation=45,
        ha="right",
        fontsize=20,
        color="white",
    )
    for label in ax.get_yticklabels():
        label.set_color(Constants.COLORS["white"])
    ax.tick_params(axis="x", which="major", pad=40)
    ax.tick_params(axis="both", which="both", labelsize=16, color=Constants.COLORS["white"])

    # Match results annotations
    bbox = dict(boxstyle="round", fc="0.3", ec="0.5", alpha=0.7)
    y_min, y_max = ax.get_ylim()
    annotation_y_position = y_min + (y_max - y_min) * 0.05
    for i, result in enumerate(df["match_result"]):
        ax.text(
            i,
            annotation_y_position,
            f"{result}",
            ha="center",
            va="center",
            fontweight="bold",
            fontsize=15,
            bbox=bbox,
            rotation=0,
            color=Constants.COLORS["white"],
        )
    ax.set_ylim(annotation_y_position + (y_max - y_min) * 0.05, y_max)

    # Grid and spines
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.minorticks_on()
    ax.grid(which="minor", axis="y", linestyle=":", alpha=0.3)
    for i in ["right", "top", "left", "bottom"]:
        ax.spines[i].set_visible(False)

    plt.tight_layout()

    fig.savefig(
        f"{directory}/{player}_{y_stat}_{game_id}.png",
        facecolor=fig.get_facecolor(),
        dpi=Constants.DPI,
        bbox_inches="tight",
        pad_inches=Constants.PAD_INCHES,
    )
    return fig
