import matplotlib.pyplot as plt
import pandas as pd

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

    # Plot bars
    x = range(len(df))

    # Plot trend lines
    ax.plot(
        x,
        df[y_stat],
        color=Constants.OFF_WHITE_COLOR,
        linestyle="--",
        alpha=0.7,
        linewidth=3,
    )
    ax.scatter(
        x,
        df[y_stat],
        color=Constants.DARK_BACKGROUND_COLOR,
        edgecolors=Constants.OFF_WHITE_COLOR,
        s=100,
        zorder=3,
    )
    # MATCH
    match_df = df[df["match_id"] == game_id]
    ax.scatter(
        match_df.index,
        match_df[y_stat],
        color=Constants.DARK_BACKGROUND_COLOR,
        edgecolors=Constants.COLORS["yellow"],
        s=1000,
        zorder=1,
        linewidth=3,
    )

    # Customize the plot
    # Set the main title (suptitle)
    fig.suptitle(
        player,
        fontsize=36,
        color=Constants.COLORS["white"],
        ha="center",
        y=1.06,
    )
    # Set the subtitle
    # Set the subtitle using a second suptitle
    fig.text(
        0.5,
        0.97,
        f"{title_stat}",
        fontsize=26,
        color=Constants.COLORS["white"],
        ha="center",
    )
    # ax.set_title(f'{title_stat}', fontsize=26, pad=30, color=Constants.COLORS["white"], ha='center')
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
    ax.tick_params(
        axis="both", which="both", labelsize=16, color=Constants.COLORS["white"]
    )

    bbox = dict(boxstyle="round", fc="0.3", ec="0.5", alpha=0.7)

    # Add value labels on top of bars
    # Get the axis limits
    y_min, y_max = ax.get_ylim()
    # Calculate position for result annotations
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

    # Customize grid and minor ticks
    ax.grid(axis="y", linestyle="--", alpha=0.5)  # Major gridlines
    ax.minorticks_on()  # Enable minor ticks
    ax.grid(
        which="minor", axis="y", linestyle=":", alpha=0.3
    )  # Minor gridlines with dotted style

    for i in ["right", "top", "left", "bottom"]:
        ax.spines[i].set_visible(False)

    # Adjust layout and display the plot
    plt.tight_layout()

    fig.savefig(
        f"{directory}/{player}_{y_stat}_{game_id}.png",
        facecolor=fig.get_facecolor(),
        dpi=Constants.DPI,
        bbox_inches="tight",
        pad_inches=Constants.PAD_INCHES,
    )
    return fig
