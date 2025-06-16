import json
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from plottable import ColDef, Table

from constants import Constants
from utils import unpack_coordinates


class GoalChancesTables:
    """
    A class to analyze and visualize soccer data including goals and chances.
    """

    def __init__(self, data_df: pd.DataFrame, team_for: str, data_files: dict):
        self.data = self.expand_location(data_df)
        self.team_for = team_for
        self.data_files = data_files
        self.time_ranges = [
            "1 - 15",
            "16 - 30",
            "31 - 45+",
            "45 - 60",
            "61 - 75",
            "76 - 90+",
        ]
        self.zones = [
            "Right Side",
            "Right Half-space",
            "Middle",
            "Left Half-space",
            "Left Side",
            "Penalty Box",
        ]
        self.set_piece_shots = ["Free Kick", "Penalty"]
        self.pitch_dims = Constants.PITCH_DIMS
        self.preprocess_data()

    def get_set_piece_goals_assist_place(self, row: pd.Series) -> str:
        idx = row["index"]
        match_id = row["match_id"]
        for i in range(5):
            event = self.data[(self.data["match_id"] == match_id) & (self.data["index"] == idx - i - 1)].iloc[0]
            if event["type"] == "Foul Committed":
                return self.classify_zones_simple(
                    self.pitch_dims["pitch_length"] - event["x"], self.pitch_dims["pitch_width"] - event["y"]
                )
        return self.classify_zones_simple(row["x"], row["y"])

    def get_assisted_goals_assist_place(self, row: pd.Series) -> str:
        match_id = row["match_id"]
        event = self.data[(self.data["match_id"] == match_id) & (self.data["id"] == row["shot_key_pass_id"])].iloc[0]
        return self.classify_zones_simple(event["x"], event["y"])

    def get_rest_goals_assist_place(self, row: pd.Series) -> str:
        idx = row["index"]
        match_id = row["match_id"]
        team = row["team"]
        player = row["player"]
        possession = row["possession"]
        for i in range(10):
            event = self.data[(self.data["match_id"] == match_id) & (self.data["index"] == idx - i - 1)].iloc[0]
            if (
                event["team"] == team
                and event["player"] != player
                and event["team"] == team
                and event["possession"] == possession
                and event["type"] in ["Pass", "Shot", "Dribble", "Carry"]
            ):
                return self.classify_zones_simple(event["x"], event["y"])
        return self.classify_zones_simple(row["x"], row["y"])

    def get_own_goals_assists_place(self, row: pd.Series) -> str:
        idx = row["index"]
        match_id = row["match_id"]
        team = row["team"]
        for i in range(5):
            event = self.data[(self.data["match_id"] == match_id) & (self.data["index"] == idx - i - 1)].iloc[0]
            if event["type"] == "Pass" and event["team"] == team:
                return self.classify_zones_simple(event["x"], event["y"])
        return self.classify_zones_simple(row["x"], row["y"])

    @staticmethod
    def expand_location(data: pd.DataFrame) -> pd.DataFrame:
        xyz = (
            data["location"]
            .apply(unpack_coordinates, args=(3,))
            .apply(pd.Series)
            .rename(columns={0: "x", 1: "y", 2: "z"})
        )
        data = pd.concat([data, xyz], axis=1)
        return data

    def preprocess_data(self) -> None:
        """
        Preprocess the data DataFrame by extracting location data and adding time range and zone classifications.
        """
        data = self.data.copy()
        goals = data[(data["shot_outcome"] == "Goal") | (data["type"] == "Own Goal For")]
        set_piece_goals = goals[goals["shot_type"].isin(self.set_piece_shots)]
        own_goals = goals[goals["type"] == "Own Goal For"]
        assisted_goals = goals[
            (~goals["shot_key_pass_id"].isna())
            & ~goals["id"].isin(set_piece_goals["id"].to_list() + own_goals["id"].to_list())
        ]
        rest_of_goals = goals[
            ~goals["id"].isin(
                set_piece_goals["id"].to_list() + own_goals["id"].to_list() + assisted_goals["id"].to_list()
            )
        ]

        if set_piece_goals.shape[0] > 0:
            set_piece_goals = set_piece_goals.copy()
            set_piece_goals["zone"] = set_piece_goals.apply(lambda x: self.get_set_piece_goals_assist_place(x), axis=1)
        if assisted_goals.shape[0] > 0:
            assisted_goals = assisted_goals.copy()
            assisted_goals["zone"] = assisted_goals.apply(lambda x: self.get_assisted_goals_assist_place(x), axis=1)
        if rest_of_goals.shape[0] > 0:
            rest_of_goals = rest_of_goals.copy()
            rest_of_goals["zone"] = rest_of_goals.apply(lambda x: self.get_rest_goals_assist_place(x), axis=1)
        if own_goals.shape[0] > 0:
            own_goals = own_goals.copy()
            own_goals["zone"] = own_goals.apply(lambda x: self.get_own_goals_assists_place(x), axis=1)

        goals = pd.concat([set_piece_goals, assisted_goals, rest_of_goals, own_goals])

        goals["time_range"] = goals.apply(lambda x: self.get_time_range(x), axis=1)
        if "zone" not in goals.columns:
            goals["zone"] = np.NaN
        self.data = goals

    def classify_zones_simple(self, x: float, y: float) -> str:
        """
        Classify the zone of a goal based on its x and y coordinates.

        Args:
            x (float): x-coordinate of the goal.
            y (float): y-coordinate of the goal.

        Returns:
            str: The classified zone of the goal.
        """
        if not np.isnan(x) and not np.isnan(y):
            if self.pitch_dims["penalty_box_left_band"] <= y < self.pitch_dims["six_yard_box"]:
                return "Left Half-space"
            elif (
                self.pitch_dims["pitch_width"] - self.pitch_dims["six_yard_box"]
                <= y
                <= self.pitch_dims["pitch_width"] - self.pitch_dims["penalty_box_left_band"]
            ):
                return "Right Half-space"
            elif y <= self.pitch_dims["penalty_box_left_band"]:
                return "Left Side"
            elif y >= self.pitch_dims["pitch_width"] - self.pitch_dims["penalty_box_left_band"]:
                return "Right Side"
            if x >= self.pitch_dims["pitch_length"] - self.pitch_dims["penalty_box_length"]:
                # if pitch_dims["penalty_box_left_band"] <= y <= pitch_dims["pitch_width"] - pitch_dims["penalty_box_left_band"]:
                return "Penalty Box"
            else:
                # elif pitch_dims["six_yard_box"] <= y <= pitch_dims["pitch_width"] - pitch_dims["six_yard_box"]:
                return "Middle"

        return np.NaN

    def get_time_range(self, row: pd.Series) -> str:
        """
        Get the time range for a goal based on the period and minute.

        Args:
            row (pd.Series): A row from the goals DataFrame.

        Returns:
            str: The time range of the goal.
        """
        if row["period"] == 1:
            if row["minute"] < 15:
                return "1 - 15"
            elif row["minute"] < 30:
                return "16 - 30"
            else:
                return "31 - 45+"
        if row["period"] == 2:
            if row["minute"] < 60:
                return "45 - 60"
            elif row["minute"] < 75:
                return "61 - 75"
            else:
                return "76 - 90+"

    def create_table_from_df(self, group_by: str, ranges: list, data_type: str) -> tuple:
        """
        Create a table of data grouped by a specific attribute from the DataFrame.

        Args:
            group_by (str): The attribute to group the data by.
            ranges (list): The possible ranges or categories for the grouping attribute.
            data_type (str): The type of data (e.g., 'goals' or 'chances').

        Returns:
            tuple: A tuple containing the data table and the color for the balance row.
        """
        goals_for = self.data[self.data["team"] == self.team_for].shape[0]
        goals_against = self.data[self.data["team"] != self.team_for].shape[0]
        data_for = (
            self.data[(self.data["team"] == self.team_for)].groupby([group_by], dropna=False).count()["id"].to_frame()
        )
        data_against = (
            self.data[(self.data["team"] != self.team_for)].groupby([group_by], dropna=False).count()["id"].to_frame()
        )

        for range_item in ranges:
            if range_item not in data_for.index:
                data_for.at[range_item, "id"] = 0
            if range_item not in data_against.index:
                data_against.at[range_item, "id"] = 0

        data_for.sort_index(inplace=True)
        data_against.sort_index(inplace=True)

        data_for = data_for.astype({"id": int})
        data_against = data_against.astype({"id": int})

        # Add headers
        total_for = goals_for  # data_for['id'].sum()
        total_against = goals_against  # data_against['id'].sum()
        data_for.columns = [total_for]
        data_against.columns = [total_against]

        data_for = data_for.reset_index()
        data_against = data_against.reset_index()

        new_row_for = pd.DataFrame([[f"{data_type.capitalize()} for", total_for]], columns=data_for.columns)
        new_row_against = pd.DataFrame(
            [[f"{data_type.capitalize()} against", total_against]],
            columns=data_against.columns,
        )

        data_for = pd.concat([new_row_for, data_for], ignore_index=True)
        data_for.columns = ["to_be_index", "id"]
        data_against = pd.concat([new_row_against, data_against], ignore_index=True)
        data_against.columns = ["to_be_index", "id"]

        combined_data = pd.concat([data_for, data_against])
        combined_data.columns = ["to_be_index", "id"]

        balance = total_for - total_against
        color = Constants.NEGATIVE_COLOR if balance < 0 else Constants.POSITIVE_COLOR
        color = color if balance != 0 else Constants.NEUTRAL_COLOR

        combined_data.loc[len(combined_data)] = ["Balance", balance]
        combined_data = combined_data.astype({"id": int})
        combined_data.set_index("to_be_index", inplace=True)

        return combined_data, color

    def create_table_from_file(self, group_by: str, data_file: str, data_type: str) -> tuple:
        """
        Create a table of data grouped by a specific attribute from a JSON file.

        Args:
            group_by (str): The attribute to group the data by.
            ranges (list): The possible ranges or categories for the grouping attribute.
            title (str): The title of the table.
            data_file (str): Path to the JSON file containing data.
            data_type (str): The type of data (e.g., 'goals' or 'chances').

        Returns:
            tuple: A tuple containing the data table and the color for the balance row.
        """
        data_file = data_file if os.path.isfile(data_file) else "data/temp_" + "_".join(data_file.split("_")[1:])
        with open(data_file, "r") as f:
            data = json.load(f)

        data_for = pd.DataFrame(data["data_for"]).set_index(group_by)
        data_against = pd.DataFrame(data["data_against"]).set_index(group_by)

        data_for.sort_index(inplace=True)
        data_against.sort_index(inplace=True)

        data_for = data_for.astype({"id": int})
        data_against = data_against.astype({"id": int})
        # Add headers
        total_for = data_for["id"].sum()
        total_against = data_against["id"].sum()
        data_for.columns = [total_for]
        data_against.columns = [total_against]

        data_for = data_for.reset_index()
        data_against = data_against.reset_index()

        new_row_for = pd.DataFrame([[f"{data_type.capitalize()} for", total_for]], columns=data_for.columns)
        new_row_against = pd.DataFrame(
            [[f"{data_type.capitalize()} against", total_against]],
            columns=data_against.columns,
        )

        data_for = pd.concat([new_row_for, data_for], ignore_index=True)
        data_for.columns = ["to_be_index", "id"]
        data_against = pd.concat([new_row_against, data_against], ignore_index=True)
        data_against.columns = ["to_be_index", "id"]

        combined_data = pd.concat([data_for, data_against])
        combined_data.columns = ["to_be_index", "id"]

        balance = total_for - total_against
        color = Constants.NEGATIVE_COLOR if balance < 0 else Constants.POSITIVE_COLOR
        color = color if balance != 0 else Constants.NEUTRAL_COLOR

        combined_data.loc[len(combined_data)] = ["Balance", balance]
        combined_data = combined_data.astype({"id": int})
        combined_data.set_index("to_be_index", inplace=True)

        return combined_data, color

    def create_table_plot(
        self,
        data: pd.DataFrame,
        color: str,
        title: str,
        filename: str,
        figsize: tuple[int, int] = (4, 10),
    ) -> None:
        """
        Create and save a plot of the goals table.

        Args:
            data (pd.DataFrame): The goals data to be plotted.
            color (str): The color for the balance row.
            title (str): The title of the table.
            filename (str): The filename to save the plot.
            figsize (tuple[int, int], optional): The size of the figure. Defaults to (4, 10).
        """
        table_col_defs = [
            ColDef(
                data.index.name,
                title=title,
                width=1.5,
                textprops={"fontsize": 16, "ha": "left", "fontname": Constants.FONT},
            ),
            ColDef(
                "id",
                title="",
                width=0.5,
                textprops={"fontsize": 16, "ha": "center", "fontname": Constants.FONT},
            ),
        ]

        fig, ax = plt.subplots(figsize=figsize)
        fig.set_facecolor(Constants.STREAMLIT_COLOR)
        ax.set_facecolor(Constants.BACKGROUND_COLOR)
        plt.rcParams["text.color"] = Constants.TEXT_COLOR
        plt.rcParams["font.family"] = Constants.FONT

        tab = Table(
            data,
            column_definitions=table_col_defs,
            row_dividers=True,
            col_label_divider=True,
            footer_divider=True,
            even_row_color=Constants.EVEN_ROW_COLOR,
            odd_row_color=Constants.ODD_ROW_COLOR,
        )

        tab.rows[0].set_facecolor(Constants.HEADER_COLOR)
        tab.rows[len(data) // 2].set_facecolor(Constants.HEADER_COLOR)
        tab.rows[len(data) - 1].set_facecolor(color)

        plt.tight_layout()
        plt.savefig(
            filename,
            facecolor=fig.get_facecolor(),
            dpi=Constants.DPI,
            bbox_inches="tight",
            pad_inches=Constants.PAD_INCHES,
        )
        return fig

    def generate_single_table(self, table_type: str, directory: str = None) -> plt.Figure:
        """
        Generate and return a single table plot based on the specified type.

        Args:
            table_type (str): Type of the table to generate.
                              Options: 'goals_time', 'goals_place', 'goals_type', 'chances_time', 'chances_place', 'chances_type'
            directory (str, optional): Directory to save the plot. If None, the plot won't be saved. Defaults to None.

        Returns:
            plt.Figure: The generated figure object.
        """
        data_type, attribute = table_type.split("_")
        title = f"{data_type.capitalize()} {attribute}"
        title = title if title != "Goals place" else "Assists place"
        title = "Chances assists place" if title == "Chances place" else title

        if attribute in ["time", "place"]:
            if data_type == "goals":
                ranges = self.time_ranges if attribute == "time" else self.zones
                data, color = self.create_table_from_df(
                    group_by="time_range" if attribute == "time" else "zone",
                    ranges=ranges,
                    data_type=data_type,
                )
            else:  # chances
                ranges = self.time_ranges if attribute == "time" else self.zones
                data, color = self.create_table_from_file(
                    group_by="time_range" if attribute == "time" else "zone",
                    data_file=self.data_files[table_type],
                    data_type=data_type,
                )
        else:  # type
            data, color = self.create_table_from_file(
                group_by="type",
                data_file=self.data_files[table_type],
                data_type=data_type,
            )

        figsize = (6, 10) if attribute == "type" else (4, 10)
        filename = f"{directory}/{table_type}.png" if directory else None

        fig = self.create_table_plot(data=data, color=color, title=title, filename=filename, figsize=figsize)

        return fig
