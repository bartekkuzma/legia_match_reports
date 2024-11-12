import os

import numpy as np
import pandas as pd

from utils import ensure_player_directory, get_newest_datetime, is_file_up_to_date


class PlayerStatistics:

    def __init__(self, match_events, player, team_name, match_id):
        self.periods_durations = self.calculate_periods_durations(match_events)
        self.player = player
        self.team_name = team_name
        self.match_id = match_id
        self.player_minutes_info = self.calculate_played_minutes(match_events)
        self.player_match_events = self._preprocess_match_events(match_events)
        self.player_team_events = self.player_match_events[
            self.player_match_events["team"] == team_name
        ]
        self.passes = self._preprocess_passes()
        self.carries = self._preprocess_carries()
        self.shots = self._preprocess_shots()
        self.set_pieces = ["Throw-in", "Free Kick", "Corner", "Goal Kick"]
        self.touches = [
            "Pass",
            "Ball Receipt*",
            "Carry",
            "Clearance",
            "Foul Won",
            "Block",
            "Ball Recovery",
            "Duel",
            "Dribble",
            "Interception",
            "Miscontrol",
            "Shot",
        ]
        self.box_dims = {"x": 102.0, "y_left": 18.0, "y_right": 62.0}
        self.final_third = 80.0
        self.oppostion_half = 60.0

    def _preprocess_match_events(self, match_events):
        match_events = match_events[
            (match_events["index"] >= self.player_minutes_info["start_index"])
            & (match_events["index"] <= self.player_minutes_info["end_index"])
        ].copy()
        try:
            match_events[["x", "y", "z"]] = match_events["location"].apply(pd.Series)
        except:
            match_events[["x", "y"]] = match_events["location"].apply(pd.Series)

        match_events = match_events.sort_values("index").reset_index(drop=True)
        return match_events

    def _preprocess_passes(self):
        passes = self.player_team_events[
            self.player_team_events["type"] == "Pass"
        ].copy()
        if not passes.empty:
            passes[["pass_end_x", "pass_end_y"]] = passes["pass_end_location"].apply(
                pd.Series
            )
            passes.loc[passes["pass_outcome"].isna(), "pass_outcome"] = "Complete"
        return passes

    def _preprocess_carries(self):
        carries = self.player_team_events[
            self.player_team_events["type"] == "Carry"
        ].copy()
        if not carries.empty:
            carries[["carry_end_x", "carry_end_y"]] = carries[
                "carry_end_location"
            ].apply(pd.Series)
        return carries

    def _preprocess_shots(self):
        shots = self.player_team_events[
            self.player_team_events["type"] == "Shot"
        ].copy()
        if not shots.empty:
            try:
                shots[["shot_end_x", "shot_end_y", "shot_end_z"]] = shots[
                    "shot_end_location"
                ].apply(pd.Series)
            except:
                shots[["shot_end_x", "shot_end_y"]] = shots["shot_end_location"].apply(
                    pd.Series
                )
        return shots

    # Helper function to calculate the duration between two rows, even if they span multiple periods
    @staticmethod
    def _calculate_duration_in_seconds(start_row, end_row, df):
        start_period = start_row["period"].item()
        end_period = end_row["period"].item()

        # If both rows are in the same period
        if start_period == end_period:
            start_time = start_row["minute"].item() * 60 + start_row["second"].item()
            end_time = end_row["minute"].item() * 60 + end_row["second"].item()
            return end_time - start_time

        # If rows span multiple periods
        total_duration = 0

        # 1. Calculate time from start_row to the end of its period
        start_time = start_row["minute"].item() * 60 + start_row["second"].item()
        period_end_row = df[
            (df["period"] == start_period) & (df["type"] == "Half End")
        ].iloc[0]
        period_end_time = (
            period_end_row["minute"].item() * 60 + period_end_row["second"].item()
        )
        total_duration += period_end_time - start_time

        # 2. Add full durations of any intermediate periods
        for period in range(start_period + 1, end_period):
            period_start_row = df[
                (df["period"] == period) & (df["type"] == "Half Start")
            ].iloc[0]
            period_end_row = df[
                (df["period"] == period) & (df["type"] == "Half End")
            ].iloc[0]
            period_start_time = (
                period_start_row["minute"].item() * 60
                + period_start_row["second"].item()
            )
            period_end_time = (
                period_end_row["minute"].item() * 60 + period_end_row["second"].item()
            )
            total_duration += period_end_time - period_start_time

        # 3. Calculate time from the start of the last period to end_row
        period_start_row = df[
            (df["period"] == end_period) & (df["type"] == "Half Start")
        ].iloc[0]
        period_start_time = (
            period_start_row["minute"].item() * 60 + period_start_row["second"].item()
        )
        end_time = end_row["minute"].item() * 60 + end_row["second"].item()
        total_duration += end_time - period_start_time

        return total_duration

    @staticmethod
    def _seconds_to_mmss(total_seconds):
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02}:{seconds:02}"

    # Main function to calculate each period's duration and total match duration
    @staticmethod
    def calculate_periods_durations(df):
        result = {}
        total_duration_seconds = 0

        # Calculate the duration for each period
        for period in df["period"].unique():
            start_row = df[(df["period"] == period) & (df["type"] == "Half Start")]
            end_row = df[(df["period"] == period) & (df["type"] == "Half End")]

            if not start_row.empty and not end_row.empty:
                # Calculate period duration in seconds
                period_duration_seconds = (
                    PlayerStatistics._calculate_duration_in_seconds(
                        start_row.iloc[0], end_row.iloc[0], df
                    )
                )

                # Add both formats to the result dictionary
                result[f"period_{period}_duration_seconds"] = period_duration_seconds
                result[f"period_{period}_duration_minutes"] = (
                    PlayerStatistics._seconds_to_mmss(period_duration_seconds)
                )
                result[f"period_{period}_duration_minutes_decimal"] = round(
                    period_duration_seconds / 60, 2
                )  # Decimal format

                # Add to total match duration
                total_duration_seconds += period_duration_seconds

        # Total match duration
        result["full_match_duration_minutes"] = PlayerStatistics._seconds_to_mmss(
            total_duration_seconds
        )
        result["full_match_duration_seconds"] = total_duration_seconds
        result["full_match_duration_minutes_decimal"] = round(
            total_duration_seconds / 60, 2
        )  # Decimal format

        return result

    def calculate_played_minutes(self, match_events):
        starting_xi = match_events[
            (match_events["team"] == self.team_name)
            & (match_events["type"] == "Starting XI")
        ]["tactics"].item()
        starting_players_ids = [
            player["player"]["id"] for player in starting_xi["lineup"]
        ]
        player_id_df = match_events[match_events["player"] == self.player]

        if player_id_df.empty:
            played_time_seconds = 0
            played_time_minutes = 0
            played_time_minutes_decimal = 0
            start_index = 0
            end_index = 0
        else:
            player_id = player_id_df.iloc[0]["player_id"]
            was_subbed_on = match_events[
                (match_events["substitution_replacement"] == self.player)
            ]
            if player_id in starting_players_ids:
                start_index = 1
                first_event = match_events[match_events["index"] == start_index]
                substitution = match_events[
                    (match_events["player"] == self.player)
                    & (match_events["type"] == "Substitution")
                ]
                if not substitution.empty:
                    played_time_seconds = (
                        PlayerStatistics._calculate_duration_in_seconds(
                            first_event, substitution, match_events
                        )
                    )
                    played_time_minutes = PlayerStatistics._seconds_to_mmss(
                        played_time_seconds
                    )
                    played_time_minutes_decimal = round(played_time_seconds / 60, 2)
                    end_index = substitution["index"].item()
                else:
                    played_time_seconds = self.periods_durations[
                        "full_match_duration_seconds"
                    ]
                    played_time_minutes = self.periods_durations[
                        "full_match_duration_minutes"
                    ]
                    played_time_minutes_decimal = self.periods_durations[
                        "full_match_duration_minutes_decimal"
                    ]
                    end_index = match_events.iloc[-1]["index"]
            elif not was_subbed_on.empty:
                start_index = was_subbed_on["index"].item()
                substitution = match_events[
                    (match_events["player"] == self.player)
                    & (match_events["type"] == "Substitution")
                ]
                if not substitution.empty:
                    played_time_seconds = (
                        PlayerStatistics._calculate_duration_in_seconds(
                            was_subbed_on, substitution, match_events
                        )
                    )
                    played_time_minutes = PlayerStatistics._seconds_to_mmss(
                        played_time_seconds
                    )
                    played_time_minutes_decimal = round(played_time_seconds / 60, 2)
                    end_index = substitution["index"].item()
                else:
                    end_match_row = match_events.iloc[-1]
                    played_time_seconds = (
                        PlayerStatistics._calculate_duration_in_seconds(
                            was_subbed_on, end_match_row, match_events
                        )
                    )
                    played_time_minutes = PlayerStatistics._seconds_to_mmss(
                        played_time_seconds
                    )
                    played_time_minutes_decimal = round(played_time_seconds / 60, 2)
                    end_index = end_match_row["index"]
            else:
                played_time_seconds = 0
                played_time_minutes = 0
                played_time_minutes_decimal = 0
                start_index = 0
                end_index = 0

        ret = {
            "played_time_second": played_time_seconds,
            "played_time_minutes": played_time_minutes,
            "played_time_minutes_decimal": played_time_minutes_decimal,
            "start_index": start_index,
            "end_index": end_index,
        }

        return ret

    # SUCCESSFUL PASSES UNDER PRESSURE
    def count_passes_under_pressure(self):
        total_passes_under_pressure = self.passes[
            (self.passes["player"] == self.player)
            & (self.passes["under_pressure"] == True)
        ].shape[0]
        completed_passes_under_pressure = self.passes[
            (self.passes["player"] == self.player)
            & (self.passes["under_pressure"] == True)
            & (self.passes["pass_outcome"] == "Complete")
        ].shape[0]

        ratio_passes_under_pressure = (
            completed_passes_under_pressure / total_passes_under_pressure
            if total_passes_under_pressure != 0
            else np.NaN
        )

        ret = {
            "total_passes_under_pressure": total_passes_under_pressure,
            "completed_passes_under_pressure": completed_passes_under_pressure,
            "ratio_passes_under_pressure": ratio_passes_under_pressure,
        }

        return ret

    # PROGRESSIVE PASSES
    def count_progressive_passes(self):
        total_progressive_passes = self.passes[
            (self.passes["player"] == self.player)
            & (self.passes["pass_end_x"] > self.passes["x"])
        ].shape[0]

        completed_progressive_passes = self.passes[
            (self.passes["player"] == self.player)
            & (self.passes["pass_end_x"] > self.passes["x"])
            & (self.passes["pass_outcome"] == "Complete")
        ].shape[0]

        ratio_progressive_passes = (
            completed_progressive_passes / total_progressive_passes
            if total_progressive_passes != 0
            else np.NaN
        )

        ret = {
            "total_progressive_passes": total_progressive_passes,
            "completed_progressive_passes": completed_progressive_passes,
            "ratio_progressive_passes": ratio_progressive_passes,
        }

        return ret

    # LONG BALL ACCURACY (as per SB long ball >= 35 yards)
    def count_long_balls(self, length=35.0):
        total_long_balls = self.passes[
            (self.passes["player"] == self.player)
            & (self.passes["pass_length"] >= length)
        ].shape[0]

        completed_long_balls = self.passes[
            (self.passes["player"] == self.player)
            & (self.passes["pass_length"] >= length)
            & (self.passes["pass_outcome"] == "Complete")
        ].shape[0]

        ratio_long_balls = (
            completed_long_balls / total_long_balls if total_long_balls != 0 else np.NaN
        )

        ret = {
            "total_long_balls": total_long_balls,
            "completed_long_balls": completed_long_balls,
            "ratio_long_balls": ratio_long_balls,
        }

        return ret

    # LINE BREAKING PASSES
    def count_line_breaking_passes(self):
        total_line_breaking_passes = self.passes[
            (self.passes["player"] == self.player)
            & (self.passes["line_breaking_pass"] == True)
        ].shape[0]

        completed_line_breaking_passes = self.passes[
            (self.passes["player"] == self.player)
            & (self.passes["line_breaking_pass"] == True)
            & (self.passes["pass_outcome"] == "Complete")
        ].shape[0]

        ratio_line_breaking_passes = (
            completed_line_breaking_passes / total_line_breaking_passes
            if total_line_breaking_passes != 0
            else np.NaN
        )

        ret = {
            "total_line_breaking_passes": total_line_breaking_passes,
            "completed_line_breaking_passes": completed_line_breaking_passes,
            "ratio_line_breaking_passes": ratio_line_breaking_passes,
        }

        return ret

    # THROUGH BALLS
    def count_through_balls(self):
        total_through_balls = self.passes[
            (self.passes["player"] == self.player)
            & (self.passes["pass_through_ball"] == True)
        ].shape[0]

        completed_through_balls = self.passes[
            (self.passes["player"] == self.player)
            & (self.passes["pass_through_ball"] == True)
            & (self.passes["pass_outcome"] == "Complete")
        ].shape[0]

        ratio_through_balls = (
            completed_through_balls / total_through_balls
            if total_through_balls != 0
            else np.NaN
        )

        ret = {
            "total_through_balls": total_through_balls,
            "completed_through_balls": completed_through_balls,
            "ratio_through_balls": ratio_through_balls,
        }

        return ret

    # CROSSES
    def count_crosses(self):
        total_crosses = self.passes[
            (self.passes["player"] == self.player) & (self.passes["pass_cross"] == True)
        ].shape[0]

        completed_crosses = self.passes[
            (self.passes["player"] == self.player)
            & (self.passes["pass_cross"] == True)
            & (self.passes["pass_outcome"] == "Complete")
        ].shape[0]

        ratio_crosses = (
            completed_crosses / total_crosses if total_crosses != 0 else np.NaN
        )

        ret = {
            "total_crosses": total_crosses,
            "completed_crosses": completed_crosses,
            "ratio_crosses": ratio_crosses,
        }

        return ret

    # OPEN PLAY PASSES INTO BOX
    def count_passes_into_box(self):
        total_passes_into_box = self.passes[
            (self.passes["player"] == self.player)
            & (
                (self.passes["x"] < self.box_dims["x"])
                | (
                    (self.passes["x"] >= self.box_dims["x"])
                    & (self.passes["pass_end_y"] < self.box_dims["y_left"])
                )
                | (
                    (self.passes["x"] >= self.box_dims["x"])
                    & (self.passes["pass_end_y"] > self.box_dims["y_right"])
                )
            )
            & (self.passes["pass_end_x"] >= self.box_dims["x"])
            & (self.passes["pass_end_y"] >= self.box_dims["y_left"])
            & (self.passes["pass_end_y"] <= self.box_dims["y_right"])
            & (~self.passes["pass_type"].isin(self.set_pieces))
        ].shape[0]

        completed_passes_into_box = self.passes[
            (self.passes["player"] == self.player)
            & (
                (self.passes["x"] < self.box_dims["x"])
                | (
                    (self.passes["x"] >= self.box_dims["x"])
                    & (self.passes["pass_end_y"] < self.box_dims["y_left"])
                )
                | (
                    (self.passes["x"] >= self.box_dims["x"])
                    & (self.passes["pass_end_y"] > self.box_dims["y_right"])
                )
            )
            & (self.passes["pass_end_x"] >= self.box_dims["x"])
            & (self.passes["pass_end_y"] >= self.box_dims["y_left"])
            & (self.passes["pass_end_y"] <= self.box_dims["y_right"])
            & (~self.passes["pass_type"].isin(self.set_pieces))
            & (self.passes["pass_outcome"] == "Complete")
        ].shape[0]

        ratio_passes_into_box = (
            completed_passes_into_box / total_passes_into_box
            if total_passes_into_box != 0
            else np.NaN
        )

        ret = {
            "total_passes_into_box": total_passes_into_box,
            "completed_passes_into_box": completed_passes_into_box,
            "ratio_passes_into_box": ratio_passes_into_box,
        }

        return ret

    # OPEN PLAY FINAL THIRD PASSES
    def count_final_third_passes(self):
        total_final_third_passes = self.passes[
            (self.passes["player"] == self.player)
            & (
                (self.passes["x"] >= self.final_third)
                | (self.passes["pass_end_x"] >= self.final_third)
            )
            & (self.passes["pass_end_x"] >= self.final_third)
            & (~self.passes["pass_type"].isin(self.set_pieces))
        ].shape[0]

        completed_final_third_passes = self.passes[
            (self.passes["player"] == self.player)
            & (
                (self.passes["x"] >= self.final_third)
                | (self.passes["pass_end_x"] >= self.final_third)
            )
            & (~self.passes["pass_type"].isin(self.set_pieces))
            & (self.passes["pass_outcome"] == "Complete")
        ].shape[0]

        ratio_final_third_passes = (
            completed_final_third_passes / total_final_third_passes
            if total_final_third_passes != 0
            else np.NaN
        )

        ret = {
            "total_final_third_passes": total_final_third_passes,
            "completed_final_third_passes": completed_final_third_passes,
            "ratio_final_third_passes": ratio_final_third_passes,
        }

        return ret

    # OPEN PLAY PASS ACCURACY (without set pieces - all of them)
    def count_passes(self):
        total_passes = self.passes[
            (self.passes["player"] == self.player)
            & (~self.passes["pass_type"].isin(self.set_pieces))
        ].shape[0]

        completed_passes = self.passes[
            (self.passes["player"] == self.player)
            & (~self.passes["pass_type"].isin(self.set_pieces))
            & (self.passes["pass_outcome"] == "Complete")
        ].shape[0]

        ratio_passes = completed_passes / total_passes if total_passes != 0 else np.NaN

        ret = {
            "total_passes": total_passes,
            "completed_passes": completed_passes,
            "ratio_passes": ratio_passes,
        }

        return ret

    # OBV FROM PASSES, CARRIES & DRIBBLES
    def count_obv(self):
        carry_passes_dribbles = self.player_team_events[
            (self.player_team_events["type"].isin(["Pass", "Dribble", "Carry"]))
            & (self.player_team_events["player"] == self.player)
        ]
        sums = carry_passes_dribbles.groupby("type", dropna=False).sum()[
            "obv_total_net"
        ]
        from_pass = sums["Pass"] if "Pass" in sums else np.NaN
        from_dribble = sums["Dribble"] if "Dribble" in sums else np.NaN
        from_carry = sums["Carry"] if "Carry" in sums else np.NaN

        obv_sum = sum(
            [x for x in [from_pass, from_dribble, from_carry] if x is not np.NaN]
        )

        ret = {
            "passes_obv": from_pass,
            "dribbles_obv": from_dribble,
            "carries_obv": from_carry,
            "sum_obv": obv_sum,
        }
        return ret

    # SCORING CONTRIBUTION
    def count_scoring_contributions(self):

        goals = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["shot_outcome"] == "Goal")
        ].shape[0]

        assists_df = self.player_team_events[
            (self.player_team_events["pass_goal_assist"] == True)
        ]
        player_assists = assists_df[(assists_df["player"] == self.player)].shape[0]

        second_assists_df = pd.DataFrame()
        for index, row in assists_df.iterrows():
            team_name = row["team"]
            assist_index = row["index"]
            goal_scorer = self.player_team_events[
                self.player_team_events["id"] == row["pass_assisted_shot_id"]
            ]["player"].item()
            for i in range(3):
                if assist_index - i - 1 in self.player_team_events["index"].to_list():
                    pos = self.player_team_events[
                        self.player_team_events["index"] == assist_index - i - 1
                    ].iloc[0]
                    if (
                        pos["type"] == "Pass"
                        and pos["team"] == team_name
                        and pos["player"] == self.player
                        and goal_scorer != self.player
                    ):
                        second_assists_df = pd.concat([second_assists_df, pos])
                        break
        second_assists_df = second_assists_df.T
        second_assists = second_assists_df.shape[0]

        ret = {
            "goals": goals,
            "assists": player_assists,
            "second_assists": second_assists,
            "total_goal_contributions": goals + player_assists + second_assists,
        }

        return ret

    # SHOTS CONTRIBUTIONS
    def count_shots_contributions(self):

        shots = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["type"] == "Shot")
            & (self.player_team_events["shot_outcome"] != "Goal")
        ].shape[0]

        key_passes_df = self.player_team_events[
            (self.player_team_events["pass_shot_assist"] == True)
        ]
        player_key_passes = key_passes_df[
            (key_passes_df["player"] == self.player)
        ].shape[0]

        second_assists_to_shot_df = pd.DataFrame()
        for index, row in key_passes_df.iterrows():
            team_name = row["team"]
            key_pass_index = row["index"]
            shot_taker = self.player_team_events[
                self.player_team_events["id"] == row["pass_assisted_shot_id"]
            ]["player"].item()
            for i in range(3):
                if key_pass_index - i - 1 in self.player_team_events["index"].to_list():
                    pos = self.player_team_events[
                        self.player_team_events["index"] == key_pass_index - i - 1
                    ].iloc[0]
                    if (
                        pos["type"] == "Pass"
                        and pos["team"] == team_name
                        and pos["player"] == self.player
                        and shot_taker != self.player
                    ):
                        second_assists_to_shot_df = pd.concat(
                            [second_assists_to_shot_df, pos]
                        )
                        break
        second_assists_to_shot_df = second_assists_to_shot_df.T
        second_assists_to_shot = second_assists_to_shot_df.shape[0]

        ret = {
            "shots": shots,
            "key_passes": player_key_passes,
            "second_assists_to_shots": second_assists_to_shot,
            "total_shots_contributions": shots
            + player_key_passes
            + second_assists_to_shot,
        }
        return ret

    # BLOCKED SHOTS
    def count_blocked_shots(self, df=None, match_events=None):
        if match_events is None:
            match_events = self.player_match_events
        if df is None:
            df = self.player_team_events
        shots_df = match_events[
            (match_events["type"] == "Shot") & (match_events["team"] != self.team_name)
        ]
        blocked_shots_df = shots_df[shots_df["shot_outcome"] == "Blocked"]
        related_events = [
            item
            for sublist in blocked_shots_df["related_events"].to_list()
            for item in sublist
        ]
        blocked_shots = df[
            (df["id"].isin(related_events))
            & (df["type"] == "Block")
            & (df["player"] == self.player)
        ].shape[0]
        ret = {"shots_faced": shots_df.shape[0], "shots_blocked": blocked_shots}

        return ret

    # CLEARANCES
    def count_clearances(self, df=None):
        if df is None:
            df = self.player_team_events
        clearances = df[
            (df["type"] == "Clearance") & (df["player"] == self.player)
        ].shape[0]

        ret = {"clearances": clearances}

        return ret

    # TOUCHES INSIDE BOX
    def count_touches_inside_box(self, df=None):
        if df is None:
            df = self.player_team_events
        touches_inside_box_df = df[
            (df["type"].isin(self.touches))
            & (df["player"] == self.player)
            & (df["x"] >= self.box_dims["x"])
            & (df["y"] >= self.box_dims["y_left"])
            & (df["y"] <= self.box_dims["y_right"])
        ]
        count_touches = (
            touches_inside_box_df.groupby("type").count()["index"].reset_index()
        )
        count_touches["type"] = count_touches["type"].str.lower()
        count_touches["type"] = count_touches["type"].str.replace("*", "")
        count_touches["type"] = count_touches["type"].str.replace(" ", "_")
        count_touches["type"] = count_touches["type"] + "_inside_box"

        ret = count_touches.set_index("type")["index"].to_dict()
        ret["total_touches_inside_box"] = touches_inside_box_df.shape[0]

        return ret

    # DRIBBLES
    def count_dribbles(self):
        total_dribbles = self.player_team_events[
            (self.player_team_events["type"] == "Dribble")
            & (self.player_team_events["player"] == self.player)
        ].shape[0]

        completed_dribbles = self.player_team_events[
            (self.player_team_events["type"] == "Dribble")
            & (self.player_team_events["player"] == self.player)
            & (self.player_team_events["dribble_outcome"] == "Complete")
        ].shape[0]

        ratio_dribbles = (
            completed_dribbles / total_dribbles if total_dribbles != 0 else np.NaN
        )

        ret = {
            "total_dribbles": total_dribbles,
            "completed_dribbles": completed_dribbles,
            "ratio_dribbles": ratio_dribbles,
        }

        return ret

    # SHOTS
    def count_shots_output(self, shots=None):
        if shots is None:
            shots = self.shots
        shots_df = shots[shots["player"] == self.player]

        shots = shots_df.shape[0]
        xg = shots_df["shot_statsbomb_xg"].sum()
        xg_per_shot = xg / shots if shots != 0 else np.NaN

        shots_on_target = shots_df[
            shots_df["shot_outcome"].isin(["Saved", "Goal", "Saved to Post"])
        ].shape[0]
        ratio_shots = shots_on_target / shots if shots != 0 else np.NaN

        goals = shots_df[shots_df["shot_outcome"] == "Goal"].shape[0]
        shot_conversion = goals / shots if shots != 0 else np.NaN

        ret = {
            "shots": shots,
            "shots_on_taget": shots_on_target,
            "ratio_shots": ratio_shots,
            "goals": goals,
            "shot_conversion": shot_conversion,
            "xg": xg,
            "shot_quality": xg_per_shot,
        }

        return ret

    # DEEP PROGRESSIONS
    def count_deep_progressions(self):
        carries_into_final_third = self.carries[
            (self.carries["player"] == self.player)
            & (self.carries["x"] < self.final_third)
            & (self.carries["carry_end_x"] >= self.final_third)
        ].shape[0]
        passes_into_final_third = self.passes[
            (self.passes["player"] == self.player)
            & (self.passes["x"] < self.final_third)
            & (self.passes["pass_end_x"] >= self.final_third)
            & (self.passes["pass_outcome"] == "Complete")
        ].shape[0]

        deep_progressions = carries_into_final_third + passes_into_final_third

        ret = {
            "carries_into_final_third": carries_into_final_third,
            "passes_into_final_third": passes_into_final_third,
            "deep_progressions": deep_progressions,
        }
        return ret

    # xA
    def count_expected_assists(self):
        shots_info = self.shots[["shot_statsbomb_xg", "shot_key_pass_id"]]
        shots_info.columns = ["xg", "id"]
        key_passes = self.player_team_events[
            self.player_team_events["id"].isin(shots_info["id"].to_list())
        ][["id", "player"]]
        xa_df = shots_info.merge(key_passes, on="id")

        xa = xa_df[xa_df["player"] == self.player]["xg"].sum()

        ret = {"xa": xa}

        return ret

    # OFFENSIVE DUELS
    def count_offensive_duels(self):

        dribbles = self.count_dribbles()

        dispossessed = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["type"] == "Dispossessed")
        ].shape[0]

        fouls_won = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["type"] == "Foul Won")
            & (self.player_team_events["foul_won_defensive"].isna())
        ].shape[0]

        fouls_commited = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["type"] == "Foul Committed")
            & (self.player_team_events["foul_committed_offensive"] == True)
        ].shape[0]

        # to w zasadzie nie jest duel TODO: should I count this as a duel?!?!?!
        miscontrols = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["type"] == "Miscontrol")
        ].shape[0]

        turnovers = (
            miscontrols + dribbles["total_dribbles"] - dribbles["completed_dribbles"]
        )

        aerial_lost = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["type"] == "Duel")
            & (self.player_team_events["duel_type"] == "Aerial Lost")
            & (
                self.player_team_events["team"]
                == self.player_team_events["possession_team"]
            )
        ].shape[0]

        passes_aerial_won = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["type"] == "Pass")
            & (self.player_team_events["pass_aerial_won"] == True)
            & (
                self.player_team_events["team"]
                == self.player_team_events["possession_team"]
            )
        ].shape[0]

        shots_aerial_won = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["type"] == "Shot")
            & (self.player_team_events["shot_aerial_won"] == True)
            & (
                self.player_team_events["team"]
                == self.player_team_events["possession_team"]
            )
        ].shape[0]

        miscontrol_aerial_won = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["type"] == "Miscontrol")
            & (self.player_team_events["miscontrol_aerial_won"] == True)
            & (
                self.player_team_events["team"]
                == self.player_team_events["possession_team"]
            )
        ].shape[0]

        total_attacking_aerials = (
            passes_aerial_won + shots_aerial_won + miscontrol_aerial_won + aerial_lost
        )
        ratio_attacking_aerials = (
            (passes_aerial_won + shots_aerial_won + miscontrol_aerial_won)
            / total_attacking_aerials
            if total_attacking_aerials != 0
            else np.NaN
        )

        fifty_fifty_df = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["type"] == "50/50")
            & (
                self.player_team_events["team"]
                == self.player_team_events["possession_team"]
            )
        ].copy()
        fifty_fifty_df["50_50_outcome"] = fifty_fifty_df["50_50"].apply(
            lambda x: x.get("outcome", {}).get("name", None)
        )

        fifty_fifty_total = fifty_fifty_df.shape[0]
        fifty_fifty_won = fifty_fifty_df[
            (fifty_fifty_df["50_50_outcome"].isin(["Won", "Success To Team"]))
        ].shape[0]
        fifty_fifty_ratio = (
            fifty_fifty_won / fifty_fifty_total if fifty_fifty_total != 0 else np.NaN
        )

        errors = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["type"] == "Error")
            & (
                self.player_team_events["team"]
                == self.player_team_events["possession_team"]
            )
        ].shape[0]

        total_ball_recoveries = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (
                (
                    (self.player_team_events["type"] == "Ball Recovery")
                    & (self.player_team_events["ball_recovery_offensive"] == True)
                )
                | (
                    (self.player_team_events["type"] == "Pass")
                    & (self.player_team_events["pass_type"] == "Recovery")
                    & (
                        self.player_team_events["possession_team"]
                        == self.player_team_events["team"]
                    )
                    & (
                        self.player_team_events["team"]
                        == self.player_team_events["possession_team"].shift(1)
                    )
                )
            )
        ].shape[0]

        lost_ball_recoveries = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (
                (
                    (self.player_team_events["type"] == "Ball Recovery")
                    & (self.player_team_events["ball_recovery_offensive"].isna())
                    & (
                        self.player_team_events["ball_recovery_recovery_failure"]
                        == True
                    )
                )
                | (
                    (self.player_team_events["type"] == "Pass")
                    & (self.player_team_events["pass_type"] == "Recovery")
                    & (self.player_team_events["pass_outcome"] != "Complete")
                    & (
                        self.player_team_events["possession_team"]
                        == self.player_team_events["team"]
                    )
                    & (
                        self.player_team_events["team"]
                        == self.player_team_events["possession_team"].shift(1)
                    )
                )
            )
        ].shape[0]

        bal_recoveries_ratio = (
            (total_ball_recoveries - lost_ball_recoveries) / total_ball_recoveries
            if total_ball_recoveries != 0
            else np.NaN
        )

        attacking_duels_won = (
            dribbles["completed_dribbles"]
            + fouls_won
            + passes_aerial_won
            + shots_aerial_won
            + miscontrol_aerial_won
            + fifty_fifty_won
        )
        attacking_duels_lost = (
            dispossessed
            + fouls_commited
            + (turnovers - miscontrols)
            + aerial_lost
            + (fifty_fifty_total - fifty_fifty_won)
        )
        total_attacking_duels = attacking_duels_won + attacking_duels_lost
        ratio_attacking_duels = (
            attacking_duels_won / total_attacking_duels
            if total_attacking_duels != 0
            else np.NaN
        )

        ret = dribbles | {
            "dispossessed": dispossessed,
            "miscontrols": miscontrols,
            "turnovers": turnovers,
            "attacking_errors": errors,
            "total_attacking_ball_recoveries": total_ball_recoveries,
            "won_attacking_ball_recoveries": total_ball_recoveries
            - lost_ball_recoveries,
            "ratio_attacking_ball_recoveries": bal_recoveries_ratio,
            "attacking_fouls_won": fouls_won,
            "attacking_fouls_commited": fouls_commited,
            "total_attacking_aerials": total_attacking_aerials,
            "won_attacking_aerials": passes_aerial_won
            + shots_aerial_won
            + miscontrol_aerial_won,
            "ratio_attacking_aerials": ratio_attacking_aerials,
            "total_attacking_50_50": fifty_fifty_total,
            "won_attacking_50_50": fifty_fifty_won,
            "ratio_attacking_50_50": fifty_fifty_ratio,
            "total_attacking_duels": total_attacking_duels,
            "won_attacking_duels": attacking_duels_won,
            "ratio_attacking_duels": ratio_attacking_duels,
        }

        return ret

    # TOUCHES TO SHOTS
    def count_touches_to_shots(self):
        shots = self.count_shots_output()["shots"]
        touches_inside_box = self.count_touches_inside_box()["total_touches_inside_box"]

        ratio_touches_inside_box_to_shots = (
            touches_inside_box / shots if shots != 0 else np.NaN
        )

        ret = {
            "total_touches_inside_box": touches_inside_box,
            "shots": shots,
            "ratio_touches_inside_box_to_shots": ratio_touches_inside_box_to_shots,
        }

        return ret

    # xGChain AND xGBuildup
    def count_xg_buildup_metrics(self):
        shots_data_df = self.shots[
            ["index", "player", "shot_statsbomb_xg", "possession"]
        ]

        xg_chain = 0
        xg_buildup = 0

        for shot in shots_data_df.to_dict(orient="records"):
            shots_index = shot["index"]
            possession_data = self.player_team_events[
                (self.player_team_events["possession"] == shot["possession"])
                & (self.player_team_events["index"] <= shots_index)
            ]
            if self.player in possession_data["player"].to_list():
                xg_chain += shot["shot_statsbomb_xg"]

            buildup_data = possession_data[
                (possession_data["index"] != shots_index)  # exlude THE shot
                | (
                    (possession_data["type"] == "Pass")
                    & (possession_data["pass_shot_assist"].isna())
                    & (possession_data["pass_goal_assist"].isna())
                )
            ]
            if (
                self.player != shot["player"]
                and self.player in buildup_data["player"].to_list()
            ):
                xg_buildup += shot["shot_statsbomb_xg"]
            elif (
                self.player == shot["player"]
                and self.player
                in buildup_data[buildup_data["index"] < shots_index - 3][
                    "player"
                ].to_list()
            ):
                xg_buildup += shot["shot_statsbomb_xg"]

        ret = {
            "xg_chain": xg_chain,
            "xg_buildup": xg_buildup,
        }

        return ret

    def _count_pressure_regains(self, time_to_end=6):
        regains_df = self.player_match_events.copy()
        regains_df = regains_df.sort_values("index", ascending=True)
        regains_df["next_pos_team"] = regains_df["possession_team"].shift(-1)
        regains_df["next_pos_team"] = regains_df.groupby(["possession", "match_id"])[
            "next_pos_team"
        ].transform("last")

        # Convert timestamp columns to datetime format
        regains_df["timestamp"] = pd.to_timedelta(regains_df["timestamp"])
        regains_df["possession_end_time"] = pd.to_timedelta(
            regains_df.groupby(["possession", "match_id"])["timestamp"].transform("max")
        )

        # Calculate TimeToPossEnd for each event
        regains_df["time_to_possession_end"] = (
            regains_df["possession_end_time"] - regains_df["timestamp"]
        ).dt.total_seconds()

        # Now apply the pressure regain condition using the calculated TimeToPossEnd
        regains_df["pressure_regain"] = regains_df.apply(
            lambda row: (
                True
                if row["type"] == "Pressure"
                and row["time_to_possession_end"] < time_to_end
                and row["team"] == row["next_pos_team"]
                else None
            ),
            axis=1,
        )
        regains_df = regains_df[
            (regains_df["play_pattern"] != "Other")
            & (regains_df["pressure_regain"] == True)
        ]
        return regains_df

    # PRESSURES
    def count_pressures(self):
        pressures_df = self.player_team_events[
            (self.player_team_events["type"] == "Pressure")
            & (self.player_team_events["player"] == self.player)
        ]
        pressures = pressures_df.shape[0]
        avg_pressure_duration = pressures_df["duration"].mean()

        counterpressures = pressures_df[pressures_df["counterpress"] == True].shape[0]
        avg_counterpressure_duration = pressures_df[
            pressures_df["counterpress"] == True
        ]["duration"].mean()

        pressure_regains_df = self._count_pressure_regains()
        pressure_regains = pressure_regains_df[
            pressure_regains_df["player"] == self.player
        ].shape[0]
        counterpressure_regains = pressure_regains_df[
            (pressure_regains_df["player"] == self.player)
            & (pressure_regains_df["counterpress"] == True)
        ].shape[0]

        ratio_pressures = pressure_regains / pressures if pressures != 0 else np.NaN
        ratio_counterpressures = (
            counterpressures / counterpressure_regains
            if counterpressure_regains != 0
            else np.NaN
        )

        pressures_final_third_df = pressures_df[pressures_df["x"] >= self.final_third]
        pressures_final_third = pressures_final_third_df.shape[0]
        counterpressures_final_third = pressures_final_third_df[
            pressures_final_third_df["counterpress"] == True
        ].shape[0]
        pressures_oppostion_half_df = pressures_df[
            pressures_df["x"] >= self.oppostion_half
        ]
        pressures_oppostion_half = pressures_oppostion_half_df.shape[0]
        counterpressures_oppostion_half = pressures_oppostion_half_df[
            pressures_oppostion_half_df["counterpress"] == True
        ].shape[0]

        ret = {
            "pressures": pressures,
            "pressures_oppostion_half": pressures_oppostion_half,
            "pressures_final_third": pressures_final_third,
            "avg_pressure_duration": avg_pressure_duration,
            "pressure_regains": pressure_regains,
            "ratio_pressures": ratio_pressures,
            "counterpressures": counterpressures,
            "counterpressures_oppostion_half": counterpressures_oppostion_half,
            "counterpressures_final_third": counterpressures_final_third,
            "avg_counterpressure_duration": avg_counterpressure_duration,
            "counterpressure_regains": counterpressure_regains,
            "ratio_counterpressures": ratio_counterpressures,
        }

        return ret

    # DEFENSIVE DUELS
    def count_defensive_duels(self):

        fouls_won = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["type"] == "Foul Won")
            & (self.player_team_events["foul_won_defensive"] == True)
        ].shape[0]

        fouls_commited = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["type"] == "Foul Committed")
            & (self.player_team_events["foul_committed_offensive"].isna())
        ].shape[0]

        aerial_lost = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["type"] == "Duel")
            & (self.player_team_events["duel_type"] == "Aerial Lost")
            & (
                self.player_team_events["team"]
                != self.player_team_events["possession_team"]
            )
        ].shape[0]

        passes_aerial_won = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["type"] == "Pass")
            & (self.player_team_events["pass_aerial_won"] == True)
            & (
                self.player_team_events["team"]
                != self.player_team_events["possession_team"]
            )
        ].shape[0]

        clearance_aerial_won = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["type"] == "Clearance")
            & (self.player_team_events["clearance_aerial_won"] == True)
            & (
                self.player_team_events["team"]
                != self.player_team_events["possession_team"]
            )
        ].shape[0]

        miscontrol_aerial_won = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["type"] == "Miscontrol")
            & (self.player_team_events["miscontrol_aerial_won"] == True)
            & (
                self.player_team_events["team"]
                != self.player_team_events["possession_team"]
            )
        ].shape[
            0
        ]  # ---> TODO: TU CHYBA NIE - dodac brakujace

        total_defensive_aerials = (
            passes_aerial_won
            + clearance_aerial_won
            + miscontrol_aerial_won
            + aerial_lost
        )
        ratio_defensive_aerials = (
            (passes_aerial_won + clearance_aerial_won + miscontrol_aerial_won)
            / total_defensive_aerials
            if total_defensive_aerials != 0
            else np.NaN
        )

        clearances_on_the_ground = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["type"] == "Clearance")
            & (self.player_team_events["clearance_aerial_won"].isna())
            & (
                self.player_team_events["team"]
                != self.player_team_events["possession_team"]
            )
        ].shape[0]

        total_clearances = clearances_on_the_ground + clearance_aerial_won

        fifty_fifty_df = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["type"] == "50/50")
            & (
                self.player_team_events["team"]
                != self.player_team_events["possession_team"]
            )
        ].copy()
        fifty_fifty_df["50_50_outcome"] = fifty_fifty_df["50_50"].apply(
            lambda x: x.get("outcome", {}).get("name", None)
        )

        fifty_fifty_total = fifty_fifty_df.shape[0]
        fifty_fifty_won = fifty_fifty_df[
            (fifty_fifty_df["50_50_outcome"].isin(["Won", "Success To Team"]))
        ].shape[0]
        fifty_fifty_ratio = (
            fifty_fifty_won / fifty_fifty_total if fifty_fifty_total != 0 else np.NaN
        )

        dribbled_past = self.player_team_events[
            (self.player_team_events["type"] == "Dribbled Past")
            & (self.player_team_events["player"] == self.player)
        ].shape[0]

        errors = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["type"] == "Error")
            & (
                self.player_team_events["team"]
                != self.player_team_events["possession_team"]
            )
        ].shape[0]

        total_interceptions = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["type"] == "Interception")
        ].shape[0]

        interceptions_won = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["type"] == "Interception")
            & (
                self.player_team_events["interception_outcome"].isin(
                    ["Success", "Success In Play", "Success Out", "Won"]
                )
            )
        ].shape[0]

        interceptions_ratio = (
            interceptions_won / total_interceptions
            if total_interceptions != 0
            else np.NaN
        )

        total_tackles = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["type"] == "Duel")
            & (self.player_team_events["duel_type"] == "Tackle")
        ].shape[0]

        tackles_won = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["type"] == "Duel")
            & (self.player_team_events["duel_type"] == "Tackle")
            & (
                self.player_team_events["duel_outcome"].isin(
                    ["Success", "Success In Play", "Success Out", "Won"]
                )
            )
        ].shape[0]

        tackles_ratio = tackles_won / total_tackles if total_tackles != 0 else np.NaN

        total_ball_recoveries = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (
                (
                    (self.player_team_events["type"] == "Ball Recovery")
                    & (self.player_team_events["ball_recovery_offensive"].isna())
                )
                | (
                    (self.player_team_events["type"] == "Pass")
                    & (self.player_team_events["pass_type"] == "Recovery")
                    & (
                        self.player_team_events["possession_team"]
                        != self.player_team_events["team"]
                    )
                )
                | (
                    (self.player_team_events["type"] == "Pass")
                    & (self.player_team_events["pass_type"] == "Recovery")
                    & (
                        self.player_team_events["possession_team"]
                        == self.player_team_events["team"]
                    )
                    & (
                        self.player_team_events["team"]
                        != self.player_team_events["possession_team"].shift(1)
                    )
                )
            )
        ].shape[0]

        lost_ball_recoveries = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (
                (
                    (self.player_team_events["type"] == "Ball Recovery")
                    & (self.player_team_events["ball_recovery_offensive"].isna())
                    & (
                        self.player_team_events["ball_recovery_recovery_failure"]
                        == True
                    )
                )
                | (
                    (self.player_team_events["type"] == "Pass")
                    & (self.player_team_events["pass_type"] == "Recovery")
                    & (self.player_team_events["pass_outcome"] != "Complete")
                    & (
                        self.player_team_events["possession_team"]
                        != self.player_team_events["team"]
                    )
                )
                | (
                    (self.player_team_events["type"] == "Pass")
                    & (self.player_team_events["pass_type"] == "Recovery")
                    & (self.player_team_events["pass_outcome"] != "Complete")
                    & (
                        self.player_team_events["possession_team"]
                        == self.player_team_events["team"]
                    )
                    & (
                        self.player_team_events["team"]
                        != self.player_team_events["possession_team"].shift(1)
                    )
                )
            )
        ].shape[0]

        ball_recoveries_ratio = (
            (total_ball_recoveries - lost_ball_recoveries) / total_ball_recoveries
            if total_ball_recoveries != 0
            else np.NaN
        )
        # TODO: NOT DOUBLING AERIAL (for example in tackles)

        tackles_dribbled_past = (
            total_tackles / dribbled_past if dribbled_past != 0 else np.NaN
        )

        defensive_duels_won = (
            fouls_won
            + clearance_aerial_won
            + passes_aerial_won
            + miscontrol_aerial_won
            + fifty_fifty_won
            + tackles_won
        )
        defensive_duels_lost = (
            fouls_commited
            + aerial_lost
            + (fifty_fifty_total - fifty_fifty_won)
            + (total_tackles - tackles_won)
            + dribbled_past
        )
        total_defensive_duels = defensive_duels_won + defensive_duels_lost
        ratio_defensive_duels = (
            defensive_duels_won / total_defensive_duels
            if total_defensive_duels != 0
            else np.NaN
        )

        ret = {
            "defensive_fouls_won": fouls_won,
            "defensive_fouls_commited": fouls_commited,
            "defensive_errors": errors,
            "total_defensive_aerials": total_defensive_aerials,
            "won_defensive_aerials": passes_aerial_won
            + clearance_aerial_won
            + miscontrol_aerial_won,
            "ratio_defensive_aerials": ratio_defensive_aerials,
            "total_defensive_50_50": fifty_fifty_total,
            "won_defensive_50_50": fifty_fifty_won,
            "ratio_defensive_50_50": fifty_fifty_ratio,
            "total_interceptions": total_interceptions,
            "interceptions_won": interceptions_won,
            "interceptions_ratio": interceptions_ratio,
            "total_tackles": total_tackles,
            "tackles_won": tackles_won,
            "tackles_ratio": tackles_ratio,
            "clearances": total_clearances,
            "dribbled_past": dribbled_past,
            "ratio_tackles_dribbled_past": tackles_dribbled_past,
            "total_defensive_ball_recoveries": total_ball_recoveries,
            "won_defensive_ball_recoveries": total_ball_recoveries
            - lost_ball_recoveries,
            "ratio_defensive_ball_recoveries": ball_recoveries_ratio,
            "total_defensive_duels": total_defensive_duels,
            "won_defensive_duels": defensive_duels_won,
            "ratio_defensive_duels": ratio_defensive_duels,
        }
        return ret

    # BALL RECEPTIONS
    def count_ball_receptions(self):
        ball_reception_df = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["type"] == "Ball Receipt*")
        ]
        total_ball_receptions = ball_reception_df.shape[0]
        successful_ball_receptions = ball_reception_df[
            ball_reception_df["ball_receipt_outcome"].isna()
        ].shape[0]
        ball_receptions_ratio = (
            successful_ball_receptions / total_ball_receptions
            if total_ball_receptions != 0
            else np.NaN
        )

        total_ball_receptions_under_pressure = ball_reception_df[
            ball_reception_df["under_pressure"] == True
        ].shape[0]
        successful_ball_receptions_under_pressure = ball_reception_df[
            (ball_reception_df["ball_receipt_outcome"].isna())
            & (ball_reception_df["under_pressure"] == True)
        ].shape[0]
        ball_receptions_under_pressure_ratio = (
            successful_ball_receptions_under_pressure
            / total_ball_receptions_under_pressure
            if total_ball_receptions_under_pressure != 0
            else np.NaN
        )
        pressure_of_ball_receptions_ratio = (
            total_ball_receptions_under_pressure / total_ball_receptions
            if total_ball_receptions != 0
            else np.NaN
        )

        total_ball_receptions_in_the_box = ball_reception_df[
            (ball_reception_df["x"] >= self.box_dims["x"])
            & (ball_reception_df["y"] >= self.box_dims["y_left"])
            & (ball_reception_df["y"] <= self.box_dims["y_right"])
        ].shape[0]
        successful_ball_receptions_in_the_box = ball_reception_df[
            (ball_reception_df["ball_receipt_outcome"].isna())
            & (ball_reception_df["x"] >= self.box_dims["x"])
            & (ball_reception_df["y"] >= self.box_dims["y_left"])
            & (ball_reception_df["y"] <= self.box_dims["y_right"])
        ].shape[0]
        ball_receptions_in_the_box_ratio = (
            successful_ball_receptions_in_the_box / total_ball_receptions_in_the_box
            if total_ball_receptions_in_the_box != 0
            else np.NaN
        )
        box_ball_receptions_ratio = (
            total_ball_receptions_in_the_box / total_ball_receptions
            if total_ball_receptions != 0
            else np.NaN
        )

        ret = {
            "total_ball_receptions": total_ball_receptions,
            "successful_ball_receptions": successful_ball_receptions,
            "ball_receptions_ratio": ball_receptions_ratio,
            "total_ball_receptions_under_pressure": total_ball_receptions_under_pressure,
            "successful_ball_receptions_under_pressure": successful_ball_receptions_under_pressure,
            "ball_receptions_under_pressure_ratio": ball_receptions_under_pressure_ratio,
            "pressured_ball_receptions_ratio": pressure_of_ball_receptions_ratio,
            "total_ball_receptions_in_the_box": total_ball_receptions_in_the_box,
            "successful_ball_receptions_in_the_box": successful_ball_receptions_in_the_box,
            "ball_receptions_in_the_box_ratio": ball_receptions_in_the_box_ratio,
            "box_ball_receptions_ratio": box_ball_receptions_ratio,
        }

        return ret

    def aggregate_player_statistics(self) -> pd.DataFrame:
        """
        Aggregates all statistics for the given player.

        Args:
            player (str): Player name for whom to calculate statistics.

        Returns:
            pd.DataFrame: DataFrame with all aggregated statistics.
        """
        stats_functions = [
            self.count_passes_under_pressure,
            self.count_progressive_passes,
            self.count_long_balls,
            self.count_line_breaking_passes,
            self.count_crosses,
            self.count_through_balls,
            self.count_passes,
            self.count_obv,
            self.count_scoring_contributions,
            self.count_shots_contributions,
            self.count_blocked_shots,
            self.count_clearances,
            self.count_touches_inside_box,
            self.count_dribbles,
            self.count_passes_into_box,
            self.count_final_third_passes,
            self.count_shots_output,
            self.count_deep_progressions,
            self.count_expected_assists,
            self.count_offensive_duels,
            self.count_touches_to_shots,
            self.count_xg_buildup_metrics,
            self.count_pressures,
            self.count_defensive_duels,
            self.count_ball_receptions,
            self.count_set_piece_clearances,
            self.count_set_piece_blocked_shots,
            self.count_set_piece_shots_output,
            self.count_set_piece_touches_inside_box,
            self.count_aggressive_actions,
            self.count_defending_dribbles,
            self.count_defensive_actions_regains,
        ]
        results = {
            key: value for func in stats_functions for key, value in func().items()
        }
        results["minutes_played"] = self.player_minutes_info[
            "played_time_minutes_decimal"
        ]
        ret = pd.DataFrame([results]).T
        # ret.columns = [player]
        ret = ret.round(2).T
        ret["player"] = self.player
        ret["match_id"] = self.match_id
        ret = ret[
            ["match_id", "player", "minutes_played"]
            + [
                col
                for col in ret.columns
                if col not in ["match_id", "player", "minutes_played"]
            ]
        ]
        return ret

    def _build_set_pieces_dataframe(self, team, time=15, x_coord=None):
        if x_coord is None:
            x_coord = self.final_third
        match_events = self.player_match_events.copy()
        match_events["timestamp"] = pd.to_timedelta(match_events["timestamp"])
        if team == "for":
            condition = self.player_match_events["team"] == self.team_name
        elif team == "against":
            condition = self.player_match_events["team"] != self.team_name
        else:
            condition = (
                self.player_match_events["team"] == self.player_match_events["team"]
            )

        set_pieces = self.player_match_events[
            (self.player_match_events["type"] == "Pass")
            & (self.player_match_events["pass_type"].isin(self.set_pieces))
            & (self.player_match_events["x"] >= x_coord)
            & condition
        ].copy()
        set_pieces["timestamp"] = pd.to_timedelta(set_pieces["timestamp"])
        set_pieces_df = pd.DataFrame()
        for set_piece in set_pieces.to_dict(orient="records"):
            sp_index = set_piece["index"]
            sp_timestamp = set_piece["timestamp"]
            sp_period = set_piece["period"]
            sp_possession_team = set_piece["possession_team"]

            sp_df = match_events[
                (match_events["index"] >= sp_index)
                & (match_events["period"] == sp_period)
                & (
                    (match_events["timestamp"] - sp_timestamp).dt.total_seconds()
                    <= time
                )
                & (match_events["possession_team"] == sp_possession_team)
            ]

            set_pieces_df = pd.concat([set_pieces_df, sp_df])

        return set_pieces_df

    def count_set_piece_clearances(self, time=15, x_coord=None):
        sp_df = self._build_set_pieces_dataframe("against", time, x_coord)
        if sp_df.empty:
            clearences = {"set_piece_" + k: 0 for k in self.count_clearances().keys()}
        else:
            clearences = self.count_clearances(df=sp_df)
            clearences = {"set_piece_" + k: v for k, v in clearences.items()}
        return clearences

    def count_set_piece_blocked_shots(self, time=15, x_coord=None):
        sp_match_events = self._build_set_pieces_dataframe("full", time, x_coord)
        sp_df = self._build_set_pieces_dataframe("against", time, x_coord)
        if sp_df.empty:
            blocked_shots = {
                "set_piece_" + k: 0 for k in self.count_blocked_shots().keys()
            }
        else:
            blocked_shots = self.count_blocked_shots(
                match_events=sp_match_events, df=sp_df
            )
            blocked_shots = {"set_piece_" + k: v for k, v in blocked_shots.items()}
        return blocked_shots

    def count_set_piece_shots_output(self, time=15, x_coord=None):
        sp_df = self._build_set_pieces_dataframe("for", time, x_coord)
        if sp_df.empty:
            set_piece_shots = {
                "set_piece_" + k: 0 for k in self.count_shots_output().keys()
            }
            set_piece_shots["set_pieces"] = 0
            set_piece_shots["shots_set_piece_ratio"] = np.NaN
        else:
            set_pieces = sp_df[sp_df["pass_type"].isin(self.set_pieces)].shape[0]
            sp_shots = sp_df[sp_df["type"] == "Shot"]
            set_piece_shots = self.count_shots_output(shots=sp_shots)
            set_piece_shots = {"set_piece_" + k: v for k, v in set_piece_shots.items()}
            shots_set_piece_ratio = (
                set_pieces / set_piece_shots["set_piece_shots"]
                if set_piece_shots["set_piece_shots"] != 0
                else np.NaN
            )
            set_piece_shots["set_pieces"] = set_pieces
            set_piece_shots["shots_set_piece_ratio"] = shots_set_piece_ratio
        return set_piece_shots

    def count_set_piece_touches_inside_box(self, time=15, x_coord=None):
        sp_df = self._build_set_pieces_dataframe("for", time, x_coord)
        if sp_df.empty:
            touches_inside_box = {
                "set_piece_" + k: 0 for k in self.count_touches_inside_box().keys()
            }
            touches_inside_box["set_pieces"] = 0
            touches_inside_box["touches_inside_box_set_piece_ratio"] = np.NaN
        else:
            set_pieces = sp_df[sp_df["pass_type"].isin(self.set_pieces)].shape[0]
            touches_inside_box = self.count_touches_inside_box(df=sp_df)
            touches_inside_box = {
                "set_piece_" + k: v for k, v in touches_inside_box.items()
            }
            touches_inside_box_set_piece_ratio = (
                set_pieces / touches_inside_box["set_piece_total_touches_inside_box"]
                if touches_inside_box["set_piece_total_touches_inside_box"] != 0
                else np.NaN
            )
            touches_inside_box["set_pieces"] = set_pieces
            touches_inside_box["touches_inside_box_set_piece_ratio"] = (
                touches_inside_box_set_piece_ratio
            )
        return touches_inside_box

    def count_aggressive_actions(self, time=2.0):
        opponents_ball_receipts = self.player_match_events[
            (self.player_match_events["team"] != self.team_name)
            & (self.player_match_events["type"] == "Ball Receipt*")
        ].copy()
        opponents_ball_receipts["timestamp"] = pd.to_timedelta(
            opponents_ball_receipts["timestamp"]
        )
        team_events = self.player_team_events.copy()
        team_events["timestamp"] = pd.to_timedelta(team_events["timestamp"])
        player_actions_after = pd.DataFrame()
        for ball in opponents_ball_receipts.to_dict(orient="records"):
            receipt_timestamp = ball["timestamp"]
            index = ball["index"]
            period = ball["period"]
            events_in_time_interval = team_events[
                (team_events["player"] == self.player)
                & (team_events["index"] >= index)
                & (team_events["period"] == period)
                & (
                    (team_events["timestamp"] - receipt_timestamp).dt.total_seconds()
                    <= time
                )
            ]
            player_actions_after = pd.concat(
                [player_actions_after, events_in_time_interval]
            )
        player_actions_after = player_actions_after.drop_duplicates(subset=["id"])
        aggressive_actions_df = player_actions_after[
            (player_actions_after["type"].isin(["Pressure", "Foul Committed"]))
            | (
                (player_actions_after["type"] == "Duel")
                & (player_actions_after["duel_type"] == "Tackle")
            )
        ]
        aggressive_actions = aggressive_actions_df.groupby(
            "type", dropna=False
        ).count()["index"]
        pressures = (
            aggressive_actions["Pressure"] if "Pressure" in aggressive_actions else 0
        )
        fouls = (
            aggressive_actions["Foul Committed"]
            if "Foul Committed" in aggressive_actions
            else 0
        )
        tackles = aggressive_actions["Duel"] if "Duel" in aggressive_actions else 0

        aggressive_actions_sum = aggressive_actions_df.shape[0]

        ret = {
            "aggressive_actions_pressures": pressures,
            "aggressive_actions_fouls": fouls,
            "aggressive_actions_tackles": tackles,
            "total_aggressive_actions": aggressive_actions_sum,
        }

        return ret

    def count_defending_dribbles(self):
        opponents_dribbles = self.player_match_events[
            (self.player_match_events["team"] != self.team_name)
            & (self.player_match_events["type"] == "Dribble")
        ]
        dribbles_faced = 0
        dribbled_past = 0
        dribble_stopped_ball_won = 0
        dribble_stopped_ball_lost = 0

        for dribble in opponents_dribbles.to_dict(orient="records"):
            dribble_index = dribble["index"]
            if dribble["dribble_outcome"] == "Complete":
                dribble_past_row = self.player_match_events[
                    self.player_match_events["index"] == dribble_index - 1
                ]
                if (dribble_past_row["player"].item() == self.player) & (
                    dribble_past_row["type"].item() == "Dribbled Past"
                ):
                    dribbles_faced += 1
                    dribbled_past += 1

            elif dribble["dribble_outcome"] == "Incomplete":
                dribble_stopped = self.player_match_events[
                    self.player_match_events["index"] == dribble_index + 1
                ]
                if (dribble_stopped["player"].item() == self.player) & (
                    dribble_stopped["type"].item() == "Duel"
                ):
                    dribbles_faced += 1
                    if dribble_stopped["duel_outcome"].item() in [
                        "Won",
                        "Success",
                        "Success In Play",
                        "Success Out",
                    ]:
                        dribble_stopped_ball_won += 1
                    else:
                        dribble_stopped_ball_lost += 1

        ratio_dribbles_successfully_defended = (
            dribble_stopped_ball_won / dribbles_faced if dribbles_faced != 0 else np.NaN
        )

        ret = {
            "dribbles_faced": dribbles_faced,
            "dribbled_past": dribbled_past,
            "dribble_stopped_ball_won": dribble_stopped_ball_won,
            "dribble_stopped_ball_lost": dribble_stopped_ball_lost,
            "ratio_dribbles_successfully_defended": ratio_dribbles_successfully_defended,
        }

        return ret

    def count_defensive_actions_regains(self, time_to_end=6.0):
        regains_df = self.player_match_events.copy()
        regains_df = regains_df.sort_values("index", ascending=True)
        regains_df["next_pos_team"] = regains_df["possession_team"].shift(-1)
        regains_df["next_pos_team"] = regains_df.groupby(["possession", "match_id"])[
            "next_pos_team"
        ].transform("last")

        # Convert timestamp columns to datetime format
        regains_df["timestamp"] = pd.to_timedelta(regains_df["timestamp"])
        regains_df["possession_end_time"] = pd.to_timedelta(
            regains_df.groupby(["possession", "match_id"])["timestamp"].transform("max")
        )

        # Calculate TimeToPossEnd for each event
        regains_df["time_to_possession_end"] = (
            regains_df["possession_end_time"] - regains_df["timestamp"]
        ).dt.total_seconds()

        # Now apply the pressure regain condition using the calculated TimeToPossEnd
        regains_df["regain"] = regains_df.apply(
            lambda row: (
                True
                if (
                    (
                        row["type"]
                        in (["Pressure", "Interception", "Dribbled Past", "Block"])
                    )
                    | (row["duel_type"] == "Tackle")
                )
                and row["time_to_possession_end"] < time_to_end
                and row["team"] == row["next_pos_team"]
                else None
            ),
            axis=1,
        )
        regains_df = regains_df[
            (regains_df["player"] == self.player)
            & (regains_df["regain"] == True)
            & (regains_df["play_pattern"] != "Other")
        ]

        defensive_actions_regains = regains_df.groupby("type", dropna=False).count()[
            "index"
        ]
        pressures = (
            defensive_actions_regains["Pressure"]
            if "Pressure" in defensive_actions_regains
            else 0
        )
        interceptions = (
            defensive_actions_regains["Interception"]
            if "Interception" in defensive_actions_regains
            else 0
        )
        blocks = (
            defensive_actions_regains["Block"]
            if "Block" in defensive_actions_regains
            else 0
        )
        tackles = (
            defensive_actions_regains["Duel"]
            if "Duel" in defensive_actions_regains
            else 0
        )
        dribbled_past = (
            defensive_actions_regains["Dribbled Past"]
            if "Dribbled Past" in defensive_actions_regains
            else 0
        )

        total_defensive_actions_regains = regains_df.shape[0]

        ret = {
            "defensive_actions_regains_pressures": pressures,
            "defensive_actions_regains_interceptions": interceptions,
            "defensive_actions_regains_blocks": blocks,
            "defensive_actions_regains_tackles": tackles,
            "defensive_actions_regains_dribbled_past": dribbled_past,
            "total_defensive_actions_regains": total_defensive_actions_regains,
        }

        return ret

    @staticmethod
    def _count_gk_pass_length_accuracy(df, short_max=15.0, long_min=35.0):
        # Classify each pass length
        df = df.copy()
        df["length_type"] = pd.cut(
            df["pass_length"],
            bins=[-float("inf"), short_max, long_min, float("inf")],
            labels=["short", "medium", "long"],
        )

        # Group by length_type and pass_outcome and count occurrences
        grouped = (
            df.groupby(["length_type", "pass_outcome"])["index"]
            .count()
            .unstack(fill_value=0)
        )
        grouped = grouped.reindex(columns=["Complete", "Incomplete"], fill_value=0)

        # Calculate the completion ratio for each length_type
        grouped["ratio"] = grouped.apply(
            lambda row: (
                row.get("Complete", 0)
                / (row.get("Complete", 0) + row.get("Incomplete", 0))
                if (row.get("Complete", 0) + row.get("Incomplete", 0)) > 0
                else np.NaN
            ),
            axis=1,
        )
        # Create a one-level dictionary with the desired keys
        result = {}
        for length_type in grouped.index:
            result[f"{length_type}_complete"] = grouped.at[length_type, "Complete"]
            result[f"{length_type}_incomplete"] = grouped.at[length_type, "Incomplete"]
            result[f"{length_type}_ratio"] = grouped.at[length_type, "ratio"]

        # Calculate totals
        total_complete = grouped["Complete"].sum()
        total_incomplete = grouped["Incomplete"].sum()
        total_ratio = (
            total_complete / (total_complete + total_incomplete)
            if (total_complete + total_incomplete) > 0
            else np.NaN
        )

        # Add totals to the result dictionary
        result["total_complete"] = total_complete
        result["total_incomplete"] = total_incomplete
        result["total_ratio"] = total_ratio

        return result

    @staticmethod
    def _count_gk_under_pressure_accuracy(df):
        gk_df = df.copy()

        # Create a new column for pressure classification
        gk_df["pressure"] = gk_df.apply(
            lambda row: (
                "under_pressure"
                if row["under_pressure"] == True
                else "without_pressure"
            ),
            axis=1,
        )

        # Group by pressure type and pass outcome, counting occurrences
        grouped = (
            gk_df.groupby(["pressure", "pass_outcome"], dropna=False)["index"]
            .count()
            .unstack(fill_value=0)
        )
        pass_length = gk_df.groupby(["pressure"], dropna=False)["pass_length"].mean()

        under_pressure_avg_length = (
            pass_length["under_pressure"] if "under_pressure" in pass_length else np.NaN
        )
        without_pressure_avg_length = (
            pass_length["without_pressure"]
            if "without_pressure" in pass_length
            else np.NaN
        )
        diff_in_avg_length = under_pressure_avg_length - without_pressure_avg_length

        # Ensure both outcomes are present
        grouped = grouped.reindex(columns=["Complete", "Incomplete"], fill_value=0)
        # Calculate the completion ratio for each pressure type
        grouped["ratio"] = grouped.apply(
            lambda row: (
                row.get("Complete", 0)
                / (row.get("Complete", 0) + row.get("Incomplete", 0))
                if (row.get("Complete", 0) + row.get("Incomplete", 0)) > 0
                else np.NaN
            ),
            axis=1,
        )
        # Initialize result dictionary with default values
        result = {
            "under_pressure_complete": 0.0,
            "under_pressure_incomplete": 0.0,
            "under_pressure_ratio": np.NaN,
            "without_pressure_complete": 0.0,
            "without_pressure_incomplete": 0.0,
            "without_pressure_ratio": np.NaN,
        }

        # Fill result dictionary with values from grouped DataFrame
        for index, row in grouped.iterrows():
            result[f"{index}_complete"] = row["Complete"]
            result[f"{index}_incomplete"] = row["Incomplete"]
            result[f"{index}_ratio"] = row["ratio"]

        # Calculate the pressured_ratio
        total_under_pressure = (
            result["under_pressure_complete"] + result["under_pressure_incomplete"]
        )
        total_without_pressure = (
            result["without_pressure_complete"] + result["without_pressure_incomplete"]
        )

        pressured_ratio = (
            total_under_pressure / (total_under_pressure + total_without_pressure)
            if (total_under_pressure + total_without_pressure) != 0
            else np.NaN
        )
        result["pressured_ratio"] = pressured_ratio

        result["under_pressure_avg_length"] = under_pressure_avg_length
        result["without_pressure_avg_length"] = without_pressure_avg_length
        result["diff_in_avg_length_while_pressured"] = diff_in_avg_length

        return result

    def count_gk_distribution(self):
        gk_passes_df = self.passes[
            (self.passes["player"] == self.player)
            & (self.passes["position"] == "Goalkeeper")
        ].copy()
        open_play_df = gk_passes_df[~gk_passes_df["pass_type"].isin(self.set_pieces)]
        goal_kicks_df = gk_passes_df[gk_passes_df["pass_type"] == "Goal Kick"]
        hands_passes_df = gk_passes_df[gk_passes_df["pass_body_part"] == "Keeper Arm"]
        feet_passes_df = gk_passes_df[
            gk_passes_df["pass_body_part"].isin(["Left Foot", "Right Foot"])
        ]

        all_passes = {
            "gk_all_passes_" + k: v
            for k, v in self._count_gk_pass_length_accuracy(gk_passes_df).items()
        }
        open_play = {
            "gk_open_play_passes_" + k: v
            for k, v in self._count_gk_pass_length_accuracy(open_play_df).items()
        }
        goal_kicks = {
            "gk_goal_kicks_" + k: v
            for k, v in self._count_gk_pass_length_accuracy(goal_kicks_df).items()
        }
        hands_passes = {
            "gk_hands_passes_" + k: v
            for k, v in self._count_gk_pass_length_accuracy(hands_passes_df).items()
        }
        feet_passes = {
            "gk_feet_passes_" + k: v
            for k, v in self._count_gk_pass_length_accuracy(feet_passes_df).items()
        }
        open_play_pressures = {
            "gk_open_play_passes_" + k: v
            for k, v in self._count_gk_under_pressure_accuracy(open_play_df).items()
        }

        ret = {
            **all_passes,
            **open_play,
            **open_play_pressures,
            **goal_kicks,
            **hands_passes,
            **feet_passes,
        }

        return ret

    def count_gk_shots_faced(self):
        shots_against_df = self.player_match_events[
            (self.player_match_events["type"] == "Shot")
            & (self.player_match_events["team"] != self.team_name)
        ]

        shots_conceded = shots_against_df.shape[0]
        avg_shot_conceded_xg = shots_against_df["shot_statsbomb_xg"].mean()
        shot_conceded_xg = shots_against_df["shot_statsbomb_xg"].sum()

        shots_faced_df = shots_against_df[
            shots_against_df["shot_outcome"].isin(["Goal", "Saved", "Saved To Post"])
        ]
        shots_faced = shots_faced_df.shape[0]

        shot_faced_xg = shots_faced_df["shot_statsbomb_xg"].sum()
        shot_faced_post_shot_xg = shots_faced_df["shot_shot_execution_xg"].sum()
        avg_shot_faced_xg = shots_faced_df["shot_statsbomb_xg"].mean()
        avg_shot_faced_post_shot_xg = shots_faced_df["shot_shot_execution_xg"].mean()

        saved_shots_df = shots_against_df[
            shots_against_df["shot_outcome"].isin(["Saved", "Saved To Post"])
        ]
        saved_shots = saved_shots_df.shape[0]
        shot_saved_xg = saved_shots_df["shot_statsbomb_xg"].sum()
        shot_saved_post_shot_xg = saved_shots_df["shot_shot_execution_xg"].sum()
        avg_shot_saved_xg = saved_shots_df["shot_statsbomb_xg"].mean()
        avg_shot_saved_post_shot_xg = saved_shots_df["shot_shot_execution_xg"].mean()

        save_ratio = saved_shots / shots_faced if shots_faced > 0 else np.NaN

        goals_conceded = self.player_match_events[
            (self.player_match_events["goalkeeper_type"] == "Goal Conceded")
            & (self.player_match_events["player"] == self.player)
        ].shape[0]

        avg_goals_conceded_xg = shots_faced_df[
            shots_faced_df["shot_outcome"] == "Goal"
        ]["shot_statsbomb_xg"].mean()
        avg_goals_conceded_post_shot_xg = shots_faced_df[
            shots_faced_df["shot_outcome"] == "Goal"
        ]["shot_shot_execution_xg"].mean()

        ret = {
            "gk_shots_conceded": shots_conceded,
            "gk_shots_conceded_xg": shot_conceded_xg,
            "gk_avg_shot_conceded_xg": avg_shot_conceded_xg,
            "gk_shots_faced": shots_faced,
            "gk_shots_faced_xg": shot_faced_xg,
            "gk_shots_faced_post_shot_xg": shot_faced_post_shot_xg,
            "gk_avg_shot_faced_xg": avg_shot_faced_xg,
            "gk_avg_shot_faced_post_shot_xg": avg_shot_faced_post_shot_xg,
            "gk_shots_saved": saved_shots,
            "gk_shot_saved_xg": shot_saved_xg,
            "gk_shot_saved_post_shot_xg": shot_saved_post_shot_xg,
            "gk_avg_shot_saved_xg": avg_shot_saved_xg,
            "gk_avg_shot_saved_post_shot_xg": avg_shot_saved_post_shot_xg,
            "gk_save_ratio": save_ratio,
            "gk_goals_conceded": goals_conceded,
            "gk_avg_goals_conceded_xg": avg_goals_conceded_xg,
            "gk_avg_goals_conceded_post_shot_xg": avg_goals_conceded_post_shot_xg,
        }

        return ret

    def count_gk_positioning(self):

        gk_defensive_actions_df = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["position"] == "Goalkeeper")
            & (
                self.player_team_events["type"].isin(
                    ["Ball Recovery", "Block", "Dribbled Past", "Foul Won", "Pressure"]
                )
            )
        ].copy()

        avg_defensive_action_location = gk_defensive_actions_df["x"].mean()

        gk_open_play_passes_df = self.passes[
            (self.passes["player"] == self.player)
            & (self.passes["position"] == "Goalkeeper")
            & (~self.passes["pass_type"].isin(self.set_pieces))
        ].copy()

        gk_carries_df = self.carries[
            (self.carries["player"] == self.player)
            & (self.carries["position"] == "Goalkeeper")
        ].copy()

        gk_ball_receipt_df = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["position"] == "Goalkeeper")
            & (self.player_team_events["type"] == "Ball Receipt*")
        ].copy()

        avg_pass_location = gk_open_play_passes_df["x"].mean()
        avg_carry_start_location = gk_carries_df["x"].mean()
        avg_carry_end_location = gk_carries_df["carry_end_x"].mean()
        avg_ball_receipt_location = gk_ball_receipt_df["x"].mean()

        overall_avg_location_with_ball = pd.concat(
            [
                gk_open_play_passes_df["x"],
                gk_carries_df["x"],
                gk_carries_df["carry_end_x"],
                gk_ball_receipt_df["x"],
            ]
        ).mean()

        overall_avg_location = pd.concat(
            [
                gk_defensive_actions_df["x"],
                gk_open_play_passes_df["x"],
                gk_carries_df["x"],
                gk_carries_df["carry_end_x"],
                gk_ball_receipt_df["x"],
            ]
        ).mean()

        ret = {
            "gk_avg_defensive_action_location": avg_defensive_action_location,
            "gk_avg_open_play_pass_location": avg_pass_location,
            "gk_avg_carry_start_location": avg_carry_start_location,
            "gk_avg_carry_end_location": avg_carry_end_location,
            "gk_avg_ball_receipt_location": avg_ball_receipt_location,
            "gk_avg_location_with_ball": overall_avg_location_with_ball,
            "gk_avg_location": overall_avg_location,
        }

        return ret

    def _check_gk_contribution(self, df, time=20.0):
        contributed = 0
        match_events = self.player_match_events.copy()
        match_events["timestamp"] = pd.to_timedelta(match_events["timestamp"])

        for event in df.to_dict(orient="records"):
            possession_num = event["possession"]
            index_num = event["index"]
            event_timestamp = event["timestamp"]
            before_events = match_events[
                (match_events["possession"] == possession_num)
                & (match_events["index"] < index_num)
                & (
                    (event_timestamp - match_events["timestamp"]).dt.total_seconds()
                    <= time
                )
                & (match_events["type"] == "Pass")
                & (match_events["player"] == self.player)
            ]
            if not before_events.empty:
                contributed += 1
        return contributed

    def count_gk_offensive_contribution(self, time=20.0):
        free_kick_op_half = self.passes[
            (self.passes["pass_type"] == "Free Kick")
            & (self.passes["x"] >= self.oppostion_half)
        ].copy()
        corners = self.passes[self.passes["pass_type"] == "Corner"].copy()
        open_play_shots = self.shots[self.shots["shot_type"] == "Open Play"].copy()
        free_kick_shots = self.shots[self.shots["shot_type"] == "Free Kick"].copy()
        penalities_won = self.player_match_events[
            (self.player_match_events["team"] != self.team_name)
            & (self.player_match_events["foul_committed_penalty"] == True)
        ].copy()

        free_kick_op_half["timestamp"] = pd.to_timedelta(free_kick_op_half["timestamp"])
        corners["timestamp"] = pd.to_timedelta(corners["timestamp"])
        open_play_shots["timestamp"] = pd.to_timedelta(open_play_shots["timestamp"])
        free_kick_shots["timestamp"] = pd.to_timedelta(free_kick_shots["timestamp"])
        penalities_won["timestamp"] = pd.to_timedelta(penalities_won["timestamp"])

        contributed_free_kick_opposition_half = self._check_gk_contribution(
            free_kick_op_half, time
        )
        contributed_corners = self._check_gk_contribution(corners, time)
        contributed_open_play_shots = self._check_gk_contribution(open_play_shots, time)
        contributed_direct_free_kick_shots = self._check_gk_contribution(
            free_kick_shots, time
        )
        contributed_penalities_won = self._check_gk_contribution(penalities_won, time)

        tpo = (
            0.5 * contributed_free_kick_opposition_half
            + 0.4 * contributed_corners
            + 1.0 * (contributed_open_play_shots + contributed_direct_free_kick_shots)
            + 7.5 * contributed_penalities_won
        )

        ret = {
            "gk_contributed_free_kick_opposition_half": contributed_free_kick_opposition_half,
            "gk_contributed_corners": contributed_corners,
            "gk_contributed_open_play_shots": contributed_open_play_shots,
            "gk_contributed_direct_free_kick_shots": contributed_direct_free_kick_shots,
            "gk_contributed_penalities_won": contributed_penalities_won,
            "gk_tpo_total_positive_outcome": tpo,
        }

        return ret

    def count_gk_defensive_actions(self):
        gk_defensive_actions_df = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["position"] == "Goalkeeper")
            & (
                self.player_team_events["type"].isin(
                    ["Ball Recovery", "Block", "Dribbled Past", "Foul Won", "Pressure"]
                )
            )
        ].copy()

        defensive_actions = gk_defensive_actions_df.groupby(
            "type", dropna=False
        ).count()["index"]
        ball_recoveries = (
            defensive_actions["Ball Recovery"]
            if "Ball Recovery" in defensive_actions
            else 0
        )
        blocks = defensive_actions["Block"] if "Block" in defensive_actions else 0
        pressures = (
            defensive_actions["Pressure"] if "Pressure" in defensive_actions else 0
        )
        blocks = defensive_actions["Foul Won"] if "Foul Won" in defensive_actions else 0
        dribbled_past = (
            defensive_actions["Dribbled Past"]
            if "Dribbled Past" in defensive_actions
            else 0
        )
        total_defensive_actions = defensive_actions.sum()

        punches_df = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["position"] == "Goalkeeper")
            & (self.player_team_events["goalkeeper_type"] == "Punch")
        ]
        punches_grouped = punches_df.groupby(
            "goalkeeper_outcome", dropna=False
        ).count()["index"]
        punches_save = (
            punches_grouped["In Play Safe"] if "In Play Safe" in punches_grouped else 0
        )
        punches_danger = (
            punches_grouped["In Play Danger"]
            if "In Play Danger" in punches_grouped
            else 0
        )
        punches_out = (
            punches_grouped["Punched out"] if "Punched out" in punches_grouped else 0
        )
        total_punches = punches_grouped.sum()

        clears = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["position"] == "Goalkeeper")
            & (self.player_team_events["goalkeeper_outcome"] == "Clear")
        ].shape[0]

        smothers_df = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["position"] == "Goalkeeper")
            & (self.player_team_events["goalkeeper_type"] == "Smother")
        ]
        smothers = smothers_df.shape[0]
        smothers_won = smothers_df[
            smothers_df["goalkeeper_outcome"].isin(
                ["Won", "Success In Play", "Success Out"]
            )
        ].shape[0]

        ret = {
            "gk_ball_recoveries": ball_recoveries,
            "gk_blocks": blocks,
            "gk_pressures": pressures,
            "gk_blocks": blocks,
            "gk_dribbled_past": dribbled_past,
            "gk_total_defensive_actions": total_defensive_actions,
            "gk_punches_save": punches_save,
            "gk_punches_danger": punches_danger,
            "gk_punches_out": punches_out,
            "gk_total_punches": total_punches,
            "gk_clears": clears,
            "gk_total_smothers": smothers,
            "gk_smothers_won": smothers_won,
        }
        return ret

    def count_gk_claims(self):
        collections_df = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["position"] == "Goalkeeper")
            & (self.player_team_events["goalkeeper_type"] == "Collected")
        ]
        total_collections = collections_df.shape[0]
        collections_won = collections_df[
            collections_df["goalkeeper_outcome"].isin(["Collected Twice", "Success"])
        ].shape[0]
        ratio_collections = (
            collections_won / total_collections if total_collections > 0 else np.NaN
        )

        claims = self.player_team_events[
            (self.player_team_events["player"] == self.player)
            & (self.player_team_events["position"] == "Goalkeeper")
            & (self.player_team_events["goalkeeper_outcome"] == "Claim")
        ].shape[0]

        ret = {
            "gk_total_collections": total_collections,
            "gk_collections_won": collections_won,
            "gk_ratio_collections": ratio_collections,
            "gk_claims": claims,
        }

        return ret

    def aggregate_goalkeeper_statistics(self) -> pd.DataFrame:
        """
        Aggregates all statistics for the given player.

        Args:
            player (str): Player name for whom to calculate statistics.

        Returns:
            pd.DataFrame: DataFrame with all aggregated statistics.
        """
        stats_functions = [
            self.count_gk_distribution,
            self.count_gk_shots_faced,
            self.count_gk_positioning,
            self.count_gk_offensive_contribution,
            self.count_gk_defensive_actions,
            self.count_gk_claims,
        ]
        results = {
            key: value for func in stats_functions for key, value in func().items()
        }
        results["minutes_played"] = self.player_minutes_info[
            "played_time_minutes_decimal"
        ]
        ret = pd.DataFrame([results]).T
        # ret.columns = [player]
        ret = ret.round(2).T
        ret["player"] = self.player
        ret["match_id"] = self.match_id
        ret = ret[
            ["match_id", "player", "minutes_played"]
            + [
                col
                for col in ret.columns
                if col not in ["match_id", "player", "minutes_played"]
            ]
        ]
        return ret

    # TODO: TIMEDELTA IN WHOLE DF
    # TODO: GK BALL RECOVERIES FAIL

    @staticmethod
    def prepare_player_statistics(
        all_matches_events: pd.DataFrame,
        available_matches: pd.DataFrame,
        team_name: str,
        chosen_player: str,
        position: str,
    ):
        """
        Prepares player statistics for the specified player, saving to or loading from a TSV file
        in the player's directory if up-to-date.

        Args:
            all_matches_events (pd.DataFrame): DataFrame containing event data for all matches.
            available_matches (pd.DataFrame): DataFrame containing information about available matches.
            team_name (str): The team name to filter matches.
            chosen_player (str): The player's name for whom statistics are generated.

        Returns:
            pd.DataFrame: DataFrame of aggregated player statistics.
        """

        # Set up the player's directory and file path
        directory = ensure_player_directory(chosen_player)
        file_path = os.path.join(directory, f"{chosen_player}_stats.tsv")

        # Get the latest match date
        last_match_update_date = get_newest_datetime(available_matches)

        # Check if the stats file is up-to-date
        if is_file_up_to_date(file_path, last_match_update_date):
            # Load player statistics from the TSV file
            return pd.read_csv(file_path, sep="\t")

        # Generate player statistics if the file is not up-to-date or doesn't exist
        player_matches = all_matches_events[
            all_matches_events["player"] == chosen_player
        ]["match_id"].unique()
        player_stats = pd.DataFrame()

        for game_id in player_matches:
            game_file_path = os.path.join(
                directory, f"{chosen_player}_{game_id}_stats.tsv"
            )
            if os.path.exists(game_file_path):
                player_df = pd.read_csv(game_file_path, sep="\t")
            else:
                game_events = all_matches_events[
                    all_matches_events["match_id"] == game_id
                ]
                stats = PlayerStatistics(
                    match_events=game_events,
                    player=chosen_player,
                    team_name=team_name,
                    match_id=game_id,
                )
                player_df = (
                    stats.aggregate_player_statistics()
                    if position != "Goalkeeper"
                    else stats.aggregate_goalkeeper_statistics()
                )
                player_df.to_csv(game_file_path, sep="\t", index=False)

            player_stats = pd.concat([player_stats, player_df])
        player_stats = (
            available_matches[["match_id", "match_date", "opponent", "match_result"]]
            .merge(player_stats, on="match_id", how="right")
            .sort_values(["match_date"], ascending=True)
            .reset_index(drop=True)
        )
        # Save the aggregated statistics to a TSV file
        player_stats.to_csv(file_path, sep="\t", index=False)

        return player_stats
