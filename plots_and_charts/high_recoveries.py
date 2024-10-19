import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mplsoccer import VerticalPitch

from constants import Constants
from utils import unpack_coordinates


class HighRecoveries:

    def __init__(self, match_events: pd.DataFrame, team_for: str, radius: int = 40) -> None:
        """
        Initialize the HighRecoveries class.

        Args:
            match_events (pd.DataFrame): DataFrame containing data.
            team_for (str): The team to analyze.
        """
        self.match_events = match_events
        self.team_for = team_for
        self.radius = radius

    @staticmethod
    def is_point_closer_than_radius(goal_x, goal_y, radius, x, y) -> bool:
        """
        Check if a given point is closer to the goal center than a defined radius.
        
        Parameters:
        goal_x (int): The x-coordinate of the goal center.
        goal_y (int): The y-coordinate of the goal center.
        radius (int): The radius to compare the distance to.
        x (float): The x-coordinate of the point to check.
        y (float): The y-coordinate of the point to check.
        
        Returns:
        bool: True if the point is closer to the goal center than the defined radius, False otherwise.
        """
        # Calculate the distance between the point and the goal center
        distance = np.sqrt((x - goal_x)**2 + (y - goal_y)**2)
        
        # Check if the distance is closer than the defined radius
        return distance < radius
    
    def is_new_possession(self, possession_num: int, possession_team: str) -> bool:
        previous_possession = possession_num - 1
        previous_pos_team = self.match_events[self.match_events["possession"] == previous_possession]["possession_team"].to_list()[0]
        return possession_team != previous_pos_team
    
    def lead_to_shot(self, possession_num: int) -> bool:
        possession_event_types = self.match_events[self.match_events["possession"] == possession_num]["type"].to_list()
        return "Shot" in possession_event_types
    
    def prepare_data(self) -> pd.DataFrame:

        high_recoveries = self.match_events.drop_duplicates(subset='possession', keep='first').copy()
        high_recoveries["new_possession_check"] = True
        interception_won = self.match_events[(self.match_events["type"] == "Interception") & (self.match_events["interception_outcome"] == "Won")]
        interception_won["new_possession_check"] = False
        ball_recoveries = self.match_events[(self.match_events["type"] == "Ball Recovery") & (self.match_events["ball_recovery_recovery_failure"].isna())]
        ball_recoveries["new_possession_check"] = False
        high_recoveries = pd.concat([high_recoveries, interception_won, ball_recoveries])
        
        coordinates = high_recoveries['location'].apply(unpack_coordinates, args=(2,)).apply(pd.Series).rename(columns={0: 'x', 1: 'y'})
        high_recoveries = pd.concat([high_recoveries, coordinates], axis=1)
        high_recoveries["is_high_turnover"] = high_recoveries.apply(lambda x: self.is_point_closer_than_radius(Constants.PITCH_DIMS["pitch_length"], Constants.PITCH_DIMS["pitch_width"]/2, self.radius, x["x"], x["y"]), axis=1)
        high_recoveries = high_recoveries[high_recoveries["is_high_turnover"] == True]
        high_recoveries["is_new_possession"] = high_recoveries.apply(lambda x: self.is_new_possession(x["possession"], x["possession_team"]), axis=1)
        high_recoveries = high_recoveries[((high_recoveries["is_new_possession"] == True) & (high_recoveries["new_possession_check"] == True)) | (high_recoveries["new_possession_check"] == False)]
        high_recoveries["lead_to_shot"] = high_recoveries["possession"].apply(self.lead_to_shot)

        return high_recoveries
    
    def plot_high_turnover_map(self, team_for: bool, directory: str, figsize: tuple[int, int] = (8, 12)) -> plt.Figure:

        high_recoveries = self.prepare_data()
        team_type = "for" if team_for else "against"
        high_recoveries = high_recoveries[(high_recoveries["possession_team"] == self.team_for) == team_for]
        player_all = high_recoveries.groupby("player").count().sort_values("index", ascending=False)["index"].reset_index()
        lead_to_shot = high_recoveries[high_recoveries["lead_to_shot"] == True]
        player_lead = lead_to_shot.groupby("player").count().sort_values("index", ascending=False)["index"].reset_index()
        not_lead_to_shot = high_recoveries[high_recoveries["lead_to_shot"] != True]

        pitch = VerticalPitch(pitch_type='statsbomb', half=True, pitch_color=Constants.DARK_BACKGROUND_COLOR, pad_bottom=.5, 
                              line_color=Constants.COLORS["white"], linewidth=.75, axis=True, label=True)

        fig = plt.figure(figsize=figsize)
        fig.patch.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
        title = self.team_for if team_for else "Opponent"
        plt.rcParams["font.family"] = Constants.FONT

        ax1 = fig.add_axes([0, 0.6, 1, .2])
        ax1.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
        ax1.set_xlim(0, 1)
        ax1.set_ylim(0, 1)

        ax1.text(x=0.65, y=.75, s=f"{title}'s high recoveries.", fontsize=28, fontweight='bold', color=Constants.COLORS["white"], ha='center')
        ax1.set_axis_off()

        ax2 = fig.add_axes([0.05, 0.25, .9, .5])
        ax2.set_facecolor(Constants.DARK_BACKGROUND_COLOR)

        pitch.draw(ax=ax2)

        # Define the center and radius for the high turnover area
        center_y = Constants.PITCH_DIMS["pitch_width"]/2  # The x-coordinate for the center of the high turnover area
        center_x = Constants.PITCH_DIMS["pitch_length"]  # The y-coordinate for the middle of the pitch
        # Create the filled arc area using a polygon
        num_points = 100  # Increase for smoother edges
        angles = np.linspace(np.pi, 0, num_points)  # From pi to 0 radians
        y_fill = center_y - self.radius * np.cos(angles)  # X coordinates of the filled area
        x_fill = center_x - self.radius * np.sin(angles)  # Y coordinates of the filled area

        # Add the filled polygon to the pitch
        # Close the polygon by adding the point at the bottom
        x_fill = np.concatenate((x_fill, [center_x]))  # Add the bottom point
        y_fill = np.concatenate((y_fill, [center_y]))  # Add the center point to close

        ax2.fill(y_fill, x_fill, facecolor=Constants.COLORS["blue"], edgecolor=Constants.COLORS["white"], alpha=0.3, zorder=1)
        ax2.scatter(not_lead_to_shot["y"].to_list(), not_lead_to_shot["x"].to_list(), c=Constants.COLORS["white"], edgecolor=Constants.COLORS["black"], s=100, label='High Recoveries', zorder=2, alpha=0.8)
        ax2.scatter(lead_to_shot["y"].to_list(), lead_to_shot["x"].to_list(), c='yellow', edgecolor='black', s=300, marker='*', label='Turnover Leading to Shot', zorder=3)
        
        # bbox_pass = dict(boxstyle="round", fc=Constants.COLORS["green"], ec="0.1", alpha=0.8)
        # for one_pass in high_recoveries.to_dict(orient='records'):
        #     ax2.text(one_pass["y"], one_pass["x"] - 7, one_pass["player"].replace(" ", "\n"), ha="center", fontsize=12, fontweight="bold", color=Constants.COLORS["white"], bbox=bbox_pass)
        
        ax2.set_axis_off()

        # add another axis for the stats
        ax3 = fig.add_axes([1, .2, 0.3, .05])
        ax3.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
        ax3.set_xlim(0, 1)
        ax3.set_ylim(0, 1)


        ax3.text(x=0.5, y=9, s='High Recoveries', fontsize=18, fontweight='bold', color=Constants.COLORS["white"], ha='center')
        ax3.text(x=0.5, y=8.5, s=f'{len(high_recoveries)}', fontsize=14, color=Constants.COLORS["cyan"], ha='center')
        if len(high_recoveries)>0:
            all_max = player_all['index'].max()
            player_all_max = player_all[player_all['index'] == all_max]   
            max_all_num_disp = 3 if all_max == 1 and len(player_all_max) >= 3 else len(player_all_max)
            ax3.text(x=0.5, y=7.7, s='Top player(s)', fontsize=18, fontweight='bold', color=Constants.COLORS["white"], ha='center')
            for index, player in player_all_max.iloc[:max_all_num_disp].iterrows():
                ax3.text(x=0.5, y=7.2-0.5*index, s=f'{player_all_max.iloc[index]["player"]} ({player_all_max.iloc[index]["index"]})', fontsize=14, color=Constants.COLORS["cyan"], ha='center')

        
        ax3.text(x=0.5, y=4.5, s='High recoveries\nleading to shot', fontsize=18, fontweight='bold', color=Constants.COLORS["white"], ha='center')
        ax3.text(x=0.5, y=4, s=f'{len(lead_to_shot)}', fontsize=14, color=Constants.COLORS["cyan"], ha='center')
        if len(lead_to_shot)>0:
            lead_max = player_lead['index'].max()
            player_lead_max = player_lead[player_lead['index'] == lead_max]            
            max_lead_num_disp = 3 if lead_max == 1 and len(player_lead_max) >= 3 else len(player_lead_max)
            ax3.text(x=0.5, y=3.2, s='Top player(s)', fontsize=18, fontweight='bold', color=Constants.COLORS["white"], ha='center')
            for index, player in player_lead_max.iloc[:max_lead_num_disp].iterrows():
                ax3.text(x=0.5, y=2.7-0.5*index, s=f'{player_lead_max.iloc[index]["player"]} ({player_lead_max.iloc[index]["index"]})', fontsize=14, color=Constants.COLORS["cyan"], ha='center')


        ax3.set_axis_off()


        # add another axis for the stats
        ax4 = fig.add_axes([0, 0.1, 1, 0.2])
        ax4.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
        ax4.set_xlim(0, 1)
        ax4.set_ylim(0, 1)

        ax4.text(x=0.1, y=0.5, s=f'High Recoveries - interception won, ball recovery or possessions \n\t\t\t\tthat started in the 40 meters radius of opposite goal.'.replace("\t", 8*" "), fontsize=16, color=Constants.COLORS["white"], ha='left')
        ax4.text(x=0.1, y=0.35, s=f'High Recoveries which lead to shot marked as       .', fontsize=16, color=Constants.COLORS["white"], ha='left')
        ax4.scatter(x=0.725, y=0.387, c='yellow', edgecolor='black', s=400, marker='*', zorder=3)
        ax4.set_axis_off()

        fig.savefig(
            f"{directory}/high_recoveries_{team_type}.png",
            facecolor=fig.get_facecolor(),
            dpi=Constants.DPI,
            bbox_inches='tight', 
            pad_inches=Constants.PAD_INCHES
        )

        return fig