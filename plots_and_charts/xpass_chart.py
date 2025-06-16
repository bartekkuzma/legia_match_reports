import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

from constants import Constants


class ExpectedPassChart:

    def __init__(self, passes_df: pd.DataFrame, team_for: str, n_buckets: int = 5, pass_diff: int = 30) -> None:
        self.passes_df = passes_df
        self.team_for = team_for
        self.n_buckets = n_buckets
        self.pass_diff = pass_diff
        self.cmap = LinearSegmentedColormap.from_list("", Constants.CMAPLIST_XPASS)

    def preprocess_passes(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        # remove passes where outcome is unknown
        pass_df = self.passes_df[self.passes_df["pass_outcome"] != "Unknown"].copy()
        # filter to open play passes only
        pass_df = pass_df[pass_df["pass_type"].isnull()]

        # identify which bucket each pass belongs to
        buckets = pd.qcut(pass_df["pass_pass_success_probability"], q=self.n_buckets, labels=False)
        # add bucket name to dataframe as a new column
        pass_df["bucket"] = buckets

        # filter to get passes played by focus player when playing for focus team
        team_df = pass_df[pass_df["team"] == self.team_for].copy()

        # add a column to indetify if pass was complete
        conditions = [team_df["pass_outcome"].isna(), team_df["pass_outcome"].notnull()]
        choices = [1, 0]
        team_df.loc[:, "pass_success"] = np.select(conditions, choices, default=np.nan)

        # group data by bucket and get average xpass for each player & bucket
        bucket_df = team_df.groupby(["bucket", "player"]).agg({"pass_pass_success_probability": ["mean", "count"]})
        bucket_df.columns = bucket_df.columns.droplevel()
        bucket_df = bucket_df.reset_index()
        bucket_df.rename(columns={bucket_df.columns[2]: "mean_prob"}, inplace=True)

        # group data by bucket and get player pass completion % for each player & bucket
        bucket_comp_df = team_df.groupby(["bucket", "player"]).agg({"pass_success": ["mean", "count"]})
        bucket_comp_df.columns = bucket_comp_df.columns.droplevel()
        bucket_comp_df = bucket_comp_df.reset_index()
        bucket_comp_df.rename(columns={bucket_comp_df.columns[2]: "mean_completion"}, inplace=True)

        # merge thw two bucketed dataframes together
        all_players_data = pd.merge(bucket_df, bucket_comp_df, how="left", on=["bucket", "player", "count"])
        all_players_data["difference"] = all_players_data["mean_completion"] - all_players_data["mean_prob"]

        return team_df, all_players_data

    @staticmethod
    def get_players(team_data: pd.DataFrame, num_of_players: int = 8) -> list[str]:
        # get count of player passes attempted for ordering
        team_count = team_data.groupby("player").size().reset_index()
        team_count = team_count.sort_values(by=team_count.columns[1], ascending=False)
        players_list = team_count.player.unique()[:8]

        return players_list

    def plot_xpass_plot(self, directory: str, figsize: tuple[int, int] = (20, 20)):

        team_df, all_players_data = self.preprocess_passes()
        players_stats = self.get_players(team_df)
        y_span = all_players_data["count"].max() + 2
        fig, axs = plt.subplots(ncols=4, nrows=2, figsize=figsize, sharex=True, sharey=True)
        fig.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
        plt.rcParams["text.color"] = Constants.COLORS["white"]
        plt.rcParams["font.family"] = Constants.FONT

        for focus_player, ax in zip(players_stats, axs.ravel()):
            ax.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
            data = all_players_data[all_players_data["player"] == focus_player]

            data.loc[:, "mean_prob"] = data["mean_prob"] * 100
            data.loc[:, "mean_completion"] = data["mean_completion"] * 100
            data.loc[:, "difference"] = data["difference"] * 100

            total_passes = data["count"].sum()

            height = data["count"]
            bars = data["bucket"]
            scaled_data = data["difference"]
            colors = []
            cmapn = plt.get_cmap(self.cmap)
            norm = plt.Normalize(-self.pass_diff, self.pass_diff)

            for decimal in scaled_data:
                colors.append(cmapn(norm(decimal)))

            bbox = dict(boxstyle="round", fc="0.4", ec="0.1", alpha=0.8)
            bar_container = ax.bar(bars, height, color=colors, ec=Constants.COLORS["white"], lw=1, zorder=5)
            for i, (bar, color_value) in enumerate(zip(bar_container, scaled_data)):
                if color_value < (-self.pass_diff) / 3 or color_value > (self.pass_diff) / 3:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.5,
                        f"{color_value:.1f}",
                        ha="center",
                        va="bottom",
                        fontsize=15,
                        fontweight="bold",
                        color=Constants.COLORS["white"],
                        rotation=45,
                        bbox=bbox,
                        zorder=10,
                    )

            ax.set_xticks(np.arange(0, self.n_buckets, 1))
            ax.set_xticks(np.arange(0, self.n_buckets, 1), minor=True)

            ax.set_xticklabels(
                ("More difficult\npasses", "", "Avg. difficulty\npasses", "", "Easier\npasses"),
                ha="center",
                rotation=90,
                fontsize=16,
            )

            y_ticks = np.arange(0, y_span + 1, 2)
            ax.set_yticks(y_ticks)
            ax.set_yticklabels(y_ticks, fontsize=12)
            ax.set_ylim(0, y_span)

            ax.axhline(y=0, c=Constants.COLORS["white"], lw=2)
            ax.grid(which="both")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

            ax.set_title(f"{focus_player} ({total_passes})", fontsize=16, color=Constants.COLORS["white"])
            ax.tick_params(axis="x", colors=Constants.COLORS["white"])
            ax.tick_params(axis="y", colors=Constants.COLORS["white"])
            ax.spines["left"].set_color(Constants.COLORS["white"])

        fig.text(0.08, 0.5, "Number of passes", fontsize=24, va="center", rotation="vertical")

        cbar = fig.colorbar(
            plt.cm.ScalarMappable(norm=norm, cmap=cmapn),
            orientation="vertical",
            ax=axs,
            shrink=0.5,
            aspect=30,
        )
        cbar.set_ticks(
            ticks=[-self.pass_diff + 1, 0, self.pass_diff - 1],
            labels=[-self.pass_diff, "0", self.pass_diff],
            fontsize=20,
        )
        cbar.set_label("Pass completion % - Expected completion %", rotation=90, labelpad=25, fontsize=24)
        cbar.ax.tick_params(labelcolor=Constants.COLORS["white"])  # Set tick label font color
        cbar.ax.yaxis.label.set_color(Constants.COLORS["white"])  # Set the font color for the colorbar label
        cbar.outline.set_edgecolor(Constants.COLORS["white"])

        fig.text(s=f"{self.team_for}'s passing performance", x=0.1, y=0.985, fontsize=32)
        fig.text(
            s=f"Ordered by top 8 {self.team_for} players for passing volume.\nPasses grouped into equal sized bins based on all attempted passes in match.\nOpen Play passes only.\nDisplaying label when difference is greater than {int(self.pass_diff/3)}  or lower than -{int(self.pass_diff/3)}.",
            x=0.1,
            y=0.92,
            fontsize=18,
        )

        fig.savefig(
            f"{directory}/players_passing_performance.png",
            facecolor=fig.get_facecolor(),
            dpi=Constants.DPI,
            bbox_inches="tight",
            pad_inches=Constants.PAD_INCHES,
        )

        return fig
