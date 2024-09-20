import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from mplsoccer import VerticalPitch

from constants import Constants


class ObvPitches:

    def __init__(self, match_events: pd.DataFrame, team_for: str) -> None:
        self.match_events = match_events
        self.team_for = team_for
        self.cmap = LinearSegmentedColormap.from_list("", Constants.CMAP_FOR_HEATMAP)

    def filter_obv_data(self) -> pd.DataFrame:
        obv_df = self.match_events.copy()
        obv_df.loc[:, 'x'] = obv_df['location'].str[0]
        obv_df.loc[:, 'y'] = obv_df['location'].str[1]
        obv_df = obv_df[(obv_df["type"].isin(["Pass", "Dribble", "Carry"])) & (obv_df["x"] >= 60)]
        return obv_df
    
    def create_heatmap(self, ax, data):
        pitch = VerticalPitch(pitch_type='statsbomb', pitch_color=Constants.COLORS["white"], line_color=Constants.COLORS["black"], line_zorder=2, half=True, goal_type='box')
        
        bin_statistic = pitch.bin_statistic_positional(data.x, data.y, statistic='sum', values=data.obv_total_net, positional='full', normalize=False)
        
        vmin, vmax = -0.3, 0.3  # Fixed scale for all heatmaps
        heatmap = pitch.heatmap_positional(bin_statistic, ax=ax, cmap=self.cmap, vmax=vmax, vmin=vmin)
        pitch.draw(ax=ax)
        pitch.label_heatmap(bin_statistic, ax=ax, str_format='{:.2f}', color=Constants.COLORS["black"], fontsize=8, va='center', ha='center')

        return heatmap[0]  # Return the first (and only) mappable object

    def plot_obv_heatmap(self, team_for: bool, directory: str, figsize: tuple[int, int] = (12, 8)) -> plt.Figure:
        obv_df = self.filter_obv_data()
        team_type = "for" if team_for else "against"
        team_data = obv_df[(obv_df["team"] == self.team_for) == team_for]
            
        fig, ax = plt.subplots(1, 1, figsize=figsize)
        title = self.team_for if team_for else "Opponent"
        heatmap = self.create_heatmap(ax, team_data)
        
        plt.colorbar(heatmap, ax=ax, label='OBV')
        plt.suptitle(f"{title}'s OBV from Passes, Carries & Dribbles", fontsize=20, fontweight="bold")
        plt.rcParams["text.color"] = Constants.TEXT_COLOR
        plt.rcParams["font.family"] = Constants.FONT
        
        fig.savefig(
            f"{directory}/obv_map_{team_type}.png",
            facecolor=fig.get_facecolor(),
            dpi=Constants.DPI,
            bbox_inches='tight', 
            pad_inches=Constants.PAD_INCHES
        )

        return fig
