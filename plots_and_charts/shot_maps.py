import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mplsoccer import VerticalPitch

from constants import Constants
from utils import unpack_coordinates


class ShotMaps:
    """Class for analyzing and visualizing game opening pitches."""

    def __init__(self, shots_df: pd.DataFrame, team_for: str) -> None:
        """
        Initialize the KeyPassesPitches class.

        Args:
            match_events (pd.DataFrame): DataFrame containing passes data.
            team_for (str): The team to analyze.
        """
        self.shots_df = shots_df
        self.team_for = team_for

    def prepare_data(self, team_for: bool) -> pd.DataFrame:
        team_shots = self.shots_df[(self.shots_df["team"] == self.team_for) == team_for]
        shots_xyz = team_shots['location'].apply(unpack_coordinates, args=(3,)).apply(pd.Series).rename(columns={0: 'x', 1: 'y', 2: 'z'})
        team_shots = pd.concat([team_shots, shots_xyz], axis=1)

        return team_shots
    
    def plot_shot_map(self, team_for: bool, directory: str, figsize: tuple[int, int] = (25, 18)) -> plt.Figure:
        shots = self.prepare_data(team_for)
        team_type = "for" if team_for else "against"

        total_shots = shots.shape[0]
        total_goals = shots[shots['shot_outcome'] == 'Goal'].shape[0]
        total_xG = shots['shot_statsbomb_xg'].sum()
        xG_per_shot = total_xG / total_shots
        points_average_distance = shots['x'].mean()
        actual_average_distance = 120 - shots['x'].mean()

        pitch = VerticalPitch(
            pitch_type='statsbomb', 
            half=True, 
            pitch_color=Constants.DARK_BACKGROUND_COLOR, 
            pad_bottom=.5, 
            line_color=Constants.COLORS["white"],
            linewidth=.75,
            axis=True, label=True
        )

        # create a subplot with 2 rows and 1 column
        fig = plt.figure(figsize=(8, 12))
        fig.patch.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
        title = self.team_for if team_for else "Opponent"
        plt.rcParams["font.family"] = Constants.FONT
        # Top row for the team names and score
        # [left, bottom, width, height]

        ax1 = fig.add_axes([0, 0.6, 1, .2])
        ax1.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
        ax1.set_xlim(0, 1)
        ax1.set_ylim(0, 1)

        ax1.text(x=0.65, y=.75, s=f"{title}'s shots from the match.", fontsize=28, fontweight='bold', color=Constants.COLORS["white"], ha='center')
        ax1.set_axis_off()

        ax2 = fig.add_axes([0.05, 0.25, .9, .5])
        ax2.set_facecolor(Constants.DARK_BACKGROUND_COLOR)

        pitch.draw(ax=ax2)
        # create a scatter plot at y 100 - average_distance
        ax2.scatter(x=10, y=points_average_distance, s=100, color=Constants.COLORS["white"], linewidth=.8)
        # create a line from the bottom of the pitch to the scatter point
        ax2.plot([10, 10], [120, points_average_distance], color=Constants.COLORS["white"], linewidth=2)
        # Add a text label for the average distance
        ax2.text(x=10, y=points_average_distance - 5, s=f'Average Distance\n{actual_average_distance:.2f} m.', fontsize=10, color=Constants.COLORS["white"], ha='center')
        for x in shots.to_dict(orient='records'):
            pitch.scatter(
                x['x'], 
                x['y'], 
                s=500 * x['shot_statsbomb_xg'], 
                color=Constants.COLORS["red"] if x['shot_outcome'] == 'Goal' else Constants.DARK_BACKGROUND_COLOR, 
                ax=ax2,
                alpha=.7,
                linewidth=1,
                edgecolor=Constants.COLORS["white"]
            )
            
        ax2.set_axis_off()

        # add another axis for the stats
        ax3 = fig.add_axes([1, .2, 0.3, .05])
        ax3.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
        ax3.set_xlim(0, 1)
        ax3.set_ylim(0, 1)


        ax3.text(x=0.5, y=8.5, s='Shots', fontsize=20, fontweight='bold', color=Constants.COLORS["white"], ha='center')
        ax3.text(x=0.5, y=8, s=f'{total_shots}', fontsize=16, color='red', ha='center')
        ax3.text(x=0.5, y=6.5, s='Goals', fontsize=20, fontweight='bold', color=Constants.COLORS["white"], ha='center')
        ax3.text(x=0.5, y=6, s=f'{total_goals}', fontsize=16, color='red', ha='center')
        ax3.text(x=0.5, y=4.5, s='xG', fontsize=20, fontweight='bold', color=Constants.COLORS["white"], ha='center')
        ax3.text(x=0.5, y=4, s=f'{total_xG:.2f}', fontsize=16, color='red', ha='center')
        ax3.text(x=0.5, y=2.5, s='xG/Shot', fontsize=20, fontweight='bold', color=Constants.COLORS["white"], ha='center')
        ax3.text(x=0.5, y=2, s=f'{xG_per_shot:.2f}', fontsize=16, color='red', ha='center')

        ax3.set_axis_off()


        # add another axis for the stats
        ax4 = fig.add_axes([0, 0.1, 1, .2])
        ax4.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
        ax4.set_xlim(0, 1)
        ax4.set_ylim(0, 1)


        ax4.text(x=0.22, y=0.5, s=f'Low Quality Chance', fontsize=15, color=Constants.COLORS["white"], ha='center')
        ax4.scatter(x=0.37, y=0.53, s=100, color=Constants.DARK_BACKGROUND_COLOR, edgecolor=Constants.COLORS["white"], linewidth=1.5)
        ax4.scatter(x=0.42, y=0.53, s=200, color=Constants.DARK_BACKGROUND_COLOR, edgecolor=Constants.COLORS["white"], linewidth=1.5)
        ax4.scatter(x=0.48, y=0.53, s=300, color=Constants.DARK_BACKGROUND_COLOR, edgecolor=Constants.COLORS["white"], linewidth=1.5)
        ax4.scatter(x=0.54, y=0.53, s=400, color=Constants.DARK_BACKGROUND_COLOR, edgecolor=Constants.COLORS["white"], linewidth=1.5)
        ax4.scatter(x=0.6, y=0.53, s=500, color=Constants.DARK_BACKGROUND_COLOR, edgecolor=Constants.COLORS["white"], linewidth=1.5)
        ax4.text(x=0.78, y=0.5, s=f'High Quality Chance', fontsize=15, color=Constants.COLORS["white"], ha='center')

        ax4.text(x=0.43, y=0.27, s=f'Goal', fontsize=15, color=Constants.COLORS["white"], ha='right')
        ax4.scatter(x=0.47, y=0.3, s=300, color='red', edgecolor=Constants.COLORS["white"], linewidth=1, alpha=.7)
        ax4.scatter(x=0.53, y=0.3, s=300, color=Constants.DARK_BACKGROUND_COLOR, edgecolor=Constants.COLORS["white"], linewidth=1)
        ax4.text(x=0.57, y=0.27, s=f'No Goal', fontsize=15, color=Constants.COLORS["white"], ha='left')
        ax4.set_axis_off()

        fig.savefig(
            f"{directory}/shot_maps_{team_type}.png",
            facecolor=fig.get_facecolor(),
            dpi=Constants.DPI,
            bbox_inches='tight', 
            pad_inches=Constants.PAD_INCHES
        )

        return fig
    