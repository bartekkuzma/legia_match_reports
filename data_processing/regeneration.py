import os

import pandas as pd
from tqdm import tqdm

from data_processing.individual_stats import PlayerStatistics
from utils import ensure_player_directory, load_postions


def regenerate_data(
    players_list: list[dict[str, str]],
    available_matches: pd.DataFrame,
    all_matches_events: pd.DataFrame,
    team_name: str,
):
    players_positions = load_postions()
    team_stats = pd.DataFrame()
    gk_stats = pd.DataFrame()

    for player in tqdm(players_list, total=len(players_list)):
        position = players_positions[player]
        player_stats = PlayerStatistics.prepare_player_statistics(
            all_matches_events=all_matches_events,
            available_matches=available_matches,
            team_name=team_name,
            chosen_player=player,
            position=position,
        )
        if position != "Goalkeeper":
            team_stats = pd.concat([team_stats, player_stats])
        else:
            gk_stats = pd.concat([gk_stats, player_stats])

    team_directory = ensure_player_directory("Team")
    team_file_path = os.path.join(team_directory, f"Team_stats.tsv")
    team_gk_file_path = os.path.join(team_directory, f"Team_gk_stats.tsv")

    team_stats.to_csv(team_file_path, sep="\t", index=False)
    gk_stats.to_csv(team_gk_file_path, sep="\t", index=False)
