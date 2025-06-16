import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from mplsoccer import Pitch
from scipy.ndimage import gaussian_filter

from constants import Constants


class FinalThirdTouchesPlots:

    def __init__(self, match_events: pd.DataFrame, team_for: str) -> None:
        self.match_events = match_events
        self.team_for = team_for
        self.cmap_for = LinearSegmentedColormap.from_list(
            "", [Constants.COLORS["white"], Constants.COLORS["sb_grey"], Constants.COLORS["blue"]]
        )
        self.cmap_against = LinearSegmentedColormap.from_list(
            "", [Constants.COLORS["white"], Constants.COLORS["sb_grey"], Constants.COLORS["red"]]
        )

    def prepare_data(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        touches = self.match_events.loc[self.match_events["type"].isin(["Pass", "Carry", "Shot", "Dribble"])].copy()
        touches["x"] = touches["location"].str[0]
        touches["y"] = touches["location"].str[1]

        touches = touches.loc[touches["pass_type"].isna()]
        touches = touches.loc[
            (touches["x"] >= (Constants.PITCH_DIMS["pitch_length"] - Constants.PITCH_DIMS["final_third"]))
        ]
        touches_for = touches.loc[(touches["team"] == self.team_for)]
        touches_against = touches.loc[(touches["team"] != self.team_for)]
        touches_against.loc[:, "x"] = Constants.PITCH_DIMS["pitch_length"] - touches_against["x"]
        touches_against.loc[:, "y"] = Constants.PITCH_DIMS["pitch_width"] - touches_against["y"]

        return touches_for, touches_against

    def plot_final_third_touches(self, directory: str, figsize: tuple[int, int] = (25, 18)):

        data_for, data_against = self.prepare_data()
        pitch = Pitch(
            pitch_type="statsbomb",
            pitch_color=Constants.DARK_BACKGROUND_COLOR,
            line_color=Constants.COLORS["white"],
            line_zorder=3,
            pad_top=10,
        )
        fig, ax = plt.subplots(nrows=1, ncols=1, figsize=figsize, constrained_layout=True)
        fig.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
        pitch.draw(ax=ax)

        plt.rcParams["text.color"] = Constants.COLORS["white"]
        plt.rcParams["font.family"] = Constants.FONT

        pitch.scatter(
            data_for.x,
            data_for.y,
            s=300,
            edgecolors=Constants.COLORS["sb_grey"],
            c=Constants.COLORS["blue"],
            marker="o",
            ax=ax,
            zorder=10,
        )

        pitch.scatter(
            data_against.x,
            data_against.y,
            s=300,
            edgecolors=Constants.COLORS["sb_grey"],
            c=Constants.COLORS["red"],
            marker="o",
            ax=ax,
            zorder=10,
        )

        bin_statistic = pitch.bin_statistic(data_for.x, data_for.y, statistic="count", bins=(12, 8))
        bin_statistic["statistic"] = gaussian_filter(bin_statistic["statistic"], 1)
        pitch.heatmap(
            bin_statistic, ax=ax, cmap=self.cmap_for, edgecolors=Constants.COLORS["white"], zorder=1, alpha=0.75
        )

        bin_statistic = pitch.bin_statistic(data_against.x, data_against.y, statistic="count", bins=(12, 8))
        bin_statistic["statistic"] = gaussian_filter(bin_statistic["statistic"], 1)
        pitch.heatmap(
            bin_statistic, ax=ax, cmap=self.cmap_against, edgecolors=Constants.COLORS["white"], zorder=1, alpha=0.5
        )

        rect = plt.Rectangle([40, 0], 40, 80, color=Constants.DARK_BACKGROUND_COLOR, zorder=2, alpha=1)
        ax.add_artist(rect)

        total_for = len(data_for)
        total_against = len(data_against)
        total = total_for + total_against
        percent_for = round(total_for / total * 100, 1)
        percent_against = round(total_against / total * 100, 1)
        ax.text(
            32.5,
            -2.5,
            s=f"Opposition:\n{total_against} ({percent_against}%)",
            fontsize=30,
            ha="center",
            weight="bold",
            color=Constants.COLORS["red"],
        )
        ax.text(
            87.5,
            -2.5,
            s=f"{self.team_for}:\n{total_for} ({percent_for}%)",
            fontsize=30,
            ha="center",
            weight="bold",
            color=Constants.COLORS["blue"],
        )

        ax.arrow(37, -8, -5, 0, width=0.35, color=Constants.COLORS["red"])
        ax.arrow(84, -8, 5, 0, width=0.35, color=Constants.COLORS["blue"])

        fig.text(x=0.05, y=1.05, s=f"Open Play touches in final 3rd", fontsize=40, weight="bold")
        fig.text(
            x=0.05,
            y=1.02,
            s=f"A touch is defined as the start point of any pass, dribble, carry or shot.",
            fontsize=32,
        )

        fig.savefig(
            f"{directory}/touches_in_final_3rd.png",
            facecolor=fig.get_facecolor(),
            dpi=Constants.DPI,
            bbox_inches="tight",
            pad_inches=Constants.PAD_INCHES,
        )

        return fig
