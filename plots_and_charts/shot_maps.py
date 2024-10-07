import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from mplsoccer import VerticalPitch

from constants import Constants
from utils import unpack_coordinates


class ShotMaps:

    def __init__(self, shots_df: pd.DataFrame, team_for: str) -> None:
        """
        Initialize the ShotMaps class.

        Args:
            match_events (pd.DataFrame): DataFrame containing passes data.
            team_for (str): The team to analyze.
        """
        self.shots_df = shots_df
        self.team_for = team_for
        self.xg_values = xg_values = [0.0, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.8, 1]
        self.cmap = LinearSegmentedColormap.from_list("", list(zip(self.xg_values, Constants.SHOT_MAP_CMAP)), N=100)


    def prepare_data(self, team_for: bool) -> pd.DataFrame:
        team_shots = self.shots_df[(self.shots_df["team"] == self.team_for) == team_for]
        shots_xyz = team_shots['location'].apply(unpack_coordinates, args=(3,)).apply(pd.Series).rename(columns={0: 'x', 1: 'y', 2: 'z'})
        team_shots = pd.concat([team_shots, shots_xyz], axis=1)

        return team_shots
    
    def plot_shot_map(self, team_for: bool, directory: str, figsize: tuple[int, int] = (8, 12)) -> plt.Figure:
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
        fig = plt.figure(figsize=figsize)
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
        ax3.text(x=0.5, y=8, s=f'{total_shots}', fontsize=16, color=Constants.COLORS["cyan"], ha='center')
        ax3.text(x=0.5, y=6.5, s='Goals', fontsize=20, fontweight='bold', color=Constants.COLORS["white"], ha='center')
        ax3.text(x=0.5, y=6, s=f'{total_goals}', fontsize=16, color=Constants.COLORS["cyan"], ha='center')
        ax3.text(x=0.5, y=4.5, s='xG', fontsize=20, fontweight='bold', color=Constants.COLORS["white"], ha='center')
        ax3.text(x=0.5, y=4, s=f'{total_xG:.2f}', fontsize=16, color=Constants.COLORS["cyan"], ha='center')
        ax3.text(x=0.5, y=2.5, s='xG/Shot', fontsize=20, fontweight='bold', color=Constants.COLORS["white"], ha='center')
        ax3.text(x=0.5, y=2, s=f'{xG_per_shot:.2f}', fontsize=16, color=Constants.COLORS["cyan"], ha='center')

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
        ax4.scatter(x=0.47, y=0.3, s=300, color=Constants.COLORS["red"], edgecolor=Constants.COLORS["white"], linewidth=1, alpha=.7)
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
    
    def plot_advanced_shot_map(self, team_for: bool, directory: str, figsize: tuple[int, int] = (8, 12)) -> plt.Figure:
        shots = self.prepare_data(team_for)
        team_type = "for" if team_for else "against"

        total_shots = shots.shape[0]
        shots_on_target = shots[shots["shot_outcome"].isin(["Saved", "Goal", "Saved to Post"])].shape[0]
        shots_off_target = shots[~shots["shot_outcome"].isin(["Saved", "Saved to Post", "Blocked", "Goal"])].shape[0]
        shots_blocked = shots[shots["shot_outcome"] == "Blocked"].shape[0]
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
        fig = plt.figure(figsize=figsize)
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
            color = self.cmap(x['shot_statsbomb_xg']) if x["shot_outcome"] != "Blocked" else Constants.COLORS["white"]
            edge_color = Constants.COLORS["green"] if x["shot_outcome"] == "Goal" else Constants.COLORS["white"]
            edge_color = edge_color if x["shot_outcome"] in ["Goal", "Saved", "Saved to Post"] else Constants.COLORS["sb_grey"]
            linewidth = 2.5 if x["shot_outcome"] in ["Goal", "Saved", "Saved to Post"] else 0.5
            linewidth = linewidth if x["shot_outcome"] != "Blocked" else 0
            alpha = 0.4 if x["shot_outcome"] in ["Blocked"] else 1
            # marker = "D" if x["shot_outcome"] == "Goal" else "o"
            zorder = 5 if x["shot_outcome"] in ["Goal", "Saved", "Saved to Post"] else 4
            pitch.scatter(
                x['x'], 
                x['y'], 
                s=300, 
                color=color,
                ax=ax2,
                zorder=zorder,
                alpha=alpha,
                # marker=marker,
                linewidth=linewidth,
                edgecolor=edge_color
            )
            
        ax2.set_axis_off()

        # add another axis for the stats
        ax3 = fig.add_axes([1, .2, 0.2, .05])
        ax3.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
        ax3.set_xlim(0, 1)
        ax3.set_ylim(0, 1)


        ax3.text(x=0.3, y=9.5, s='Shots', fontsize=16, fontweight='bold', color=Constants.COLORS["white"], ha='center')
        ax3.text(x=0.3, y=9.1, s=f'{total_shots}', fontsize=16, color=Constants.COLORS["cyan"], ha='center')
        
        ax3.text(x=0.3, y=8.3, s='Goals', fontsize=16, fontweight='bold', color=Constants.COLORS["white"], ha='center')
        ax3.text(x=0.3, y=7.9, s=f'{total_goals}', fontsize=16, color=Constants.COLORS["cyan"], ha='center')

        ax3.text(x=0.3, y=7, s='On Target', fontsize=16, fontweight='bold', color=Constants.COLORS["white"], ha='center')
        ax3.text(x=0.3, y=6.6, s=f'{shots_on_target}', fontsize=16, color=Constants.COLORS["cyan"], ha='center')

        ax3.text(x=0.3, y=5.8, s='Off Target', fontsize=16, fontweight='bold', color=Constants.COLORS["white"], ha='center')
        ax3.text(x=0.3, y=5.4, s=f'{shots_off_target}', fontsize=16, color=Constants.COLORS["cyan"], ha='center')

        ax3.text(x=0.3, y=4.6, s='Blocked', fontsize=16, fontweight='bold', color=Constants.COLORS["white"], ha='center')
        ax3.text(x=0.3, y=4.2, s=f'{shots_blocked}', fontsize=16, color=Constants.COLORS["cyan"], ha='center')
        
        ax3.text(x=0.3, y=3.4, s='xG', fontsize=16, fontweight='bold', color=Constants.COLORS["white"], ha='center')
        ax3.text(x=0.3, y=3, s=f'{total_xG:.2f}', fontsize=16, color=Constants.COLORS["cyan"], ha='center')

        ax3.text(x=0.3, y=2.2, s='xG/Shot', fontsize=16, fontweight='bold', color=Constants.COLORS["white"], ha='center')
        ax3.text(x=0.3, y=1.8, s=f'{xG_per_shot:.2f}', fontsize=16, color=Constants.COLORS["cyan"], ha='center')

        ax3.set_axis_off()


        # add another axis for the stats
        ax4 = fig.add_axes([0, 0.1, 1, 0.2])
        ax4.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
        ax4.set_xlim(0, 1)
        ax4.set_ylim(0, 1)
        size = 700
        ax4.text(x=0.16, y=0.6, s=f'Low Quality\nChance', fontsize=15, color=Constants.COLORS["white"], ha='center')
        ax4.scatter(x=0.28, y=0.68, s=size, color=self.cmap(0.0), edgecolor=Constants.COLORS["white"], linewidth=0)
        ax4.text(x=0.28, y=0.53, s=f'0.00', fontsize=15, color=Constants.COLORS["white"], ha='center')
        ax4.scatter(x=0.32, y=0.68, s=size, color=self.cmap(0.05), edgecolor=Constants.COLORS["white"], linewidth=0)
        ax4.scatter(x=0.36, y=0.68, s=size, color=self.cmap(0.075), edgecolor=Constants.COLORS["white"], linewidth=0)
        ax4.scatter(x=0.40, y=0.68, s=size, color=self.cmap(0.1), edgecolor=Constants.COLORS["white"], linewidth=0)
        ax4.scatter(x=0.44, y=0.68, s=size, color=self.cmap(0.15), edgecolor=Constants.COLORS["white"], linewidth=0)
        ax4.text(x=0.44, y=0.53, s=f'0.15', fontsize=15, color=Constants.COLORS["white"], ha='center')
        ax4.scatter(x=0.48, y=0.68, s=size, color=self.cmap(0.2), edgecolor=Constants.COLORS["white"], linewidth=0)
        
        ax4.scatter(x=0.52, y=0.68, s=size, color=self.cmap(0.25), edgecolor=Constants.COLORS["white"], linewidth=0)
        ax4.scatter(x=0.56, y=0.68, s=size, color=self.cmap(0.3), edgecolor=Constants.COLORS["white"], linewidth=0)
        ax4.text(x=0.56, y=0.53, s=f'0.30', fontsize=15, color=Constants.COLORS["white"], ha='center')
        ax4.scatter(x=0.60, y=0.68, s=size, color=self.cmap(0.4), edgecolor=Constants.COLORS["white"], linewidth=0)
        ax4.scatter(x=0.64, y=0.68, s=size, color=self.cmap(0.5), edgecolor=Constants.COLORS["white"], linewidth=0)
        ax4.scatter(x=0.68, y=0.68, s=size, color=self.cmap(0.6), edgecolor=Constants.COLORS["white"], linewidth=0)
        ax4.scatter(x=0.72, y=0.68, s=size, color=self.cmap(0.8), edgecolor=Constants.COLORS["white"], linewidth=0)
        ax4.text(x=0.72, y=0.53, s=f'0.80', fontsize=15, color=Constants.COLORS["white"], ha='center')
        ax4.text(x=0.84, y=0.6, s=f'High Quality\nChance', fontsize=15, color=Constants.COLORS["white"], ha='center')

        ax4.scatter(x=0.45, y=0.3, s=size, color=self.cmap(0.2), edgecolor=Constants.COLORS["green"], linewidth=2.5, alpha=1)
        ax4.text(x=0.3, y=0.27, s=f'Goal', fontsize=15, color=Constants.COLORS["white"], ha='center')
        ax4.scatter(x=0.55, y=0.3, s=size, color=self.cmap(0.2), edgecolor=Constants.COLORS["white"], linewidth=2.5, alpha=1)
        ax4.text(x=0.7, y=0.27, s=f'On Target', fontsize=15, color=Constants.COLORS["white"], ha='center')
        ax4.scatter(x=0.55, y=0.1, s=size, color=self.cmap(0.2), edgecolor=Constants.COLORS["sb_grey"], linewidth=0.5, alpha=1)
        ax4.text(x=0.7, y=0.07, s=f'Off Target', fontsize=15, color=Constants.COLORS["white"], ha='center')
        ax4.scatter(x=0.45, y=0.1, s=size, color=Constants.COLORS["white"], edgecolor=Constants.COLORS["white"], linewidth=0, alpha=0.4)
        ax4.text(x=0.3, y=0.07, s=f'Blocked', fontsize=15, color=Constants.COLORS["white"], ha='center')
        
        ax4.set_axis_off()
                
        fig.savefig(
            f"{directory}/shot_maps_{team_type}.png",
            facecolor=fig.get_facecolor(),
            dpi=Constants.DPI,
            bbox_inches='tight', 
            pad_inches=Constants.PAD_INCHES
        )

        return fig