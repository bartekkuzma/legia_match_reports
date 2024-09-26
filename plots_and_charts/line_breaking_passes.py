import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mplsoccer import VerticalPitch

from constants import Constants
from utils import unpack_coordinates


class LineBreakingPasses:

    def __init__(self, match_events: pd.DataFrame, team_for: str) -> None:
        """
        Initialize the LineBreakingPasses class.

        Args:
            match_events (pd.DataFrame): DataFrame containing passes data.
            team_for (str): The team to analyze.
        """
        self.match_events = match_events
        self.team_for = team_for

    def prepare_data(self) -> pd.DataFrame:
        df = self.match_events[self.match_events["type"].isin(["Pass", "Ball Receipt*"])].copy()
        df_unpacked = pd.concat([
            df['location'].apply(unpack_coordinates, args=(3,)).apply(pd.Series).rename(columns={0: 'x', 1: 'y', 2: 'z'}),
            df['pass_end_location'].apply(unpack_coordinates, args=(2,)).apply(pd.Series).rename(columns={0: 'pass_end_x', 1: 'pass_end_y'}),
        ], axis=1)
        # Concatenate the new columns to the original dataframe
        df = pd.concat([df, df_unpacked], axis=1)

        #get ball receipts in space in the final third
        ball_recs = df[(df.type == "Ball Receipt*") & (df.ball_receipt_in_space == True) & (df.distance_to_nearest_defender >= 5) & (df.x >= 80)]
        #get a list of all related events
        passes_ids = [idx-1 for idx in ball_recs["index"].to_list()]
        line_breaking_passes_ids = df[(df["index"].isin(passes_ids)) & (df["line_breaking_pass"] == True) & (df["pass_outcome"].isna())]["index"].to_list()
        ball_recs_ids = [idx + 1 for idx in line_breaking_passes_ids]
        
        data = df[df["index"].isin(line_breaking_passes_ids+ball_recs_ids)]
        return data

    def plot_line_breaking_passes(self, team_for: bool, directory: str, figsize: tuple[int, int] = (16, 12)) -> plt.Figure:

        data = self.prepare_data()
        data = data[(data["team"] == self.team_for) == team_for]
        passes = data[data["type"] == "Pass"]
        recs = data[data["type"] == "Ball Receipt*"]

        team_type = "for" if team_for else "against"

        pitch = VerticalPitch(pitch_type='statsbomb', pitch_color=Constants.DARK_BACKGROUND_COLOR, line_color=Constants.COLORS["white"], linewidth=1, goal_type='box', goal_alpha=1)

        fig, ax = pitch.draw(figsize=figsize)
        fig.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
        plt.rcParams["font.family"] = Constants.FONT
            
        #plot the passes
        bbox_pass = dict(boxstyle="round", fc=Constants.COLORS["green"], ec="0.1", alpha=0.8)
        pitch.lines(passes.x, passes.y, passes.pass_end_x, passes.pass_end_y,
                    linestyle='--', color=Constants.COLORS["sb_grey"], ax=ax, lw=2,zorder=2, label = "Line Break")
        for one_pass in passes.to_dict(orient='records'):
            ax.text(one_pass["y"], one_pass["x"] - 3, one_pass["player"].replace(" ", "\n"), ha="center", fontsize=12, fontweight="bold", color=Constants.COLORS["white"], bbox=bbox_pass)
        #plot the ball receipts
        bbox_rec = dict(boxstyle="round", fc="0.4", ec="0.1", alpha=0.8)
        sc = pitch.scatter(recs.x, recs.y,zorder=3,
                           s=recs.distance_to_nearest_defender*120,
                           facecolor=Constants.COLORS["blue"], edgecolors=Constants.COLORS["white"], marker='o', ax=ax)
        for rec in recs.to_dict(orient='records'):
            ax.text(rec["y"], rec["x"] + 4, rec["player"].replace(" ", "\n"), ha="center", fontsize=12, fontweight="bold", color=Constants.COLORS["white"], bbox=bbox_rec)
        
        #set the title
        title = self.team_for if team_for else "Opponent"
        ax_title = ax.set_title(f"{title}'s line-breaking Passes\ninto at least 5m of Space", fontsize=26, color=Constants.COLORS["white"], pad=10)

        fig.savefig(
            f"{directory}/line_breaking_passes_{team_type}.png",
            facecolor=fig.get_facecolor(),
            dpi=Constants.DPI,
            bbox_inches='tight', 
            pad_inches=Constants.PAD_INCHES
        )

        return fig