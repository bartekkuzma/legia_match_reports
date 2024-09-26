import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mplsoccer import VerticalPitch

from constants import Constants
from utils import unpack_coordinates


class Zone14Passes:

    def __init__(self, passes: pd.DataFrame, team_for: str) -> None:
        """
        Initialize the Zone14Passes class.

        Args:
            match_events (pd.DataFrame): DataFrame containing passes data.
            team_for (str): The team to analyze.
        """
        self.passes = passes
        self.team_for = team_for

    @staticmethod
    def is_pass_zone_14(x: float, y: float) -> bool:
        if x >= Constants.PITCH_DIMS["zone_14_x"] and x <= Constants.PITCH_DIMS["zone_14_x"] + Constants.PITCH_DIMS["zone_14_length"]:
            if y >= Constants.PITCH_DIMS["zone_14_y"] and y <= Constants.PITCH_DIMS["zone_14_y"] + Constants.PITCH_DIMS["zone_14_width"]:
                return True
        return False

    def prepare_data(self) -> pd.DataFrame:
        df_unpacked = pd.concat([
            self.passes['location'].apply(unpack_coordinates, args=(3,)).apply(pd.Series).rename(columns={0: 'x', 1: 'y', 2: 'z'}),
            self.passes['pass_end_location'].apply(unpack_coordinates, args=(2,)).apply(pd.Series).rename(columns={0: 'pass_end_x', 1: 'pass_end_y'}),
        ], axis=1)
        # Concatenate the new columns to the original dataframe
        df = pd.concat([self.passes.copy(), df_unpacked], axis=1)

        df["pass_to_zone_14"] = df.apply(lambda x: self.is_pass_zone_14(x["pass_end_x"], x["pass_end_y"]), axis=1)
        df["pass_from_zone_14"] = df.apply(lambda x: self.is_pass_zone_14(x["x"], x["y"]), axis=1)

        return df

    def plot_passes_to_zone_14(self, team_for: bool, directory: str, figsize: tuple[int, int] = (16, 12)) -> plt.Figure:

        data = self.prepare_data()
        data = data[(data["team"] == self.team_for) == team_for]
        data = data[(data["pass_to_zone_14"] == True) & (data["pass_from_zone_14"] == False)]

        team_type = "for" if team_for else "against"

        pitch = VerticalPitch(pitch_type='statsbomb', pitch_color=Constants.DARK_BACKGROUND_COLOR, line_color=Constants.COLORS["white"], linewidth=1, goal_type='box', goal_alpha=1)

        fig, ax = pitch.draw(figsize=figsize)
        fig.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
        plt.rcParams["font.family"] = Constants.FONT

        ax.add_patch(plt.Rectangle((Constants.PITCH_DIMS["zone_14_y"], Constants.PITCH_DIMS["zone_14_x"]), 
                                   Constants.PITCH_DIMS["zone_14_width"], Constants.PITCH_DIMS["zone_14_length"],
            facecolor=Constants.COLORS["cyan"], alpha=0.3, zorder=1,
            edgecolor=Constants.COLORS["white"], linestyle='--', linewidth=1)
        )

        complete = data[data["pass_outcome"].isna()]
        incomplete = data[data["pass_outcome"] == "Incomplete"]

        pitch.scatter(x=complete["x"], y=complete["y"], ax=ax, color=Constants.COLORS["green"])
        pitch.arrows(xstart=complete["x"], ystart=complete["y"], xend=complete["pass_end_x"], yend=complete["pass_end_y"], width=2,
             headwidth=3, headlength=4, color=Constants.COLORS["green"], ax=ax, label='Complete')
        

        pitch.scatter(x=incomplete["x"], y=incomplete["y"], ax=ax, color=Constants.COLORS["red"])
        pitch.arrows(xstart=incomplete["x"], ystart=incomplete["y"], xend=incomplete["pass_end_x"], yend=incomplete["pass_end_y"], width=2,
             headwidth=3, headlength=4, color=Constants.COLORS["red"], ax=ax, label='Incomplete')
        
        
        ax.legend(facecolor=Constants.COLORS["white"], handlelength=6, edgecolor=Constants.COLORS["sb_grey"], fontsize=20, loc='lower left', labelcolor=Constants.TEXT_COLOR)

        # Set the title
        title = self.team_for if team_for else "Opponent"
        ax_title = ax.set_title(f"{title}'s passes\nfrom outside to Zone 14.", fontsize=26, color=Constants.COLORS["white"], pad=10)

        fig.savefig(
            f"{directory}/passes_to_zone_14_{team_type}.png",
            facecolor=fig.get_facecolor(),
            dpi=Constants.DPI,
            bbox_inches='tight', 
            pad_inches=Constants.PAD_INCHES
        )

        return fig
    

    def plot_passes_from_zone_14(self, team_for: bool, directory: str, figsize: tuple[int, int] = (16, 12)) -> plt.Figure:

        data = self.prepare_data()
        data = data[(data["team"] == self.team_for) == team_for]
        data = data[(data["pass_to_zone_14"] == False) & (data["pass_from_zone_14"] == True)]

        team_type = "for" if team_for else "against"

        pitch = VerticalPitch(pitch_type='statsbomb', pitch_color=Constants.DARK_BACKGROUND_COLOR, line_color=Constants.COLORS["white"], linewidth=1, goal_type='box', goal_alpha=1)

        fig, ax = pitch.draw(figsize=figsize)
        fig.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
        plt.rcParams["font.family"] = Constants.FONT

        ax.add_patch(plt.Rectangle((Constants.PITCH_DIMS["zone_14_y"], Constants.PITCH_DIMS["zone_14_x"]), 
                                   Constants.PITCH_DIMS["zone_14_width"], Constants.PITCH_DIMS["zone_14_length"],
            facecolor=Constants.COLORS["cyan"], alpha=0.3, zorder=1,
            edgecolor=Constants.COLORS["white"], linestyle='--', linewidth=1)
        )

        complete = data[data["pass_outcome"].isna()]
        incomplete = data[data["pass_outcome"] == "Incomplete"]

        pitch.scatter(x=complete["x"], y=complete["y"], ax=ax, color=Constants.COLORS["green"])
        pitch.arrows(xstart=complete["x"], ystart=complete["y"], xend=complete["pass_end_x"], yend=complete["pass_end_y"], width=2,
             headwidth=3, headlength=4, color=Constants.COLORS["green"], ax=ax, label='Complete')
        

        pitch.scatter(x=incomplete["x"], y=incomplete["y"], ax=ax, color=Constants.COLORS["red"])
        pitch.arrows(xstart=incomplete["x"], ystart=incomplete["y"], xend=incomplete["pass_end_x"], yend=incomplete["pass_end_y"], width=2,
             headwidth=3, headlength=4, color=Constants.COLORS["red"], ax=ax, label='Incomplete')
        
        
        ax.legend(facecolor=Constants.COLORS["white"], handlelength=6, edgecolor=Constants.COLORS["sb_grey"], fontsize=20, loc='lower left', labelcolor=Constants.TEXT_COLOR)

        # Set the title
        title = self.team_for if team_for else "Opponent"
        ax_title = ax.set_title(f"{title}'s passes\nfrom Zone 14 outside.", fontsize=26, color=Constants.COLORS["white"], pad=10)

        fig.savefig(
            f"{directory}/passes_from_zone_14_{team_type}.png",
            facecolor=fig.get_facecolor(),
            dpi=Constants.DPI,
            bbox_inches='tight', 
            pad_inches=Constants.PAD_INCHES
        )

        return fig