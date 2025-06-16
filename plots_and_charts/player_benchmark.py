import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import zscore

from constants import Constants


def plot_player_benchmark(
    player: str,
    game_id: int,
    player_df: pd.DataFrame,
    metrics: list[str],
    reverse_metrics: list[str],
    directory: str,
):
    # Calculate z-scores for metrics
    for metric in metrics:
        player_df[f"{metric}_zscore"] = zscore(player_df[metric], nan_policy="omit")

        # NOT DISPLAYING METRICS FOR NANs!!!
        # Ensure z-scores are finite
        # player_df[f"{metric}_zscore"] = player_df[f"{metric}_zscore"].replace(
        #     [np.inf, -np.inf], np.nan
        # )
        # player_df[f"{metric}_zscore"].fillna(0, inplace=True)

    # Create figure and subplots
    fig, axes = plt.subplots(len(metrics), 1, figsize=(20, len(metrics) * 3), sharex=True)
    fig.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
    for ax in axes:
        ax.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
    plt.rcParams["font.family"] = Constants.FONT

    # Plot each metric
    for idx, metric in enumerate(metrics):
        ax = axes[idx]

        # Reverse z-scores if metric is in reverse_metrics
        if metric in reverse_metrics:
            player_df[f"{metric}_zscore"] *= -1

        # Exclude the focus game for background plotting
        nf_df = player_df[(player_df["match_id"] != game_id) & (~player_df[f"{metric}_zscore"].isna())]
        ax.plot(
            nf_df[f"{metric}_zscore"],
            np.zeros(len(nf_df)),
            "o",
            color=Constants.COLORS["sb_grey"],
            markerfacecolor=Constants.DARKGREEN_COLOR,
            lw=2,
            markersize=20,
            alpha=0.5,
        )

        # Focus game data
        focus_df = player_df[(player_df["match_id"] == game_id) & (~player_df[f"{metric}_zscore"].isna())]
        if not focus_df.empty:
            ax.text(
                focus_df[f"{metric}_zscore"].iloc[0],
                0,
                focus_df[metric].iloc[0],
                fontweight="bold",
                color=Constants.LIGHT_TEXT_COLOR,
                fontsize=22,
                va="center",
                ha="center",
                zorder=11,
            )
            ax.scatter(
                focus_df[f"{metric}_zscore"].iloc[0],
                0,
                s=3000,
                facecolor=Constants.DARKGREEN_COLOR,
                ec=Constants.COLORS["sb_grey"],
                alpha=1,
                zorder=10,
            )

        # Max and min annotation details
        annotate_extreme_points(player_df, metric, ax, "max", y_offset=-0.0175)
        annotate_extreme_points(player_df, metric, ax, "min", y_offset=-0.0175)

        # Add vertical season average line
        ax.axvline(0, color=Constants.COLORS["white"], linestyle="--", lw=0.5)

        # Customize metric title formatting and plot aesthetics
        ax.set_title(
            metric.replace("_", "\n"),
            x=-0.135,
            y=0.51,
            fontsize=18,
            ha="center",
            va="center",
            fontweight="bold",
            color=Constants.LIGHT_TEXT_COLOR,
            bbox=dict(
                boxstyle="round,pad=.5",
                facecolor="none",
                ec=Constants.COLORS["white"],
                alpha=1,
            ),
        )
        ax.spines["bottom"].set_color(Constants.COLORS["white"])
        ax.set_yticks([])
        ax.set_xticks([])
        ax.set_xlim(-4, 4)
        for spine in ["right", "top", "left"]:
            ax.spines[spine].set_visible(False)

    # Overall plot titles and layout
    fig.suptitle(
        f'{player} | vs {focus_df["opponent"].item()} | {focus_df["match_date"].item()}',
        y=1.03,
        fontsize=40,
        color=Constants.LIGHT_TEXT_COLOR,
    )
    fig.text(
        0.1525,
        0.925,
        "Worst performance(s)",
        ha="center",
        fontsize=20,
        color=Constants.LIGHT_TEXT_COLOR,
        bbox=dict(
            boxstyle="round,pad=.5",
            facecolor=Constants.DARKGREEN_COLOR,
            ec=Constants.COLORS["white"],
            alpha=1,
        ),
    )
    fig.text(
        0.915,
        0.925,
        "Best performance(s)",
        ha="center",
        fontsize=20,
        color=Constants.LIGHT_TEXT_COLOR,
        bbox=dict(
            boxstyle="round,pad=.5",
            facecolor=Constants.DARKGREEN_COLOR,
            ec=Constants.COLORS["white"],
            alpha=1,
        ),
    )
    fig.text(
        0.532,
        0.915,
        "Season average",
        ha="center",
        fontsize=20,
        color=Constants.LIGHT_TEXT_COLOR,
        bbox=dict(
            boxstyle="round,pad=.5",
            facecolor="none",
            ec=Constants.COLORS["white"],
            alpha=1,
        ),
    )
    plt.xlabel(
        "Z-score (compared to season average)",
        color=Constants.LIGHT_TEXT_COLOR,
        fontsize=20,
    )
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    # Save the plot
    fig.savefig(
        f"{directory}/{player}_benchmark_{game_id}.png",
        facecolor=fig.get_facecolor(),
        dpi=Constants.DPI,
        bbox_inches="tight",
        pad_inches=Constants.PAD_INCHES + 0.1,
    )
    return fig


def annotate_extreme_points(player_df, metric, ax, extreme_type, y_offset):
    if extreme_type == "max":
        labels = player_df[player_df[f"{metric}_zscore"] == player_df[f"{metric}_zscore"].max()].reset_index(drop=True)
    else:
        labels = player_df[player_df[f"{metric}_zscore"] == player_df[f"{metric}_zscore"].min()].reset_index(drop=True)

    opponents = labels["opponent"].reset_index(drop=True)
    metric_value = round(labels[metric].iloc[0], 2)
    match_dates = labels["match_date"].tolist()
    z_scores = labels[f"{metric}_zscore"].reset_index(drop=True)

    for i, (opponent, date) in enumerate(zip(opponents, match_dates)):
        ax.annotate(
            f"{opponent} ({metric_value})\n{date}",
            (3.75 if extreme_type == "max" else -3.75, y_offset + i / 35),
            fontsize=16,
            color=Constants.LIGHT_TEXT_COLOR,
            ha="center",
            va="center",
        )
        if len(opponents) > 3:
            pos = (-3.75, -0.0375) if extreme_type == "min" else (3.75, -0.0375)
            ax.annotate(
                f"plus {len(opponents) - 3} other(s)",
                pos,
                fontsize=16,
                color=Constants.LIGHT_TEXT_COLOR,
                ha="center",
                va="center",
            )
