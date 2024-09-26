"""Module for analyzing and visualizing game opening pitches."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mplsoccer import VerticalPitch

from constants import Constants


class GameOpeningsPitches:
    """Class for analyzing and visualizing game opening pitches."""

    def __init__(self, goal_kicks: pd.DataFrame, team_for: str) -> None:
        """
        Initialize the GameOpeningsPitches class.

        Args:
            goal_kicks (pd.DataFrame): DataFrame containing goal kick data.
            team_for (str): The team to analyze.
        """
        self.goal_kicks = goal_kicks
        self.team_for = team_for
        self.gk_zones = [
            "P1 Left", "P1 Half Left", "P1 Central", "P1 Half Right", "P1 Right",
            "P2 Left", "P2 Half Left", "P2 Central", "P2 Half Right", "P2 Right",
            "P3 Left", "P3 Half Left", "P3 Central", "P3 Half Right", "P3 Right", "Further"
        ]

    @staticmethod
    def classify_gk_zones(x: float, y: float) -> str:
        """
        Classify the goal kick zone based on x and y coordinates.

        Args:
            x (float): X-coordinate of the kick.
            y (float): Y-coordinate of the kick.

        Returns:
            str: Classified zone or np.NaN if coordinates are invalid.
        """
        if np.isnan(x) or np.isnan(y):
            return np.NaN

        zones = ["P1", "P2", "P3"]
        zone_boundaries = [
            Constants.PITCH_DIMS["p1"],
            Constants.PITCH_DIMS["p2"],
            Constants.PITCH_DIMS["p3"]
        ]

        def get_y_zone(y_coord: float) -> str:
            """Determine the Y-axis zone."""
            if y_coord <= Constants.PITCH_DIMS["penalty_box_left_band"]:
                return "Left"
            if y_coord <= Constants.PITCH_DIMS["six_yard_box"]:
                return "Half Left"
            if y_coord <= Constants.PITCH_DIMS["pitch_width"] - Constants.PITCH_DIMS["six_yard_box"]:
                return "Central"
            if y_coord <= Constants.PITCH_DIMS["pitch_width"] - Constants.PITCH_DIMS["penalty_box_left_band"]:
                return "Half Right"
            return "Right"

        for zone, boundary in zip(zones, zone_boundaries):
            if x <= boundary:
                return f"{zone} {get_y_zone(y)}"

        return "Further"


    def prepare_data(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Prepare the goal kick data for analysis.
    
        Returns:
            pd.DataFrame: Prepared data for visualization.
        """
        goal_kicks = self.goal_kicks.copy()
        goal_kicks["x_end"] = goal_kicks['pass_end_location'].str[0]
        goal_kicks["y_end"] = goal_kicks['pass_end_location'].str[1]
    
        goal_kicks.loc[:, 'end_zone_gk'] = goal_kicks.apply(lambda row: self.classify_gk_zones(row['x_end'], row['y_end']), axis=1)   
    
        goal_kicks["pass_outcome"] = goal_kicks["pass_outcome"].fillna("Complete")
        data_points = goal_kicks[["team", "x_end", "y_end", "pass_outcome"]]
    
        grouped_data = goal_kicks.groupby(["team", "end_zone_gk", "pass_outcome"], dropna=False).count()["id"].to_frame().reset_index()
        pivot_data = grouped_data.pivot_table(index=["team", "end_zone_gk"], columns="pass_outcome", values="id", fill_value=0)
        pivot_data["ratio"] = pivot_data.apply(lambda x: f"{x.get('Complete', 0)}/{x.get('Complete', 0) + x.get('Incomplete', 0)}", axis=1)
        
        return pivot_data.reset_index(), data_points

    def plot_game_openings(self, team_for: bool, directory: str, figsize: tuple[int, int] = (16, 12)) -> plt.Figure:
        """
        Plot the game openings visualization.

        Args:
            team_for (bool): Whether to plot for the team or against.
            directory (str): Directory to save the plot.
            figsize (tuple[int, int], optional): Figure size. Defaults to (25, 18).

        Returns:
            plt.Figure: The generated plot figure.
        """
        gk_data, data_points = self.prepare_data()
        team_type = "for" if team_for else "against"
        pitch = VerticalPitch(pitch_type='statsbomb', pitch_color=Constants.DARK_BACKGROUND_COLOR, 
                              line_color=Constants.COLORS["white"], linewidth=1, goal_type='box', goal_alpha=1)
        fig, ax = pitch.draw(figsize=figsize)
        fig.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
        plt.rcParams["font.family"] = Constants.FONT

        zone_values = {zone: "0/0" for zone in self.gk_zones}

        gk_data = gk_data[(gk_data["team"] == self.team_for) == team_for]
        # Filter data
        data_points_complete = data_points[((data_points["team"] == self.team_for) == team_for) & (data_points["pass_outcome"] == "Complete")].copy()
        data_points_incomplete = data_points[((data_points["team"] == self.team_for) == team_for) & (data_points["pass_outcome"] == "Incomplete")].copy()

        # Adjust coordinates if team_for is False
        if not team_for:
            data_points_complete.loc[:, 'x_end'] = Constants.PITCH_DIMS["pitch_length"] - data_points_complete['x_end']
            data_points_complete.loc[:, 'y_end'] = Constants.PITCH_DIMS["pitch_width"] - data_points_complete['y_end']
            data_points_incomplete.loc[:, 'x_end'] = Constants.PITCH_DIMS["pitch_length"] - data_points_incomplete['x_end']
            data_points_incomplete.loc[:, 'y_end'] = Constants.PITCH_DIMS["pitch_width"] - data_points_incomplete['y_end']

        for _, row in gk_data.iterrows():
            zone = row['end_zone_gk']
            ratio = row['ratio']
            if zone in zone_values:
                zone_values[zone] = ratio

        colors = {"red": Constants.COLORS["red"], "yellow": Constants.COLORS["yellow"], "green": Constants.COLORS["green"]}

        gk_pitch_zones = self._generate_pitch_zones(team_for=team_for, zone_values=zone_values, colors=colors)

        for zone in gk_pitch_zones:
            ax.add_patch(plt.Rectangle(
                (zone['rect'][0], zone['rect'][1]),
                zone['rect'][2], zone['rect'][3],
                facecolor=zone['color'], zorder=1,
                edgecolor=Constants.COLORS["white"], linestyle='--', linewidth=1)
            )
            # Display the value in each zone
            ax.text(
                zone['rect'][0] + zone['rect'][2] / 2, 
                zone['rect'][1] + zone['rect'][3] * 0.5,
                str(zone['value']), 
                color=Constants.COLORS["white"], ha='center', va='center', fontsize=24, zorder=2)

        # Add text for "Further" passes
        further_y = Constants.PITCH_DIMS["pitch_length"] - Constants.PITCH_DIMS["p3"] + Constants.PITCH_DIMS["p3"] / 2 - 5 if team_for else Constants.PITCH_DIMS["p3"] - Constants.PITCH_DIMS["p3"] / 2 + 5
        ax.text(
            Constants.PITCH_DIMS["pitch_width"] / 2,
            further_y,
            f"{zone_values['Further']}",
            color=Constants.COLORS["white"], ha='center', va='bottom', fontsize=24, zorder=2
        )

        # Scatter plot for complete passes
        complete_scatter = pitch.scatter(
            data_points_complete.x_end, 
            data_points_complete.y_end,
            s=100,
            edgecolors=Constants.COLORS["black"],
            facecolors=Constants.COLORS["blue"], 
            marker='o',
            ax=ax,
            zorder=10,
            label="Complete"  # Add label for legend
        )

        # Scatter plot for incomplete passes
        incomplete_scatter = pitch.scatter(
            data_points_incomplete.x_end, 
            data_points_incomplete.y_end,
            s=100,
            edgecolors=Constants.COLORS["black"],
            facecolors=Constants.COLORS["white"], 
            marker='o',
            ax=ax,
            zorder=10,
            label="Incomplete"  # Add label for legend
        )

        # Add the legend to the plot
        legend_loc = "upper left" if team_for else "lower right"
        leg = ax.legend(loc=legend_loc, fontsize=20)
        for text in leg.get_texts():
            plt.setp(text, color = Constants.TEXT_COLOR)  # You can adjust location and font size as needed                        
            
        title = self.team_for if team_for else "Opponent"
        ax.set_title(f"{title}'s game openings.", fontsize=30, color=Constants.COLORS["white"], pad=30)

        fig.savefig(
            f"{directory}/openings_{team_type}.png",
            facecolor=fig.get_facecolor(),
            dpi=Constants.DPI,
            bbox_inches='tight', 
            pad_inches=Constants.PAD_INCHES
        )

        return fig

    @staticmethod
    def _generate_pitch_zones(team_for: bool, zone_values: dict[str, str], colors: dict[str, str]) -> list[dict[str, any]]:
        """
        Generate pitch zones for visualization.

        Args:
            zone_values (dict[str, str]): Dictionary of zone values.
            colors (dict[str, str]): Dictionary of colors for each zone type.

        Returns:
            list[dict[str, any]]: List of pitch zone dictionaries.
        """
        def create_zone(x: float, y: float, width: float, height: float, color: str, value: str, name: str, class_: str) -> dict[str, any]:
            return {
                "rect": [x, y, width, height],
                "color": colors[color],
                "value": value,
                "name": name,
                "class": class_,
            }

        zones = []
        for i, prefix in enumerate(["P1", "P2", "P3"]):
            if i == 0:
                height = Constants.PITCH_DIMS["p1"]
                y = 0 if team_for else Constants.PITCH_DIMS["pitch_length"] - height
            elif i == 1:
                height = Constants.PITCH_DIMS["p2"] - Constants.PITCH_DIMS["p1"]
                y = Constants.PITCH_DIMS["p1"] if team_for else Constants.PITCH_DIMS["pitch_length"] - Constants.PITCH_DIMS["p2"]     
            else:
                height = Constants.PITCH_DIMS["p3"] - Constants.PITCH_DIMS["p2"]
                y = Constants.PITCH_DIMS["p2"] if team_for else Constants.PITCH_DIMS["pitch_length"] - Constants.PITCH_DIMS["p3"]
        
            color = ["red", "yellow", "green"][i] if team_for else ["green", "yellow", "red"][i]
            left_side = 0 if team_for else Constants.PITCH_DIMS["pitch_width"] - Constants.PITCH_DIMS["penalty_box_left_band"]
            left_half = Constants.PITCH_DIMS["penalty_box_left_band"] if team_for else Constants.PITCH_DIMS["pitch_width"] - Constants.PITCH_DIMS["six_yard_box"]
            right_side = Constants.PITCH_DIMS["pitch_width"] - Constants.PITCH_DIMS["penalty_box_left_band"] if team_for else 0
            right_half = Constants.PITCH_DIMS["pitch_width"] - Constants.PITCH_DIMS["six_yard_box"] if team_for else Constants.PITCH_DIMS["penalty_box_left_band"]
            middle = Constants.PITCH_DIMS["six_yard_box"]
            zones.extend([
                create_zone(left_side, y, Constants.PITCH_DIMS["penalty_box_left_band"], height, color, zone_values[f"{prefix} Left"], f"{prefix} Left Side", prefix),
                create_zone(left_half, y, Constants.PITCH_DIMS["six_yard_box"] - Constants.PITCH_DIMS["penalty_box_left_band"], height, color, zone_values[f"{prefix} Half Left"], f"{prefix} Left Half-space", prefix),
                create_zone(middle, y, Constants.PITCH_DIMS["pitch_width"] - 2 * Constants.PITCH_DIMS["six_yard_box"], height, color, zone_values[f"{prefix} Central"], f"{prefix} Central", prefix),
                create_zone(right_half, y, Constants.PITCH_DIMS["six_yard_box"] - Constants.PITCH_DIMS["penalty_box_left_band"], height, color, zone_values[f"{prefix} Half Right"], f"{prefix} Right Half-space", prefix),
                create_zone(right_side, y, Constants.PITCH_DIMS["penalty_box_left_band"], height, color, zone_values[f"{prefix} Right"], f"{prefix} Right Side", prefix),
            ])

        return zones
    