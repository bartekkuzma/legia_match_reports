import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsbombpy import sb

from constants import Constants


class BenchmarkChart:

    def __init__(self, matches: pd.DataFrame, game_id: int, team_for: str, team_against: str, creds: dict[str, str]) -> None:
        self.matches = matches
        self.game_id = game_id
        self.team_for = team_for
        self.team_against = team_against
        self.creds = creds

        
    def get_team_data(self, team):
        # set function to loop through and get season data for home and away team
        team_matches = self.matches[(self.matches['home_team'] == team) | (self.matches['away_team'] == team)]
        team_matches = team_matches[team_matches["match_status"] == "available"]

        list_matches = team_matches.match_id.tolist()
        
        df = []
        for n in list_matches:
            match_events = sb.events(match_id = n, include_360_metrics=True, creds=self.creds)
            teams = list(match_events["team"].unique())
            teams.remove(team)
            match_events["opposiiton"] = np.where(match_events["team"] == team, teams[0], team)
            df.append(match_events)
        df = pd.concat(df)
        
        df[['x', 'y', 'z']] = df['location'].apply(pd.Series)
        df[['pass_end_x', 'pass_end_y']] = df['pass_end_location'].apply(pd.Series)
        df[['carry_end_x', 'carry_end_y']] = df['carry_end_location'].apply(pd.Series)
        
        return df
    
    @staticmethod
    def group_by_count(count_df):
        #set funciton to get count of actions on a game by game basis
        count_data = count_df.groupby(['team', 'match_id']).size().reset_index()
        count_data.rename(columns={count_data.columns[2]: "value" }, inplace = True)
        count_data["plot"] = (count_data["value"] - count_data["value"].mean()) / count_data["value"].std()
        return (count_data)

    @staticmethod
    def group_by_metric(metric_df, metric):
        #set function to get cumulative total of advanced metrics such as xG and OBV
        metric_data = metric_df.groupby(['team', 'match_id']).agg({metric: ['sum']})
        metric_data.columns = metric_data.columns.droplevel()
        metric_data = metric_data.reset_index()
        metric_data.rename(columns={metric_data.columns[2]: "value" }, inplace = True)
        metric_data["plot"] = (metric_data["value"] - metric_data["value"].mean()) / metric_data["value"].std()
        return (metric_data)
    
    def plot_variable(self, team, plot_data, y_value, ax):
        # set function for plotting the variable
        conditions = [plot_data["match_id"] == self.game_id, plot_data["match_id"] != self.game_id]
        # opacity
        values = [1, 0.2]
        plot_data["alpha"] = np.select(conditions, values)
        # edge color
        if team == self.team_for:
            values = [Constants.TEAM_AGAINST_COLOR, Constants.TEAM_FOR_COLOR]
        else:
            values = [Constants.TEAM_FOR_COLOR, Constants.TEAM_AGAINST_COLOR]
        plot_data["ec"] = np.select(conditions, values)
        # fill color
        if team == self.team_for:
            values = [Constants.TEAM_FOR_COLOR, Constants.TEAM_AGAINST_COLOR]
        else:
            values = [Constants.TEAM_AGAINST_COLOR, Constants.TEAM_FOR_COLOR]
        plot_data["color"] = np.select(conditions, values)
        # size
        values = [5000, 500]
        plot_data["size"] = np.select(conditions, values)
        x = plot_data["plot"]
        y = pd.Series([y_value]).repeat(len(plot_data))
        ax.scatter(x, y, s=plot_data["size"], alpha=plot_data["alpha"], c=plot_data["color"], ec=plot_data["ec"],
                   lw=5, zorder=10)
        text_df = plot_data[plot_data["match_id"] == self.game_id]
        text = round(text_df.iloc[0]["value"], 2)
        x_pos = text_df.iloc[0]["plot"]

        ax.annotate(text, (x_pos, y_value - 0.05), c=Constants.COLORS["white"], fontsize=22, fontweight="bold",
                    zorder=11, ha="center")
        
    def plot_team_data(self, team, df, ax):
        # set function for plotting a team's data
        
        # cut df to shots for
        shots = df[df["type"] == "Shot"]
        shots = shots[shots["shot_type"] != "Penalty"]
        shots_for = shots[shots["team"] == team]
        shots_df = self.group_by_count(shots_for)

        # group data and calculate xg for sum
        xg_for = self.group_by_metric(shots_for, "shot_statsbomb_xg")

        # cut dataframe to shots against
        shots_against = shots[shots["team"] != team]
        shots_against_df = self.group_by_count(shots_against)
        # invert plot figures
        shots_against_df["plot"] = shots_against_df["plot"] * -1

        # xg against sum
        xg_against = self.group_by_metric(shots_against, "shot_statsbomb_xg")
        xg_against["plot"] = xg_against["plot"] * -1

        # cut df to completed passes for
        pass_for = df[df["type"] == "Pass"]
        pass_for = pass_for[pass_for["team"] == team]
        total_suc_passes = pass_for[pass_for["pass_outcome"].isnull()]
        pass_df = self.group_by_count(total_suc_passes)

        # pass obv total
        pass_obv_for = self.group_by_metric(pass_for, "obv_total_net")

        # box entries
        box_line = Constants.PITCH_DIMS["pitch_length"] - Constants.PITCH_DIMS["penalty_box_length"]
        box_left = Constants.PITCH_DIMS["penalty_box_left_band"]
        box_right = Constants.PITCH_DIMS["pitch_width"] - Constants.PITCH_DIMS["penalty_box_left_band"]
        box_entries = df[(df["type"] == "Pass") | (df["type"] == "Carry")]
        box_entries = box_entries[box_entries["team"] == team]
        box_entries = box_entries[box_entries['pass_type'].isnull()]
        box_entries = box_entries.drop(
            box_entries[
                ((box_entries['y'] <= box_right) & (box_entries['y'] >= box_left)) 
                & ((box_entries['x'] >= box_line))].index,axis=0)
        box_entries = box_entries[(box_entries['pass_end_x'] >= box_line) | (box_entries['carry_end_x'] >= box_line)]
        box_entries = box_entries[(box_entries['pass_end_y'] >= box_left) | (box_entries['carry_end_y'] >= box_left)]
        box_entries = box_entries[(box_entries['pass_end_y'] <= box_right) | (box_entries['carry_end_y'] <= box_right)]
        box_entries = box_entries[box_entries['pass_outcome'].isnull()]
        box_entry_df = self.group_by_count(box_entries)

        # pressures
        pressures = df[df["type"] == "Pressure"]
        pressures = pressures[pressures["team"] == team]
        pressures_df = self.group_by_count(pressures)

        # carries
        carries_for = df[(df["type"] == "Carry") | (df["type"] == "Dribble")]
        carries_for = carries_for[carries_for["team"] == team]
        carry_obv_for = self.group_by_metric(carries_for, "obv_total_net")


        # plot variables
        self.plot_variable(team=team, plot_data=pressures_df, y_value=0, ax=ax)
        self.plot_variable(team=team, plot_data=box_entry_df, y_value=1, ax=ax)
        self.plot_variable(team=team, plot_data=pass_df, y_value=2, ax=ax)
        self.plot_variable(team=team, plot_data=pass_obv_for, y_value=3, ax=ax)
        self.plot_variable(team=team, plot_data=carry_obv_for, y_value=4, ax=ax)
        self.plot_variable(team=team, plot_data=shots_against_df, y_value=5, ax=ax)
        self.plot_variable(team=team, plot_data=shots_df, y_value=6, ax=ax)
        self.plot_variable(team=team, plot_data=xg_against, y_value=7, ax=ax)
        self.plot_variable(team=team, plot_data=xg_for, y_value=8, ax=ax)

        # set labels for axis, should be the same order as above
        y_labels = ["Pressures","Box Entries","Completed Passes","Pass OBV",
                   "D&C OBV","Shots Conceded","Shots For","NPxG Conceded","NPxG For"]
        y_ticks=list(range(0, len(y_labels)))

        # plot line for average
        ax.axvline(x=0, c=Constants.COLORS["black"], ls="--", lw=5)
        ax.text(s="season average", x=0, y=-0.75, fontsize=28, ha="center")
        # set team name as subplot title
        ax.set_title(label=f"{team}", y=1.05, fontsize=40, fontweight="bold")

        ax.set_yticks(y_ticks)

        # plot labels only once
        if team == self.team_for:
            ax.set_yticklabels(y_labels, fontsize=36)
        else:
            ax.set_yticklabels([], fontsize=36)
        
        for i in range(0, len(y_labels)):
            ax.axhline(y=i, lw=3, c=Constants.COLORS["sb_grey"], alpha=0.5)
        
        for i in (["right","top","left","bottom"]):
            ax.spines[i].set_visible(False)
        ax.set_xlim(-3, 3)

    def plot_benchmark(self, directory: str, figsize: tuple[int, int] = (40, 20)) -> plt.Figure:
        #get season long data for the team
        df_for = self.get_team_data(self.team_for)
        #get season long data for the opposition team
        df_against = self.get_team_data(self.team_against)


        #set details of plot
        fig = plt.figure(figsize=figsize, constrained_layout=True)
        gs = fig.add_gridspec(nrows=1, ncols=2)
        fig.patch.set_facecolor(Constants.COLORS["white"])

        #subplot for the team
        ax1 = fig.add_subplot(gs[0])
        self.plot_team_data(self.team_for, df_for, ax1)
        #subplot for the opposition team
        ax2 = fig.add_subplot(gs[1])
        self.plot_team_data(self.team_against, df_against, ax2)

        fig.text(s=f"Single game data points benchmarked against season averages using z-score calculations",
         x=0.075, y =-0.05, fontsize=32)
        
        fig.savefig(
            f"{directory}/match_benchmark.png",
            facecolor=fig.get_facecolor(),
            dpi=Constants.DPI,
            bbox_inches='tight', 
            pad_inches=Constants.PAD_INCHES
        )

        return fig