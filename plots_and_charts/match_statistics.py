import matplotlib.pyplot as plt
import pandas as pd

from constants import Constants


class MatchStatistics:

    def __init__(self, match_events, team_for):
        self.match_events = match_events
        self.team_for = team_for

    @staticmethod
    def count_goals(df):
        shot_goals = df[df["shot_outcome"] == "Goal"].shape[0]
        own_goals = df[df["type"] == "Own Goal For"].shape[0]
        return shot_goals + own_goals

    @staticmethod
    def count_stats_by_grouping(df):
        stats = (
            df.groupby(["team"])
            .agg(
                xG=("shot_statsbomb_xg", "sum"),
                non_penalty_xG=(
                    "shot_statsbomb_xg",
                    lambda x: x[(df["type"] == "Shot") & (df["shot_type"] != "Penalty")].sum(),
                ),
                average_xG_per_shot=("shot_statsbomb_xg", lambda x: x[(df["type"] == "Shot")].mean()),
                non_penalty_average_xG_per_shot=(
                    "shot_statsbomb_xg",
                    lambda x: x[(df["type"] == "Shot") & (df["shot_type"] != "Penalty")].mean(),
                ),
                post_shot_xG=("shot_gk_save_difficulty_xg", "sum"),
                shots=("index", lambda x: x[df["type"] == "Shot"].count()),
                shots_on_target=(
                    "index",
                    lambda x: x[df["shot_outcome"].isin(["Saved", "Goal", "Saved To Post"])].count(),
                ),
                passes=("index", lambda x: x[df["type"] == "Pass"].count()),
                passes_completed=("index", lambda x: x[(df["type"] == "Pass") & (df["pass_outcome"].isna())].count()),
                dribbles=("index", lambda x: x[df["type"] == "Dribble"].count()),
                successful_dribbles=("index", lambda x: x[df["dribble_outcome"] == "Complete"].count()),
                crosses=("index", lambda x: x[df["pass_cross"] == True].count()),
                crosses_completed=(
                    "index",
                    lambda x: x[(df["pass_cross"] == True) & (df["pass_outcome"].isna())].count(),
                ),
                fouls=("index", lambda x: x[df["type"] == "Foul Committed"].count()),
                pressures=("index", lambda x: x[df["type"] == "Pressure"].count()),
                counterpressures=(
                    "index",
                    lambda x: x[(df["type"] == "Pressure") & (df["counterpress"] == True)].count(),
                ),
                tackles=("index", lambda x: x[df["duel_type"] == "Tackle"].count()),
                tackles_won=(
                    "index",
                    lambda x: x[
                        (df["duel_type"] == "Tackle")
                        & (df["duel_outcome"].isin(["Won", "Success In Play", "Success Out", "Success"]))
                    ].count(),
                ),
                dribbled_past=("index", lambda x: x[df["type"] == "Dribbled Past"].count()),
            )
            .reset_index()
        )
        return stats

    @staticmethod
    def count_cards(df):
        cards_bad_behaviour, cards_foul_committed = pd.DataFrame(), pd.DataFrame()

        if "bad_behaviour_card" in df.columns:
            cards_bad_behaviour = (
                df.groupby(["team"])
                .agg(
                    yellow_cards=("index", lambda x: (df.loc[x.index, "bad_behaviour_card"] == "Yellow Card").sum()),
                    red_cards=("index", lambda x: (df.loc[x.index, "bad_behaviour_card"] == "Red Card").sum()),
                    second_yellow_cards=(
                        "index",
                        lambda x: (df.loc[x.index, "bad_behaviour_card"] == "Second Yellow").sum(),
                    ),
                )
                .reset_index()
            )

        if "foul_committed_card" in df.columns:
            cards_foul_committed = (
                df.groupby(["team"])
                .agg(
                    yellow_cards=("index", lambda x: (df.loc[x.index, "foul_committed_card"] == "Yellow Card").sum()),
                    red_cards=("index", lambda x: (df.loc[x.index, "foul_committed_card"] == "Red Card").sum()),
                    second_yellow_cards=(
                        "index",
                        lambda x: (df.loc[x.index, "foul_committed_card"] == "Second Yellow").sum(),
                    ),
                )
                .reset_index()
            )

        # Merge the two DataFrames or create an empty DataFrame if both are empty
        if not cards_bad_behaviour.empty and not cards_foul_committed.empty:
            cards = (
                cards_bad_behaviour.set_index("team")
                .add(cards_foul_committed.set_index("team"), fill_value=0)
                .reset_index()
            )
        elif not cards_bad_behaviour.empty:
            cards = cards_bad_behaviour
        elif not cards_foul_committed.empty:
            cards = cards_foul_committed
        else:
            # If both are empty, create a default DataFrame with all zeros
            unique_teams = df["team"].unique()
            cards = pd.DataFrame({"team": unique_teams, "yellow_cards": 0, "red_cards": 0, "second_yellow_cards": 0})

        return cards

    @staticmethod
    def change_formatting(df):
        df = df.copy()
        for col in df.columns:
            if "%" in col:
                df[col] = df[col] * 100.0
                df[col] = df[col].round(0).astype(int).astype(str)
                df[col] = df[col] + "%"
            elif col not in [
                "xG",
                "non_penalty_xG",
                "post_shot_xG",
                "average_xG_per_shot",
                "non_penalty_average_xG_per_shot",
            ]:
                df[col] = df[col].astype(int).astype(str)
            else:
                df[col] = df[col].round(2).astype(str)

        df.columns = [col.replace("_", " ").replace("%", "") for col in df.columns]

        return df

    def prepare_team_stats(self, df, team_for):
        df = df[(df["team"] == self.team_for) == team_for].copy()
        team = df.iloc[0]["team"]
        goals = self.count_goals(df)
        goals_df = pd.DataFrame([{"team": team, "goals": goals}])
        grouped_stats = self.count_stats_by_grouping(df)
        cards = self.count_cards(df)
        team_stats = goals_df.merge(grouped_stats, on="team")
        team_stats = team_stats.merge(cards, on="team")
        return team_stats

    @staticmethod
    def count_ratios(df):
        df = df.copy()
        df["shot_accuracy%"] = df["shots_on_target"] / df["shots"]
        df["pass_completion%"] = df["passes_completed"] / df["passes"]
        df["cross_completion%"] = df["crosses_completed"] / df["crosses"]
        df["dribbles_efficiency%"] = df["successful_dribbles"] / df["dribbles"]
        return df

    @staticmethod
    def merge_columns(df):
        df = df.copy()
        df["xG (non-penalty)"] = df["xG"] + " (" + df["non penalty xG"] + ")"
        df["shots (on target)"] = df["shots"] + " (" + df["shots on target"] + ")"
        df["average xG per shot (non-penalty)"] = (
            df["average xG per shot"] + " (" + df["non penalty average xG per shot"] + ")"
        )
        df["passes (completed)"] = df["passes"] + " (" + df["passes completed"] + ")"
        df["dribbles (successful)"] = df["dribbles"] + " (" + df["successful dribbles"] + ")"
        df["crosses (completed)"] = df["crosses"] + " (" + df["crosses completed"] + ")"
        df["pressures (counterpressures)"] = df["pressures"] + " (" + df["counterpressures"] + ")"
        df["tackles (won)"] = df["tackles"] + " (" + df["tackles won"] + ")"
        df["red cards / second yellow cards"] = df["red cards"] + " / " + df["second yellow cards"]

        to_remove = [
            "xG",
            "non penalty xG",
            "shots",
            "shots on target",
            "passes",
            "passes completed",
            "dribbles",
            "successful dribbles",
            "non penalty average xG per shot",
            "average xG per shot",
            "crosses",
            "crosses completed",
            "pressures",
            "counterpressures",
            "tackles",
            "tackles won",
            "red cards",
            "second yellow cards",
        ]

        df = df.drop(to_remove, axis=1)
        return df

    def prepare_data(self):
        df = self.match_events.copy()
        our_stats = self.prepare_team_stats(df, True)
        opponent_stats = self.prepare_team_stats(df, False)

        stats = pd.concat([our_stats, opponent_stats]).rename({"team": "Stat"}, axis=1)
        stats = stats.set_index("Stat")
        stats = self.count_ratios(stats)
        stats = self.change_formatting(stats)
        stats = self.merge_columns(stats)
        stats = stats[
            [
                "goals",
                "xG (non-penalty)",
                "post shot xG",
                "shots (on target)",
                "shot accuracy",
                "average xG per shot (non-penalty)",
                "passes (completed)",
                "pass completion",
                "dribbles (successful)",
                "dribbles efficiency",
                "crosses (completed)",
                "cross completion",
                "pressures (counterpressures)",
                "tackles (won)",
                "dribbled past",
                "fouls",
                "yellow cards",
                "red cards / second yellow cards",
            ]
        ]
        stats = stats.T.reset_index().rename({"index": "Stat"}, axis=1)
        return stats

    def create_match_stats_table(self, directory: str, figsize: tuple[int, int] = (14, 0.7)):
        """
        Create a side-by-side match stats visualization using matplotlib.

        Args:
            df (pd.DataFrame): DataFrame with stats, where each column represents one team's stats.
                               The first column should be the stats descriptions (e.g., "Goals").
        """
        df = self.prepare_data()
        # Extract team names from the DataFrame
        stats = df.iloc[:, 0]  # First column: stat descriptions
        team1_name = df.columns[1]  # Second column: first team
        team2_name = df.columns[2]  # Third column: second team
        team1_stats = df.iloc[:, 1]
        team2_stats = df.iloc[:, 2]

        # Set up the plot
        fig, ax = plt.subplots(figsize=(figsize[0], len(stats) * figsize[1]))  # Height scales with number of rows
        ax.axis("off")  # Remove axes
        fig.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
        ax.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
        plt.rcParams["font.family"] = Constants.FONT

        # Create the table as a list of rows
        table_data = []
        for i in range(len(stats)):
            row = [team1_stats.iloc[i], stats.iloc[i], team2_stats.iloc[i]]
            table_data.append(row)

        # Add the table to the figure
        table = ax.table(
            cellText=table_data,
            colLabels=[team1_name, "", team2_name],  # Headers
            # colColours=["#cce5ff", Constants.DARK_BACKGROUND_COLOR, "#ffcccc"],  # Highlight columns for teams
            bbox=[0, 0, 1, 1],
            cellLoc="center",
            edges="closed",
            # {'closed', 'open', 'horizontal', 'vertical'}
        )

        # Format the table
        table.auto_set_font_size(False)
        table.set_fontsize(20)
        table.auto_set_column_width(col=list(range(len(df.columns))))

        # Highlight the stat name column
        for (row, col), cell in table.get_celld().items():
            if row == 0:  # Header row
                cell.set_facecolor(Constants.DARKGREEN_COLOR)
                cell.get_text().set_color(Constants.LIGHT_TEXT_COLOR)
                cell.get_text().set_fontweight("bold")
                cell.set_edgecolor(Constants.DARKGREEN_COLOR)  # Hide edges in the header
                cell.set_linewidth(0.5)  # Thicker lines for header
            else:
                cell.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
                cell.get_text().set_color(Constants.LIGHT_TEXT_COLOR)
                cell.set_edgecolor(Constants.DARK_BACKGROUND_COLOR)
                cell.set_linewidth(0.5)

            if row % 2 != 0:
                cell.set_facecolor(Constants.LIGHTGREY_COLOR)
                cell.set_edgecolor(Constants.LIGHTGREY_COLOR)

        fig.savefig(
            f"{directory}/match_summary.png",
            facecolor=fig.get_facecolor(),
            dpi=Constants.DPI,
            bbox_inches="tight",
            pad_inches=Constants.PAD_INCHES,
        )

        return fig
