import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

from constants import Constants


class Top5Players:

    def __init__(self, match_events: pd.DataFrame, team_for: str) -> None:
        """
        Initialize the IndividualStats class.

        Args:
            match_events (pd.DataFrame): DataFrame containing data.
            team_for (str): The team to analyze.
        """
        self.match_events = match_events
        self.team_for = team_for

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

    def prepare_obv_gains_data(self) -> pd.DataFrame:
        obv_events = self.match_events[(self.match_events["team"] == self.team_for) & (self.match_events["type"].isin(["Pass", "Carry", "Dribble"]))].copy()
        obv_events.loc[obv_events["type"] == "Pass", "pass_outcome"] = obv_events.loc[obv_events["type"] == "Pass", "pass_outcome"].fillna("Complete")
        obv_events = obv_events.loc[((obv_events["type"] == "Pass") & (obv_events["pass_outcome"] == "Complete")) | ((obv_events["type"] == "Dribble") & (obv_events["dribble_outcome"] == "Complete")) | ((obv_events["type"] == "Carry"))]

        # Assume obv_events is your DataFrame with the relevant columns
        grouped_obv_data = obv_events.groupby(["player", "type"])

        # Step 1: Aggregate data by player and type
        stats_per_player = grouped_obv_data.agg(
            number_of_actions=('id', 'size'),
            sum_obv=('obv_for_net', 'sum'),
            mean_obv_per_action=('obv_for_net', 'mean')
        ).reset_index()

        # Step 2: Aggregate to get total actions and obv, and add conditional sums
        aggregated_df = stats_per_player.groupby('player').agg(
            total_number_of_actions=('number_of_actions', 'sum'),
            total_sum_obv=('sum_obv', 'sum'),
            sum_obv_from_pass=('sum_obv', lambda x: x[stats_per_player['type'] == 'Pass'].sum()),
            sum_obv_from_carry=('sum_obv', lambda x: x[stats_per_player['type'] == 'Carry'].sum()),
            sum_obv_from_dribble=('sum_obv', lambda x: x[stats_per_player['type'] == 'Dribble'].sum())
        ).reset_index()

        # Step 3: Calculate the mean OBV per action
        aggregated_df['mean_obv_per_action'] = aggregated_df['total_sum_obv'] / aggregated_df['total_number_of_actions']
        aggregated_df["total_sum_obv"] = aggregated_df["total_sum_obv"].round(2)
        aggregated_df["sum_obv_from_pass"] = aggregated_df["sum_obv_from_pass"].round(2)
        aggregated_df["sum_obv_from_carry"] = aggregated_df["sum_obv_from_carry"].round(2)
        aggregated_df["sum_obv_from_dribble"] = aggregated_df["sum_obv_from_dribble"].round(2)

        aggregated_df["sum_obv_from_pass"] = aggregated_df["sum_obv_from_pass"].apply(lambda x: x if x >= 0 else 0)
        aggregated_df["sum_obv_from_carry"] = aggregated_df["sum_obv_from_carry"].apply(lambda x: x if x >= 0 else 0)
        aggregated_df["sum_obv_from_dribble"] = aggregated_df["sum_obv_from_dribble"].apply(lambda x: x if x >= 0 else 0)

        return aggregated_df
    
    def plot_obv_gain(self, directory: str, figsize: tuple[int, int] = (12, 8)) -> plt.Figure:

        aggregated_df = self.prepare_obv_gains_data()

        # def threat_creators(ax):
        top5_obv = aggregated_df.nlargest(5, 'total_sum_obv')['player'].tolist()

        obv_pass = aggregated_df.nlargest(5, 'total_sum_obv')['sum_obv_from_pass'].tolist()
        obv_carry = aggregated_df.nlargest(5, 'total_sum_obv')['sum_obv_from_carry'].tolist()
        obv_dribble = aggregated_df.nlargest(5, 'total_sum_obv')['sum_obv_from_dribble'].tolist()

        left1 = [w + x for w, x in zip(obv_pass, obv_carry)]
        fig, ax = plt.subplots(figsize=figsize)
        plt.gca().invert_yaxis()
        ax.barh(top5_obv, obv_pass, label='Pass OBV', color=Constants.COLORS["green"], left=0)
        ax.barh(top5_obv, obv_carry, label='Carry OBV', color=Constants.COLORS["blue"], left=obv_pass)
        ax.barh(top5_obv, obv_dribble, label='Dribble OBV', color=Constants.COLORS["red"], left=left1)

        # Add counts in the middle of the bars (if count > 0)
        for i, player in enumerate(top5_obv):
            for j, count in enumerate([obv_pass[i], obv_carry[i], obv_dribble[i]]):
                if count > 0:
                    x_position = sum([obv_pass[i], obv_carry[i], obv_dribble[i]][:j]) + count / 2
                    ax.text(x_position, i, str(count), ha='center', va='center', color=Constants.COLORS["white"], fontsize=20, rotation=30, fontweight='bold')

        ax.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
        fig.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
        ax.tick_params(axis='x', colors=Constants.COLORS["white"], labelsize=18)
        ax.tick_params(axis='y', colors=Constants.COLORS["white"], labelsize=18, pad=20)
        ax.xaxis.label.set_color(Constants.COLORS["white"])
        ax.yaxis.label.set_color(Constants.COLORS["white"])
        for spine in ax.spines.values():
            spine.set_edgecolor(Constants.DARK_BACKGROUND_COLOR)


        ax.set_title(f"Top 5 for On-ball Value gain \nthrough passed, carries and dribbles", color=Constants.COLORS["white"], fontsize=24, fontweight='bold')
        ax.legend(fontsize=18)
        plt.rcParams["font.family"] = Constants.FONT

        fig.savefig(
            f"{directory}/top_5_obv.png",
            facecolor=fig.get_facecolor(),
            dpi=Constants.DPI,
            bbox_inches='tight', 
            pad_inches=Constants.PAD_INCHES
        )

        return fig
    
    def prepare_progressions_data(self) -> pd.DataFrame:
        progressions = self.match_events.loc[(self.match_events["team"] == self.team_for) & (self.match_events["type"].isin(["Pass", "Carry"]))]
        progressions.loc[progressions["type"] == "Pass", "pass_outcome"] = progressions.loc[progressions["type"] == "Pass", "pass_outcome"].fillna("Complete")
        progressions = progressions.loc[((progressions["type"] == "Pass") & (progressions["pass_outcome"] == "Complete")) | ((progressions["type"] == "Carry"))]
        progressions["was_progressive"] = progressions.apply(lambda x: self.prog_pass_carry(x), axis=1)
        progressions = progressions[progressions["was_progressive"] == 1]

        prog_grouped_data = progressions.groupby(["player", "type"])
        prog_stats_per_player = prog_grouped_data.agg(
            number_of_actions=('id', 'size')
        ).reset_index()

        # Step 1: Group by player and calculate the sum of all defensive actions
        prog_total_actions_per_player = prog_stats_per_player.groupby('player').agg(
            total_number_of_actions=('number_of_actions', 'sum')
        ).reset_index()
        # Step 2: Pivot the DataFrame to get separate columns for each action type
        prog_pivot_df = prog_stats_per_player.pivot(index='player', columns='type', values='number_of_actions').fillna(0).reset_index()
        # Step 3: Merge the total actions DataFrame with the pivoted DataFrame
        prog_final_df = pd.merge(prog_total_actions_per_player, prog_pivot_df, on='player')
        prog_final_df = prog_final_df.astype(int, errors="ignore")

        return prog_final_df

    def plot_progressions(self, directory: str, figsize: tuple[int, int] = (12, 8)) -> plt.Figure:
        
        prog_final_df = self.prepare_progressions_data()
    
        # def threat_creators(ax):
        top5 = prog_final_df.nlargest(5, 'total_number_of_actions')['player'].tolist()

        passes = prog_final_df.nlargest(5, 'total_number_of_actions')['Pass'].tolist()
        carries = prog_final_df.nlargest(5, 'total_number_of_actions')['Carry'].tolist()


        fig, ax = plt.subplots(figsize=figsize)
        plt.gca().invert_yaxis()
        ax.barh(top5, passes, label='Passes', color=Constants.COLORS["green"], left=0)
        ax.barh(top5, carries, label='Carries', color=Constants.COLORS["blue"], left=passes)

        # Add counts in the middle of the bars (if count > 0)
        for i, player in enumerate(top5):
            for j, count in enumerate([passes[i], carries[i]]):
                if count > 0:
                    x_position = sum([passes[i], carries[i]][:j]) + count / 2
                    ax.text(x_position, i, str(count), ha='center', va='center', color=Constants.COLORS["white"], fontsize=20, rotation=0, fontweight='bold')

        ax.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
        fig.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
        ax.tick_params(axis='x', colors=Constants.COLORS["white"], labelsize=18)
        ax.tick_params(axis='y', colors=Constants.COLORS["white"], labelsize=18, pad=20)
        ax.xaxis.label.set_color(Constants.COLORS["white"])
        ax.yaxis.label.set_color(Constants.COLORS["white"])
        for spine in ax.spines.values():
            spine.set_edgecolor(Constants.DARK_BACKGROUND_COLOR)

        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{int(x)}'))
        ax.set_title(f"Top 5 for progressive\npasses and carries", color=Constants.COLORS["white"], fontsize=24, fontweight='bold')
        ax.legend(fontsize=18)
        plt.rcParams["font.family"] = Constants.FONT

        fig.savefig(
            f"{directory}/top_5_progressors.png",
            facecolor=fig.get_facecolor(),
            dpi=Constants.DPI,
            bbox_inches='tight', 
            pad_inches=Constants.PAD_INCHES
        )

        return fig
    
    def prepare_defensive_data(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        def_1_events = self.match_events.loc[(self.match_events["team"] == self.team_for) & (self.match_events["type"].isin(["Ball Recovery", "Block", "Interception", "Clearance"]))]
        def_1_grouped_data = def_1_events.groupby(["player", "type"])
        def_1_stats_per_player = def_1_grouped_data.agg(
            number_of_actions=('id', 'size')
        ).reset_index()

        # Step 1: Group by player and calculate the sum of all defensive actions
        def_1_total_actions_per_player = def_1_stats_per_player.groupby('player').agg(
            total_number_of_actions=('number_of_actions', 'sum')
        ).reset_index()
        # Step 2: Pivot the DataFrame to get separate columns for each action type
        def_1_pivot_df = def_1_stats_per_player.pivot(index='player', columns='type', values='number_of_actions').fillna(0).reset_index()
        # Step 3: Merge the total actions DataFrame with the pivoted DataFrame
        def_1_final_df = pd.merge(def_1_total_actions_per_player, def_1_pivot_df, on='player')
        def_1_final_df = def_1_final_df.astype(int, errors="ignore")


        def_2_events = self.match_events.loc[(self.match_events["team"] == self.team_for) & (self.match_events["type"].isin(["Foul Committed", "Pressure"]))]
        def_2_grouped_data = def_2_events.groupby(["player", "type"])
        def_2_stats_per_player = def_2_grouped_data.agg(
            number_of_actions=('id', 'size')
        ).reset_index()

        # Step 1: Group by player and calculate the sum of all defensive actions
        def_2_total_actions_per_player = def_2_stats_per_player.groupby('player').agg(
            total_number_of_actions=('number_of_actions', 'sum')
        ).reset_index()
        # Step 2: Pivot the DataFrame to get separate columns for each action type
        def_2_pivot_df = def_2_stats_per_player.pivot(index='player', columns='type', values='number_of_actions').fillna(0).reset_index()
        # Step 3: Merge the total actions DataFrame with the pivoted DataFrame
        def_2_final_df = pd.merge(def_2_total_actions_per_player, def_2_pivot_df, on='player')
        def_2_final_df = def_2_final_df.astype(int, errors="ignore")
    
        return def_1_final_df, def_2_final_df
    
    def plot_defensive_1(self, directory: str, figsize: tuple[int, int] = (12, 8)) -> plt.Figure:
        # def threat_creators(ax):
        def_1_final_df, _ = self.prepare_defensive_data()
        top5_def = def_1_final_df.nlargest(5, 'total_number_of_actions')['player'].tolist()

        recovery = def_1_final_df.nlargest(5, 'total_number_of_actions')['Ball Recovery'].tolist()
        block = def_1_final_df.nlargest(5, 'total_number_of_actions')['Block'].tolist()
        clearance = def_1_final_df.nlargest(5, 'total_number_of_actions')['Clearance'].tolist()
        interception = def_1_final_df.nlargest(5, 'total_number_of_actions')['Interception'].tolist()


        left1 = [w + x for w, x in zip(recovery, interception)]
        left2 = [w + x + z for w, x, z in zip(recovery, interception, clearance)]


        fig, ax = plt.subplots(figsize=figsize)
        plt.gca().invert_yaxis()
        ax.barh(top5_def, recovery, label='Recoveries', color=Constants.COLORS["green"], left=0)
        ax.barh(top5_def, interception, label='Interceptions', color=Constants.COLORS["blue"], left=recovery)
        ax.barh(top5_def, clearance, label='Clearances', color=Constants.COLORS["red"], left=left1)
        ax.barh(top5_def, block, label='Blocks', color=Constants.COLORS["yellow"], left=left2)

        # Add counts in the middle of the bars (if count > 0)
        for i, player in enumerate(top5_def):
            for j, count in enumerate([recovery[i], interception[i], clearance[i], block[i]]):
                if count > 0:
                    x_position = sum([recovery[i], interception[i], clearance[i], block[i]][:j]) + count / 2
                    ax.text(x_position, i, str(count), ha='center', va='center', color=Constants.COLORS["white"], fontsize=20, rotation=0, fontweight='bold')

        ax.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
        fig.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
        ax.tick_params(axis='x', colors=Constants.COLORS["white"], labelsize=18)
        ax.tick_params(axis='y', colors=Constants.COLORS["white"], labelsize=18, pad=20)
        ax.xaxis.label.set_color(Constants.COLORS["white"])
        ax.yaxis.label.set_color(Constants.COLORS["white"])
        for spine in ax.spines.values():
            spine.set_edgecolor(Constants.DARK_BACKGROUND_COLOR)

        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{int(x)}'))
        ax.set_title(f"Top 5 for defensive actions \nrecovery, interception, clearence and block", color=Constants.COLORS["white"], fontsize=24, fontweight='bold')
        ax.legend(fontsize=18, loc="lower right")
        plt.rcParams["font.family"] = Constants.FONT

        fig.savefig(
            f"{directory}/top_5_def_1.png",
            facecolor=fig.get_facecolor(),
            dpi=Constants.DPI,
            bbox_inches='tight', 
            pad_inches=Constants.PAD_INCHES
        )

        return fig


    
    def plot_defensive_2(self, directory: str, figsize: tuple[int, int] = (12, 8)) -> plt.Figure:
        _, def_2_final_df = self.prepare_defensive_data()
        # def threat_creators(ax):
        top5_def = def_2_final_df.nlargest(5, 'total_number_of_actions')['player'].tolist()

        pressure = def_2_final_df.nlargest(5, 'total_number_of_actions')['Pressure'].tolist()
        fouls = def_2_final_df.nlargest(5, 'total_number_of_actions')['Foul Committed'].tolist()


        fig, ax = plt.subplots(figsize=figsize)
        plt.gca().invert_yaxis()
        ax.barh(top5_def, pressure, label='Pressures', color=Constants.COLORS["green"], left=0)
        ax.barh(top5_def, fouls, label='Fouls Commited', color=Constants.COLORS["blue"], left=pressure)

        # Add counts in the middle of the bars (if count > 0)
        for i, player in enumerate(top5_def):
            for j, count in enumerate([pressure[i], fouls[i]]):
                if count > 0:
                    x_position = sum([pressure[i], fouls[i]][:j]) + count / 2
                    ax.text(x_position, i, str(count), ha='center', va='center', color=Constants.COLORS["white"], fontsize=20, rotation=0, fontweight='bold')

                        
                
        ax.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
        fig.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
        ax.tick_params(axis='x', colors=Constants.COLORS["white"], labelsize=18)
        ax.tick_params(axis='y', colors=Constants.COLORS["white"], labelsize=18, pad=20)
        ax.xaxis.label.set_color(Constants.COLORS["white"])
        ax.yaxis.label.set_color(Constants.COLORS["white"])
        for spine in ax.spines.values():
            spine.set_edgecolor(Constants.DARK_BACKGROUND_COLOR)

        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{int(x)}'))
        ax.set_title(f"Top 5 for defensive actions \npressures and fouls commited", color=Constants.COLORS["white"], fontsize=24, fontweight='bold')
        ax.legend(fontsize=18, loc="lower right")
        plt.rcParams["font.family"] = Constants.FONT

        fig.savefig(
            f"{directory}/top_5_def_2.png",
            facecolor=fig.get_facecolor(),
            dpi=Constants.DPI,
            bbox_inches='tight', 
            pad_inches=Constants.PAD_INCHES
        )
        
        return fig