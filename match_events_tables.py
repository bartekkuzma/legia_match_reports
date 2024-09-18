import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from plottable import ColDef, Table

from constants import Constants


class ShotsTables:

    def __init__(self, shots_df: pd.DataFrame, team_for: str) -> None:
        self.shots_df = shots_df
        self.team_for = team_for
        self.shot_outcomes = ["Blocked", "On target", "Off target"]

    @staticmethod
    def divide_shots(shot_outcome):
        if shot_outcome in ["Goal", "Saved", "Saved to Post"]:
            return "On target"
        if shot_outcome == "Blocked":
            return "Blocked"
        if shot_outcome in ["Off T", "Post", "Wayward"]: ## WAYWARD
            return "Off target"

    def preprocess_shots(self) -> pd.DataFrame:
        shots_df_copy = self.shots_df.copy()
        shots_df_copy["simple_outcome"] = shots_df_copy["shot_outcome"].apply(self.divide_shots)

        shots_for = self.create_teams_df(shots_df=shots_df_copy, team_for=True)
        shots_against = self.create_teams_df(shots_df=shots_df_copy, team_for=False)

        shots_combined = pd.concat([shots_for, shots_against], ignore_index=True)
        shots_combined.set_index("to_be_index", inplace=True)
        shots_combined.index.name = "shots"

        balance = shots_for.iloc[0]["id"].item() - shots_against.iloc[0]["id"].item()
        shots_combined.at["Balance", "id"] = balance
        shots_combined = shots_combined.astype({"id": int})

        return shots_combined
    
    def create_teams_df(self, shots_df: pd.DataFrame, team_for: bool) -> pd.DataFrame:
        shots = shots_df.loc[(shots_df["team"] == self.team_for) == team_for].groupby(["simple_outcome"], dropna=False).count()["id"].to_frame()
        for shot_outcome in self.shot_outcomes:
            if shot_outcome not in shots.index:
                shots.at[shot_outcome, "id"] = 0
        
        shots.sort_index(inplace=True)
        shots = shots.astype({"id": int})
        sum_of_shots = shots.sum().item()
        col_name = "Shots for" if team_for else "Shots against"
        shots.index.name = col_name
        shots.columns = [sum_of_shots]
        shots = shots.reset_index()
        new_row = pd.DataFrame([[shots.columns[0], shots.columns[1]]], columns=shots.columns)
        shots = pd.concat([new_row, shots], ignore_index=True)
        shots.columns = ["to_be_index", "id"]
        return shots
    
    def plot_team_shots_table(self, directory: str, figsize: tuple[int, int] = (4, 6)):
        shots_df = self.preprocess_shots()

        balance = shots_df.iloc[-1]["id"].item()
        color = Constants.NEGATIVE_COLOR if balance < 0 else Constants.POSITIVE_COLOR
        color = color if balance != 0 else Constants.NEUTRAL_COLOR

        table_col_defs = [
            ColDef("shots", title="Shots outcomes", width=0.75, textprops={"fontsize": 16, "ha": "left", "fontname": Constants.FONT}),
            ColDef("id", title="", width=0.5, textprops={"fontsize": 16, "ha": "center", "fontname": Constants.FONT}),
        ]

        fig, ax = plt.subplots(figsize=figsize)
        fig.set_facecolor(Constants.STREAMLIT_COLOR)
        ax.set_facecolor(Constants.BACKGROUND_COLOR)
  
        plt.rcParams["text.color"] = Constants.TEXT_COLOR
        plt.rcParams["font.family"] = Constants.FONT

        tab = Table(
            shots_df,
            column_definitions=table_col_defs,
            row_dividers=True,
            col_label_divider=True,
            footer_divider=True,
            even_row_color=Constants.EVEN_ROW_COLOR,
            odd_row_color=Constants.ODD_ROW_COLOR,
        )

        tab.rows[0].set_facecolor(Constants.HEADER_COLOR)
        tab.rows[len(shots_df) // 2].set_facecolor(Constants.HEADER_COLOR)
        tab.rows[len(shots_df)-1].set_facecolor(color)

        fig.savefig(
            f"{directory}/shots_outcome.png",
            facecolor=fig.get_facecolor(),
            dpi=Constants.DPI,
            bbox_inches='tight',
            pad_inches=Constants.PAD_INCHES
        )
        return fig
    
    def preprocess_shots_individuals(self) -> pd.DataFrame:
        team_shots = self.shots_df[self.shots_df["team"] == self.team_for][["player", "shot_outcome", "shot_statsbomb_xg"]].groupby('player')
        stats_per_player = team_shots.agg(
            num_shots=('shot_statsbomb_xg', 'size'),
            xg=('shot_statsbomb_xg', 'sum'),
            mean_xg_per_shot=('shot_statsbomb_xg', 'mean'),
        ).sort_values(["num_shots", "xg", "mean_xg_per_shot"], ascending=False).reset_index()
        
        stats_per_player['xg'] = stats_per_player['xg'].round(2)
        stats_per_player['mean_xg_per_shot'] = stats_per_player['mean_xg_per_shot'].round(3)
        stats_per_player.set_index("player", inplace=True)

        return stats_per_player

    def plot_individual_shots_table(self, directory: str, figsize: tuple[int, int] = (10, 6)):
        shots_df = self.preprocess_shots_individuals()

        table_col_defs = [
            ColDef("player", title="", width=2, textprops={"fontsize": 16, "ha": "left", "fontname": Constants.FONT}),
            ColDef("num_shots", title="Number of\nshots", width=1.5, textprops={"fontsize": 16, "ha": "center", "fontname": Constants.FONT}),
            ColDef("xg", title="xG", width=1.5, textprops={"fontsize": 16, "ha": "center", "fontname": Constants.FONT}),
            ColDef("mean_xg_per_shot", title="Mean xG\nper shot", width=1.5, textprops={"fontsize": 16, "ha": "center", "fontname": Constants.FONT}),
        ]

        fig, ax = plt.subplots(figsize=figsize)
        fig.set_facecolor(Constants.STREAMLIT_COLOR)
        ax.set_facecolor(Constants.BACKGROUND_COLOR)
  
        plt.rcParams["text.color"] = Constants.TEXT_COLOR
        plt.rcParams["font.family"] = Constants.FONT

        tab = Table(
            shots_df,
            column_definitions=table_col_defs,
            row_dividers=True,
            col_label_divider=True,
            footer_divider=True,
            even_row_color=Constants.EVEN_ROW_COLOR,
            odd_row_color=Constants.ODD_ROW_COLOR,
        )

        fig.savefig(
            f"{directory}/individual_shots.png",
            facecolor=fig.get_facecolor(),
            dpi=Constants.DPI,
            bbox_inches='tight',
            pad_inches=Constants.PAD_INCHES
        )
        return fig
    
class ThrowInsTables:
        
    def __init__(self, throw_ins_df: pd.DataFrame, team_for: str) -> None:
        self.throw_ins_df = throw_ins_df
        self.team_for = team_for
        self.throw_ins_zones = ["Low", "Mid", "High"]

    @staticmethod
    def pitch_third(location: float) -> str:
        if location[0] > 0.66 * Constants.PITCH_DIMS["pitch_length"]:
            return "High"
        if location[0] > 0.33 * Constants.PITCH_DIMS["pitch_length"]:
            return "Mid"
        return "Low"
    
    def process_single_group(self, throw_ins_df: pd.DataFrame, team_for: bool, complete: bool) -> pd.DataFrame:
        
        col_name = "Complete" if complete else "Incomplete"
        throw_ins = throw_ins_df.loc[((throw_ins_df["team"] == self.team_for) == team_for) & (throw_ins_df["pass_outcome"] == col_name)].groupby(["pitch_third"], dropna=False).count()["id"].to_frame()
        for throw_ins_zone in self.throw_ins_zones:
            if throw_ins_zone not in throw_ins.index:
                throw_ins.at[throw_ins_zone, "id"] = 0
        
        throw_ins = throw_ins.reindex(self.throw_ins_zones)
        throw_ins = throw_ins.astype({"id": int})
        sum_of_throw_ins = throw_ins.sum().item()

        throw_ins.index.name = col_name
        throw_ins.columns = [sum_of_throw_ins]
        throw_ins = throw_ins.reset_index()
        new_row = pd.DataFrame([[throw_ins.columns[0], throw_ins.columns[1]]], columns=throw_ins.columns)
        throw_ins = pd.concat([new_row, throw_ins], ignore_index=True)
        throw_ins.columns = ["to_be_index", "id"]
        return throw_ins

    def preprocess_throw_ins(self, team_for: bool) -> pd.DataFrame:
        
        throw_ins = self.throw_ins_df[self.throw_ins_df["pass_type"] == "Throw-in"].copy()
        throw_ins["pitch_third"] = throw_ins["location"].apply(self.pitch_third)
        throw_ins["pass_outcome"] = throw_ins["pass_outcome"].fillna("Complete")

        completed_throw_ins = self.process_single_group(throw_ins, team_for=team_for, complete=True)
        incompleted_throw_ins = self.process_single_group(throw_ins, team_for=team_for, complete=False)

        throw_ins_combined = pd.concat([completed_throw_ins, incompleted_throw_ins], ignore_index=True)
        throw_ins_combined.set_index("to_be_index", inplace=True)
        throw_ins_combined.index.name = "throw_ins"

        balance = completed_throw_ins.iloc[0]["id"].item() - incompleted_throw_ins.iloc[0]["id"].item()
        throw_ins_combined.at["Balance", "id"] = balance
        throw_ins_combined = throw_ins_combined.astype({"id": int})

        return throw_ins_combined

                
    def plot_throw_ins(self, directory: str, team_for: bool, figsize: tuple[int, int] = (4, 6)):
        throw_ins = self.preprocess_throw_ins(team_for)
        for_who = "for" if team_for else "against"

        negative_color = Constants.NEGATIVE_COLOR if team_for else Constants.POSITIVE_COLOR
        positive_color = Constants.POSITIVE_COLOR if team_for else Constants.NEGATIVE_COLOR

        balance = throw_ins.iloc[-1]["id"].item()
        color = negative_color if balance < 0 else positive_color
        color = color if balance != 0 else Constants.NEUTRAL_COLOR

        table_col_defs = [
            ColDef("throw_ins", title=f"Throw-ins {for_who}", width=0.75, textprops={"fontsize": 16, "ha": "left", "fontname": Constants.FONT}),
            ColDef("id", title="", width=0.5, textprops={"fontsize": 16, "ha": "center", "fontname": Constants.FONT}),
        ]

        fig, ax = plt.subplots(figsize=figsize)
        fig.set_facecolor(Constants.STREAMLIT_COLOR)
        ax.set_facecolor(Constants.BACKGROUND_COLOR)

        plt.rcParams["text.color"] = Constants.TEXT_COLOR
        plt.rcParams["font.family"] = Constants.FONT

        tab = Table(
            throw_ins,
            column_definitions=table_col_defs,
            row_dividers=True,
            col_label_divider=True,
            footer_divider=True,
            even_row_color=Constants.EVEN_ROW_COLOR,
            odd_row_color=Constants.ODD_ROW_COLOR,
        )

        tab.rows[0].set_facecolor(Constants.HEADER_COLOR)
        tab.rows[len(throw_ins) // 2].set_facecolor(Constants.HEADER_COLOR)
        tab.rows[len(throw_ins)-1].set_facecolor(color)

        fig.savefig(
            f"{directory}/throw_ins_{for_who}.png",
            facecolor=fig.get_facecolor(),
            dpi=Constants.DPI,
            bbox_inches='tight',
            pad_inches=Constants.PAD_INCHES
        )
        return fig

class RecoveriesTables:
        
    def __init__(self, match_events: pd.DataFrame, team_for: str) -> None:
        self.match_events = self.modify_match_events_timestamps(match_events)
        self.recoveries = match_events[match_events["type"] == "Ball Recovery"]
        self.team_for = team_for

    def modify_match_events_timestamps(self, match_events: pd.DataFrame) -> pd.DataFrame:
        match_events["datetime"] = match_events["timestamp"].apply(self.change_timestamp)
        return match_events
    
    @staticmethod
    def prog_pass_carry(df):
        if df["type"] == "Carry":
            if df["carry_end_location"][0] - df["location"][0] > 0:
                return 1
            else:
                return 0
        if df["type"] == "Pass":
            if df["pass_end_location"][0] - df["location"][0] > 0:
                return 1
            else:
                return 0

    @staticmethod
    def change_timestamp(timestamp):
        return datetime.datetime.strptime(timestamp, '%H:%M:%S.%f').time()
    
    @staticmethod
    def time_delta(time1, time2):
        datetime1 = datetime.datetime.combine(datetime.datetime.today(), time1)
        datetime2 = datetime.datetime.combine(datetime.datetime.today(), time2)
        
        # Calculate the difference
        time_difference = datetime1 - datetime2

        return time_difference.total_seconds()
    

    def calculate_progressive_after_recovery(self, recoveries: pd.DataFrame) -> float:
        actions_after_rec = pd.DataFrame()
        for idx, row in recoveries.iterrows():
            if self.match_events.loc[self.match_events["index"] == row["index"]+1, "type"].item() in ["Pass", "Carry"]:
                actions_after_rec = pd.concat([actions_after_rec, self.match_events.loc[self.match_events["index"] == row["index"]+1]])
        actions_after_rec["is_progressive"] = actions_after_rec.apply(lambda x: self.prog_pass_carry(x), axis=1)
        progressive_after_recovery = actions_after_rec["is_progressive"].mean()
        return progressive_after_recovery

    def calculate_lost_after_recovery(self, recoveries: pd.DataFrame) -> float:
        lost_after_rec = []
        for idx, row in recoveries.iterrows():
            recovery_time = row["datetime"]
            temp_df = self.match_events.copy()
            temp_df = temp_df.loc[temp_df["period"] == row["period"]]
            temp_df["time_delta"] = temp_df.apply(lambda x: self.time_delta(x["datetime"], recovery_time), axis=1)
            temp_df = temp_df.loc[(temp_df["time_delta"] >= 0) & (temp_df["time_delta"] <= 6)]
            if any(item != self.team_for for item in temp_df["possession_team"].to_list()):
                lost_after_rec.append(1)
            else:
                lost_after_rec.append(0)
        lost_after_recovery = sum(lost_after_rec)/len(lost_after_rec)
        return lost_after_recovery

    def calculate_recovery_after_lost(self, recoveries: pd.DataFrame) -> float:
        lost_after_rec = []
        for idx, row in recoveries.iterrows():
            recovery_time = row["datetime"]
            temp_df = self.match_events.copy()
            temp_df = temp_df.loc[temp_df["period"] == row["period"]]
            temp_df["time_delta"] = temp_df.apply(lambda x: self.time_delta(x["datetime"], recovery_time), axis=1)
            temp_df = temp_df.loc[(temp_df["time_delta"] >= 0) & (temp_df["time_delta"] <= 6)]
            if self.team_for in temp_df["possession_team"].to_list():
                lost_after_rec.append(1)
            else:
                lost_after_rec.append(0)
        recovery_after_lost = sum(lost_after_rec)/len(lost_after_rec)
        return recovery_after_lost

    def calculate_stats(self) -> pd.DataFrame:
        recoveries_for = self.recoveries[self.recoveries["team"] == self.team_for].copy()
        recoveries_against = self.recoveries[self.recoveries["team"] != self.team_for].copy()

        progressive_after_recovery = self.calculate_progressive_after_recovery(recoveries_for)
        lost_after_recovery = self.calculate_lost_after_recovery(recoveries_for)
        recovery_after_lost = self.calculate_recovery_after_lost(recoveries_against)

        recoveries_dict = {
            "% Progressive first \nPass/Carry after \nRecovery": [format(progressive_after_recovery, ".2%")],
            "% Lost within 6 seconds \nafter Recovery": [format(lost_after_recovery, ".2%")],
            "% Recovery within \n6 seconds after Lost": [format(recovery_after_lost, ".2%")],
            }
        recoveries = pd.DataFrame(recoveries_dict).T
        recoveries.columns = ["value"]

        return recoveries
    
    def plot_recovery_stats(self, directory: str, figsize: tuple[int, int] = (6, 5)):
        recoveries = self.calculate_stats()
        table_col_defs = [
                    ColDef("index", title="Recoveries stats", width=1, textprops={"fontsize": 16, "ha": "left", "fontname": Constants.FONT}),
                    ColDef("value", title="", width=1, textprops={"fontsize": 16, "ha": "center", "fontname": Constants.FONT}),
                ]

        fig, ax = plt.subplots(figsize=figsize)
        fig.set_facecolor(Constants.STREAMLIT_COLOR)
        ax.set_facecolor(Constants.BACKGROUND_COLOR)

        plt.rcParams["text.color"] = Constants.TEXT_COLOR
        plt.rcParams["font.family"] = Constants.FONT
        plt.axis('off')

        tab = Table(
            recoveries,
            column_definitions=table_col_defs,
            row_dividers=True,
            col_label_divider=True,
            footer_divider=True,
            even_row_color=Constants.EVEN_ROW_COLOR,
            odd_row_color=Constants.ODD_ROW_COLOR,
        )

        fig.savefig(
            f"{directory}/recoveries.png",
            facecolor=fig.get_facecolor(),
            dpi=Constants.DPI,
            bbox_inches='tight',
            pad_inches=Constants.PAD_INCHES
        )
        return fig
    