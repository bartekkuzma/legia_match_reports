import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from constants import Constants
from utils import get_data, unpack_coordinates


class TrendlineCharts:

    def __init__(self, matches: pd.DataFrame, game_id: int, team_for: str, creds: dict[str, str]) -> None:
        self.game_id = game_id
        self.team_for = team_for
        self.creds = creds
        self.matches = self.get_matches_data(matches, team_for)
        self.matches_events = self.get_events_data()

    @staticmethod
    def get_matches_data(full_matches, team_name):
        matches = full_matches[((full_matches["home_team"] == team_name) | (full_matches["away_team"] == team_name)) & (full_matches["match_status"] == "available")]
        matches['goals_scored'] = matches.apply(lambda row: row['home_score'] if row['home_team'] == team_name else row['away_score'], axis=1).astype(int)
        matches['goals_conceded'] = matches.apply(lambda row: row['away_score'] if row['home_team'] == team_name else row['home_score'], axis=1).astype(int)
        matches['match_result'] = matches.apply(lambda row: 'Won' if row['goals_scored'] > row['goals_conceded'] else ('Draw' if row['goals_scored'] == row['goals_conceded'] else 'Lost'), axis=1)
        matches['opponent'] = matches.apply(lambda row: row['away_team'] if row['home_team'] == team_name else row['home_team'], axis=1)
        matches = matches[["match_id", "match_date", "competition", "goals_scored", "goals_conceded", "match_result", "opponent"]].sort_values("match_date")
    
        return matches
        
    def get_events_data(self):

        list_matches = self.matches.match_id.tolist()
        df = []
        for n in list_matches:
            match_events = get_data(match_id = n, data_type="events", creds=self.creds)
            df.append(match_events)
        df = pd.concat(df)
        # Unpack 'location', 'pass_end_location', and 'carry_end_location' at once and concatenate
        df_unpacked = pd.concat([
            df['location'].apply(unpack_coordinates, args=(3,)).apply(pd.Series).rename(columns={0: 'x', 1: 'y', 2: 'z'}),
            df['pass_end_location'].apply(unpack_coordinates, args=(2,)).apply(pd.Series).rename(columns={0: 'pass_end_x', 1: 'pass_end_y'}),
            df['carry_end_location'].apply(unpack_coordinates, args=(2,)).apply(pd.Series).rename(columns={0: 'carry_end_x', 1: 'carry_end_y'})
        ], axis=1)

        # Concatenate the new columns to the original dataframe
        df = pd.concat([df, df_unpacked], axis=1)
        return df


    def plot_trendline(self, df: pd.DataFrame, title_stat: str, y_stat: str, figsize: tuple[int, int] = (16, 10)):

        # Create the plot
        fig, ax = plt.subplots(figsize=figsize)
        fig.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
        ax.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
        plt.rcParams["font.family"] = Constants.FONT

        # Plot bars
        x = range(len(df))
        width = 0.35

        # Plot trend lines
        ax.plot(x, df['team_stat'], color=Constants.OFF_WHITE_COLOR, linestyle='--', alpha=0.7, linewidth=3, label=self.team_for)
        ax.plot(x, df['opponent_stat'], color=Constants.SALMON_COLOR, linestyle='--', alpha=0.7, linewidth=3, label='Opponent')
        ax.scatter(x, df['team_stat'], color=Constants.DARK_BACKGROUND_COLOR, edgecolors=Constants.OFF_WHITE_COLOR, s=100, zorder=3)
        ax.scatter(x, df['opponent_stat'], color=Constants.DARK_BACKGROUND_COLOR, edgecolors=Constants.SALMON_COLOR, s=100, zorder=3)
        # MATCH
        match_df = df[df["match_id"]==self.game_id]
        ax.scatter(match_df.index, match_df['team_stat'], color=Constants.DARK_BACKGROUND_COLOR, edgecolors=Constants.COLORS["yellow"], s=1000, zorder=1, linewidth=3)
        ax.scatter(match_df.index, match_df['opponent_stat'], color=Constants.DARK_BACKGROUND_COLOR, edgecolors=Constants.COLORS["yellow"], s=1000, zorder=1, linewidth=3)

        # Customize the plot
        # Set the main title (suptitle)
        fig.suptitle(f'{self.team_for} vs Opponents', fontsize=36, color=Constants.COLORS["white"], ha='center', y=1.06)    
        # Set the subtitle
        # Set the subtitle using a second suptitle
        fig.text(0.5, 0.97, f'{title_stat}', fontsize=26, color=Constants.COLORS["white"], ha='center')
        # ax.set_title(f'{title_stat}', fontsize=26, pad=30, color=Constants.COLORS["white"], ha='center')
        ax.set_xlabel('Opponent', fontsize=26, color=Constants.COLORS["white"])
        ax.set_ylabel(f'{y_stat}', fontsize=26, color=Constants.COLORS["white"])
        ax.set_xticks(x)
        ax.set_xticklabels(df['opponent'], rotation=45, ha='right', fontsize=20, color="white")
        for label in ax.get_yticklabels():
            label.set_color(Constants.COLORS["white"])
        ax.tick_params(axis='x', which='major', pad=30)
        ax.tick_params(axis='both', which='both', labelsize=16, color = Constants.COLORS["white"])

        bbox = dict(boxstyle="round", fc="0.3", ec="0.5", alpha=0.7)
        min_val = min(df['team_stat'].to_list() + df['opponent_stat'].to_list())

        # Add value labels on top of bars
        for i, result in enumerate(df["match_result"]):
            ax.text(i, min_val-.15,
                f'{result}', ha='center', va='center', fontweight='bold', fontsize=15, bbox=bbox, rotation=0, color = Constants.COLORS["white"])

        # Add legend with enhanced visibility
        legend = ax.legend(loc='upper left', fontsize=20)
        for text in legend.get_texts():
            plt.setp(text, color = Constants.COLORS["white"])
        legend.get_frame().set_facecolor('#404040')  # Set the background color to a dark gray
        legend.get_frame().set_alpha(0.9)  # Make it slightly transparent
        legend.get_frame().set_edgecolor(Constants.COLORS["white"])  # Add a white edge color for better contrast
        legend.get_frame().set_linewidth(1.5)  # Increase the thickness of the border

        # Customize grid and minor ticks
        ax.grid(axis='y', linestyle='--', alpha=0.5)  # Major gridlines
        ax.minorticks_on()  # Enable minor ticks
        ax.grid(which='minor', axis='y', linestyle=':', alpha=0.3)  # Minor gridlines with dotted style

        for i in (["right","top","left","bottom"]):
            ax.spines[i].set_visible(False)

        # Add grid for better readability
        # ax.grid(axis='y', linestyle='--', alpha=0.5)
        
        # Adjust layout and display the plot
        plt.tight_layout()
        return fig

    def plot_xg_trendline(self, directory: str, figsize: tuple[int, int] = (16, 10)):
        stat_name = "shot_statsbomb_xg"
        stat = self.matches_events.groupby(["match_id", "team"])[stat_name].sum().to_frame().reset_index()
        # Pivot the table to separate xG values for 'Legia Warszawa' and their opponents
        team_stat = stat[stat['team'] == self.team_for].set_index('match_id')[stat_name]
        opponent_stat = stat[stat['team'] != self.team_for].set_index('match_id')[stat_name]

        # Combine into a new DataFrame
        stat_df = pd.DataFrame({
            'team_stat': team_stat,
            'opponent_stat': opponent_stat
        }).reset_index()

        data = self.matches.merge(stat_df, on="match_id")
        data = data.sort_values('match_date')

        fig = self.plot_trendline(df=data, title_stat="xG", y_stat="Expected Goals (xG)", figsize=figsize)

        fig.savefig(
            f"{directory}/xg_trendline.png",
            facecolor=fig.get_facecolor(),
            dpi=Constants.DPI,
            bbox_inches="tight",
            pad_inches=Constants.PAD_INCHES
        )
        return fig

    def plot_obv_trendline(self, directory: str, figsize: tuple[int, int] = (16, 10)):
        stat_name = "obv_total_net"
        stat_df = self.matches_events[self.matches_events["type"].isin(["Pass", "Carry", "Dribble"])]
        stat = stat_df.groupby(["match_id", "team"])[stat_name].sum().to_frame().reset_index()
        # Pivot the table to separate xG values for 'Legia Warszawa' and their opponents
        team_stat = stat[stat['team'] == self.team_for].set_index('match_id')[stat_name]
        opponent_stat = stat[stat['team'] != self.team_for].set_index('match_id')[stat_name]

        # Combine into a new DataFrame
        stat_df = pd.DataFrame({
            'team_stat': team_stat,
            'opponent_stat': opponent_stat
        }).reset_index()

        data = self.matches.merge(stat_df, on="match_id")
        data = data.sort_values('match_date')

        fig = self.plot_trendline(df=data, title_stat="OBV from passes, carries and dribbles", y_stat="On-Ball Value (OBV)", figsize=figsize)

        fig.savefig(
            f"{directory}/obv_trendline.png",
            facecolor=fig.get_facecolor(),
            dpi=Constants.DPI,
            bbox_inches="tight",
            pad_inches=Constants.PAD_INCHES
        )
        return fig

    def plot_shots_trendline(self, directory: str, figsize: tuple[int, int] = (16, 10)):
        stat_df = self.matches_events[self.matches_events["type"].isin(["Shot"])]
        stat = stat_df.groupby(["match_id", "team"]).count().reset_index()
        # Pivot the table to separate xG values for 'Legia Warszawa' and their opponents
        team_stat = stat[stat['team'] == self.team_for].set_index('match_id')["index"]
        opponent_stat = stat[stat['team'] != self.team_for].set_index('match_id')["index"]

        # Combine into a new DataFrame
        stat_df = pd.DataFrame({
            'team_stat': team_stat,
            'opponent_stat': opponent_stat
        }).reset_index()

        data = self.matches.merge(stat_df, on="match_id")
        data = data.sort_values('match_date')

        fig = self.plot_trendline(df=data, title_stat="shots", y_stat="number of shots", figsize=figsize)

        fig.savefig(
            f"{directory}/shots_trendline.png",
            facecolor=fig.get_facecolor(),
            dpi=Constants.DPI,
            bbox_inches="tight",
            pad_inches=Constants.PAD_INCHES
        )
        return fig