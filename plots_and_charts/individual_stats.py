import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
from plottable import ColDef, Table
from plottable.cmap import normed_cmap

from constants import Constants


class IndividualStats:

    def __init__(self, player_match_stats: pd.DataFrame, team_for: str) -> None:
        """
        Initialize the IndividualStats class.

        Args:
            player_match_events (pd.DataFrame): DataFrame containing data.
            team_for (str): The team to analyze.
        """
        self.player_match_stats = player_match_stats
        self.team_for = team_for
        self.cmap = LinearSegmentedColormap.from_list(name="", colors=Constants.CMAP_IND_GOOD, N=80)
        self.cmap_bad = ListedColormap(name="", colors=Constants.CMAP_IND_BAD, N=4)


    @staticmethod
    def per_90(row, stat):
        per_1 = row[stat]/row["player_match_minutes"]
        return round(per_1*90, 2)

    @staticmethod
    def format_float(value):
        return round(value, 2)

    @staticmethod
    def create_cmap(df, col, cmap):
        min = df[col].min()
        max = df[col].max()
        return normed_cmap(pd.DataFrame([min, max]), cmap, num_stds=1)

    def plot_offensive_table(self, directory: str, figsize: tuple[int, int] = (30, 15)) -> plt.Figure:

        attack_data = self.player_match_stats[self.player_match_stats["team_name"] == self.team_for].copy()
        attack_data = attack_data[["player_name", "player_match_minutes", "player_match_goals", "player_match_assists", "player_match_np_shots", "player_match_np_xg", "player_match_np_xg_per_shot",
                            "player_match_passes", "player_match_crosses", "player_match_xa", "player_match_key_passes", "player_match_passes_into_box", "player_match_through_balls", "player_match_deep_progressions"]]
        attack_data = attack_data.round(2)
        attack_data["player_match_minutes"] = attack_data["player_match_minutes"].round(0).astype("int")

        attack_data = attack_data.fillna(.0)
        attack_data.set_index("player_name", inplace=True)
        attack_data["player_match_np_xg_per_90"] = attack_data.apply(lambda x: self.per_90(x, "player_match_np_xg"), axis=1)
        attack_data["player_match_xa_per_90"] = attack_data.apply(lambda x: self.per_90(x, "player_match_xa"), axis=1)
        attack_data["player_match_deep_progressions_per_90"] = attack_data.apply(lambda x: self.per_90(x, "player_match_deep_progressions"), axis=1)

        attack_data.sort_index(inplace=True)

        row_font_size = 14

        table_col_defs = [
            ColDef("player_name", title="", width=3, textprops={"fontsize": 18, "ha": "left", "fontname": Constants.FONT}),
            ColDef("player_match_minutes", title="Minutes", 
                   width=1, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}),
            ColDef("player_match_goals", title="Goals", 
                   width=1, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(attack_data, "player_match_goals", self.cmap)),
            ColDef("player_match_assists", title="Assists", 
                   width=1, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(attack_data, "player_match_assists", self.cmap)),
            ColDef("player_match_np_shots", title="Non-penalty \nshots", 
                   width=2, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(attack_data, "player_match_np_shots", self.cmap)),
            ColDef("player_match_np_xg", title="Non-penalty \nxG", 
                   width=2, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(attack_data, "player_match_np_xg", self.cmap)),
            ColDef("player_match_np_xg_per_shot", title="Non-penalty \nxG per shot", 
                   width=2, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(attack_data, "player_match_np_xg_per_shot", self.cmap)),
            ColDef("player_match_passes", title="Passes",
                    width=1, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(attack_data, "player_match_passes", self.cmap)),
            ColDef("player_match_crosses", title="Crosses", 
                   width=1.5, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(attack_data, "player_match_crosses", self.cmap)),
            ColDef("player_match_key_passes", title="Key pases", 
                   width=1.5, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(attack_data, "player_match_key_passes", self.cmap)),
            ColDef("player_match_xa", title="xA", 
                   width=1, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(attack_data, "player_match_xa", self.cmap)),
            ColDef("player_match_passes_into_box", title="Passes \ninto box", 
                   width=1.5, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(attack_data, "player_match_passes_into_box", self.cmap)),
            ColDef("player_match_through_balls", title="Through balls", 
                   width=2, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(attack_data, "player_match_through_balls", self.cmap)),
            ColDef("player_match_deep_progressions", title="Deep \nprogressions", 
                   width=2, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(attack_data, "player_match_deep_progressions", self.cmap)),
            ColDef("player_match_deep_progressions_per_90", title="Deep \nprogressions per 90", 
                   width=3, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(attack_data, "player_match_deep_progressions_per_90", self.cmap)),
            ColDef("player_match_np_xg_per_90", title="Non-penalty \nxG per 90", 
                   width=2.5, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(attack_data, "player_match_np_xg_per_90", self.cmap)),
            ColDef("player_match_xa_per_90", title="xA per 90", 
                   width=2, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(attack_data, "player_match_xa_per_90", self.cmap)),

        ]
        fig, ax = plt.subplots(figsize=figsize)
        plt.rcParams["text.color"] = Constants.TEXT_COLOR
        plt.rcParams["font.family"] = Constants.FONT
        fig.set_facecolor(Constants.STREAMLIT_COLOR)
        ax.set_facecolor(Constants.BACKGROUND_COLOR)
        tab = Table(
            attack_data,
            column_definitions=table_col_defs,
            row_dividers=True,
            col_label_divider=True,
            footer_divider=False,
            even_row_color= Constants.EVEN_ROW_COLOR,
            odd_row_color= Constants.EVEN_ROW_COLOR,
        )

        fig.savefig(
            f"{directory}/individual_attack.png",
            facecolor=fig.get_facecolor(),
            dpi=Constants.DPI,
            bbox_inches='tight', 
            pad_inches=Constants.PAD_INCHES
        )

        return fig
    

    def plot_defensive_table(self, directory: str, figsize: tuple[int, int] = (30, 15)) -> plt.Figure:

        defence_data = self.player_match_stats[self.player_match_stats["team_name"] == self.team_for].copy()
        defence_data = defence_data[["player_name", "player_match_minutes", "player_match_defensive_actions", "player_match_tackles", "player_match_interceptions", "player_match_dribbled_past", "player_match_dispossessions",
                                    "player_match_aerial_ratio", "player_match_turnovers", "player_match_ball_recoveries", "player_match_pressures", "player_match_counterpressures", "player_match_pressure_regains"]]
        defence_data = defence_data.fillna(.0)

        defence_data["player_match_minutes"] = defence_data["player_match_minutes"].round(0).astype("int")
        defence_data["player_match_pressures"] = defence_data["player_match_pressures"].round(0).astype("int")
        defence_data["player_match_counterpressures"] = defence_data["player_match_counterpressures"].round(0).astype("int")

        defence_data.set_index("player_name", inplace=True)
        defence_data["player_match_ball_recoveries_per_90"] = defence_data.apply(lambda x: self.per_90(x, "player_match_ball_recoveries"), axis=1)
        defence_data["player_match_pressures_per_90"] = defence_data.apply(lambda x: self.per_90(x, "player_match_pressures"), axis=1)
        defence_data["player_match_defensive_actions_per_90"] = defence_data.apply(lambda x: self.per_90(x, "player_match_defensive_actions"), axis=1)

        defence_data.sort_index(inplace=True)

        row_font_size = 14

        table_col_defs = [
            ColDef("player_name", title="", 
                   width=3, textprops={"fontsize": 18, "ha": "left", "fontname": Constants.FONT}),
            ColDef("player_match_minutes", title="Minutes", 
                   width=1, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}),
            ColDef("player_match_defensive_actions", title="Defensive \nactions", 
                   width=1.5, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(defence_data, "player_match_defensive_actions", self.cmap)),
            ColDef("player_match_tackles", title="Tackles", 
                   width=1, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(defence_data, "player_match_tackles", self.cmap)),
            ColDef("player_match_interceptions", title="Interceptions", 
                   width=2, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(defence_data, "player_match_interceptions", self.cmap)),
            ColDef("player_match_dribbled_past", title="Dribbled past", 
                   width=2, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(defence_data, "player_match_dribbled_past", self.cmap_bad)),
            ColDef("player_match_dispossessions", title="Dispossessions", 
                   width=2, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(defence_data, "player_match_dispossessions", self.cmap_bad)),
            ColDef("player_match_aerial_ratio", title="Aerial duels \nratio", 
                   width=2, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(defence_data, "player_match_aerial_ratio", self.cmap), formatter=self.format_float),
            ColDef("player_match_turnovers", title="Turnovers", 
                   width=1.5, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(defence_data, "player_match_turnovers", self.cmap_bad)),
            ColDef("player_match_ball_recoveries", title="Ball \nrecoveries", 
                   width=1.5, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(defence_data, "player_match_ball_recoveries", self.cmap)),
            ColDef("player_match_pressures", title="Pressures", 
                   width=1.5, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(defence_data, "player_match_pressures", self.cmap)),
            ColDef("player_match_counterpressures", title="Counter-\npressures", 
                   width=2, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(defence_data, "player_match_counterpressures", self.cmap)),
            ColDef("player_match_pressure_regains", title="Pressure \nregains", 
                   width=2, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(defence_data, "player_match_pressure_regains", self.cmap)),
            ColDef("player_match_ball_recoveries_per_90", title="Ball \nrecoveries per 90", 
                   width=2.5, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(defence_data, "player_match_ball_recoveries_per_90", self.cmap)),
            ColDef("player_match_pressures_per_90", title="Pressures \nper 90", 
                   width=2, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(defence_data, "player_match_pressures_per_90", self.cmap)),
            ColDef("player_match_defensive_actions_per_90", title="Defensive \nactions per 90", 
                   width=2, textprops={"fontsize": row_font_size, "ha": "center", "fontname": Constants.FONT}, cmap=self.create_cmap(defence_data, "player_match_defensive_actions_per_90", self.cmap)),
        ]

        fig, ax = plt.subplots(figsize=figsize)
        plt.rcParams["text.color"] = Constants.TEXT_COLOR
        plt.rcParams["font.family"] = Constants.FONT
        fig.set_facecolor(Constants.STREAMLIT_COLOR)
        ax.set_facecolor(Constants.BACKGROUND_COLOR)
        tab = Table(
            defence_data,
            column_definitions=table_col_defs,
            row_dividers=True,
            col_label_divider=True,
            footer_divider=False,
            even_row_color= Constants.EVEN_ROW_COLOR,
            odd_row_color= Constants.EVEN_ROW_COLOR,
        )

        fig.savefig(
            f"{directory}/individual_defence.png",
            facecolor=fig.get_facecolor(),
            dpi=Constants.DPI,
            bbox_inches='tight', 
            pad_inches=Constants.PAD_INCHES
        )

        return fig