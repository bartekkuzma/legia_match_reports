import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mplsoccer import VerticalPitch

from constants import Constants


class KeyPassesPitches:
    """Class for analyzing and visualizing game opening pitches."""

    def __init__(self, match_events: pd.DataFrame, team_for: str) -> None:
        """
        Initialize the KeyPassesPitches class.

        Args:
            match_events (pd.DataFrame): DataFrame containing passes data.
            team_for (str): The team to analyze.
        """
        self.match_events = match_events
        self.passes = match_events[match_events["type"] == "Pass"].copy()
        self.team_for = team_for

    def categorize_pass(self, row):
        idx = row["index"]
        before_events = self.match_events[self.match_events["index"].isin([idx-1, idx-2, idx-3])].possession_team.to_list()
        if pd.notna(row.get('dribble_outcome')) or row.get('pass_type') in ['Kick Off', 'Throw-in', 'Goal Kick', 'Recovery', 'Free Kick', 'Corner']:
            return 'Individual'
        elif any(item != row["team"] for item in before_events):
            return 'Transfer'
        else:
            return 'Positional'

    def prepare_data(self) -> pd.DataFrame:
        data = self.passes.copy()
        data.loc[:, 'x'] = data['location'].str[0]
        data.loc[:, 'y'] = data['location'].str[1]
        data.loc[:, 'x_end'] = data['pass_end_location'].str[0]
        data.loc[:, 'y_end'] = data['pass_end_location'].str[1]

        data.loc[:, 'pass_category'] = data.apply(self.categorize_pass, axis=1)
        data = data[data["pass_shot_assist"] == True]
        return data

    def plot_key_passes(self, team_for: bool, directory: str, figsize: tuple[int, int] = (25, 18)) -> plt.Figure:
        
        key_passes = self.prepare_data()
        key_passes = key_passes[(key_passes["team"] == self.team_for) == team_for]
        team_type = "for" if team_for else "against"

        pitch = VerticalPitch(pitch_type='statsbomb', positional=True, positional_linewidth=2, positional_linestyle="dotted", positional_color=Constants.COLORS["sb_grey"], 
                              pitch_color=Constants.COLORS["white"], line_color=Constants.COLORS["black"], linewidth=1, goal_type='box', goal_alpha=1)

        fig, ax = pitch.draw(figsize=figsize)
        transfer = key_passes[key_passes["pass_category"] == "Transfer"]
        positional = key_passes[key_passes["pass_category"] == "Positional"]
        individual = key_passes[key_passes["pass_category"] == "Individual"]

        pitch.scatter(x=transfer["x"], y=transfer["y"], ax=ax, color=Constants.COLORS["green"])
        pitch.arrows(xstart=transfer["x"], ystart=transfer["y"], xend=transfer["x_end"], yend=transfer["y_end"], width=2,
             headwidth=3, headlength=4, color=Constants.COLORS["green"], ax=ax, label='Transfer')
        

        pitch.scatter(x=positional["x"], y=positional["y"], ax=ax, color=Constants.COLORS["red"])
        pitch.arrows(xstart=positional["x"], ystart=positional["y"], xend=positional["x_end"], yend=positional["y_end"], width=2,
             headwidth=3, headlength=4, color=Constants.COLORS["red"], ax=ax, label='Positional')
        

        pitch.scatter(x=individual["x"], y=individual["y"], ax=ax, color=Constants.COLORS["blue"])
        pitch.arrows(xstart=individual["x"], ystart=individual["y"], xend=individual["x_end"], yend=individual["y_end"], width=2,
             headwidth=3, headlength=4, color=Constants.COLORS["blue"], ax=ax, label='Individual')

        ax.legend(facecolor=Constants.COLORS["sb_grey"], handlelength=10, edgecolor='None', fontsize=24, loc='lower left', labelcolor=Constants.COLORS["white"])
        # Set the title
        title = self.team_for if team_for else "Opponent"
        ax_title = ax.set_title(f"{title}'s key passes", fontsize=30, color=Constants.TEXT_COLOR)

        fig.savefig(
            f"{directory}/key_passes_{team_type}.png",
            facecolor=fig.get_facecolor(),
            dpi=Constants.DPI,
            bbox_inches='tight', 
            pad_inches=Constants.PAD_INCHES
        )

        return fig