import json
import os
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
from statsbombpy import sb


def save_data(data: pd.DataFrame, path_to_save: str) -> None:
    # Convert all columns that are lists or dicts to JSON strings
    data.to_pickle(path_to_save)


def get_data(
    match_id: str,
    data_type: str,
    creds: dict[str, str],
    directory: str = "data",
    force_redownload: bool = False,
) -> pd.DataFrame:
    path_to_data = f"{directory}/{match_id}_{data_type}.pkl"
    if not os.path.isfile(path_to_data) or force_redownload:
        data = (
            sb.events(match_id=match_id, creds=creds, include_360_metrics=True)
            if data_type == "events"
            else sb.player_match_stats(match_id=match_id, creds=creds)
        )
        save_data(data=data, path_to_save=path_to_data)
    else:
        data = pd.read_pickle(path_to_data)
    data = replace_player_names(data)
    return data


def load_name_mappings(file_path: str) -> dict[str, str]:
    """Load player name mappings from a JSON file."""
    if file_path:
        with open(file_path, "r") as f:
            return json.load(f)


def replace_player_names(data: pd.DataFrame) -> pd.DataFrame:
    """Replace full player names with shorter versions in the given data."""
    name_mappings = load_name_mappings("resources/name_mappings.json")
    for full_name, short_name in name_mappings.items():
        data = data.replace(full_name, short_name)
    return data


def unpack_coordinates(loc, expected_len):
    """
    Unpack coordinates from a list or tuple, handling missing values.

    Args:
        loc (list or tuple): The coordinate list/tuple to unpack.
        expected_len (int): The expected number of values (e.g., 2 for [x, y], 3 for [x, y, z]).

    Returns:
        tuple: A tuple with length `expected_len`, filled with None for missing values.
    """
    if isinstance(loc, (list, tuple)):
        loc = list(loc)  # Convert tuple to list to handle slicing and padding
        return tuple(loc[:expected_len] + [None] * (expected_len - len(loc)))
    return tuple([None] * expected_len)


def get_credentials():
    return {"user": st.secrets["user"], "passwd": st.secrets["password"]}


def calculate_match_statistics(matches, team_name):
    matches.loc[:, "goals_scored"] = matches.apply(
        lambda row: (row["home_score"] if row["home_team"] == team_name else row["away_score"]),
        axis=1,
    ).astype(int)
    matches.loc[:, "goals_conceded"] = matches.apply(
        lambda row: (row["away_score"] if row["home_team"] == team_name else row["home_score"]),
        axis=1,
    ).astype(int)
    matches.loc[:, "match_result"] = matches.apply(
        lambda row: (
            "Won"
            if row["goals_scored"] > row["goals_conceded"]
            else ("Draw" if row["goals_scored"] == row["goals_conceded"] else "Lost")
        ),
        axis=1,
    )
    matches.loc[:, "opponent"] = matches.apply(
        lambda row: (row["away_team"] if row["home_team"] == team_name else row["home_team"]),
        axis=1,
    )
    matches = (
        matches[
            [
                "match_id",
                "match_date",
                "kick_off",
                "competition",
                "goals_scored",
                "goals_conceded",
                "match_result",
                "opponent",
                "match_status_360",
                "last_updated",
                "last_updated_360",
            ]
        ]
        .sort_values("match_date")
        .reset_index(drop=True)
    )
    return matches


def load_matches(team_name, season_id, competitions, creds):
    matches = pd.DataFrame()
    for comp_id in competitions:
        comp_matches = sb.matches(competition_id=comp_id, season_id=season_id, creds=creds)
        matches = pd.concat([matches, comp_matches])
    available_matches = matches[
        ((matches["home_team"] == team_name) | (matches["away_team"] == team_name))
        & (matches["match_status"] == "available")
    ].copy()
    return available_matches


def load_all_match_events(available_matches, creds):
    all_matches_events = pd.DataFrame()
    for match in available_matches.to_dict(orient="records"):
        match_id = match["match_id"]
        events = get_data(match_id=match_id, data_type="events", creds=creds)
        all_matches_events = pd.concat([all_matches_events, events])
    all_matches_events = all_matches_events.sort_values(["match_id", "index"]).reset_index(drop=True)
    return all_matches_events


def ensure_player_directory(chosen_player):
    directory = f"players/{chosen_player}"
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


def save_players_list(players, file_path):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(players, file, ensure_ascii=False, indent=4)


def load_players_list(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_file_modification_date(file_path):
    if os.path.exists(file_path):
        return datetime.fromtimestamp(os.path.getmtime(file_path))


def is_file_up_to_date(file_path, date_to_check, time_interval=0):
    if not os.path.exists(file_path) or not date_to_check:
        return False
    time_difference = get_file_modification_date(file_path=file_path) - date_to_check
    return True if time_difference > timedelta(hours=time_interval) else False


def get_players_list(
    all_matches_events,
    available_matches,
    team_name,
    file_path="resources/players_list.json",
):
    """
    Retrieves a sorted list of players for a given team. If a saved players list file exists and is
    up-to-date based on the latest match date in available_matches, the list is loaded from the file.
    Otherwise, it regenerates the list and saves it to the file.

    Args:
        all_matches_events (pd.DataFrame): DataFrame containing events for all matches.
        available_matches (pd.DataFrame): DataFrame containing information about available matches.
        team_name (str): Name of the team to filter players for.
        file_path (str): Path to the file where the players list is saved.

    Returns:
        dict: Dictionary of players with sorted list of unique match IDs by match date.
    """

    # Get the latest match date from the available matches
    last_match_update_date = get_newest_datetime(available_matches)
    # Check if the file exists and is up-to-date
    if is_file_up_to_date(file_path, last_match_update_date):
        # Load players list from the file
        players = load_players_list(file_path)
    else:
        # Initialize an empty dictionary to store each player's available matches
        players = {}

        # Merge event data with match dates from available_matches
        events_with_dates = all_matches_events.merge(
            available_matches[["match_id", "match_date"]], on="match_id", how="left"
        )

        # Get unique players for the specified team, filtering out invalid (non-string) entries
        team_players = [
            player
            for player in events_with_dates[events_with_dates["team"] == team_name]["player"].unique()
            if isinstance(player, str)
        ]

        # Sort the valid player names
        team_players = sorted(team_players)

        # Loop through each player in the team
        for player in team_players:
            # Filter events for the specific player and team, and sort by match_date
            player_events = events_with_dates[
                (events_with_dates["team"] == team_name) & (events_with_dates["player"] == player)
            ].sort_values(by="match_date")

            # Get sorted match IDs
            valid_matches = [int(match_id) for match_id in player_events["match_id"].unique()]

            # Add the player and their valid match list to the dictionary
            players[player] = {"available_matches": valid_matches}

        # Save the updated players list to the file
        save_players_list(players, file_path)

    return players


# Load metrics and weights from JSON file
def load_metrics(filename):
    filepath = f"resources/metric_weights/{filename}.json"
    with open(filepath, "r") as f:
        return json.load(f)


def load_all_metrics(filename="resources/metrics.json"):
    with open(filename, "r") as f:
        return json.load(f)


def load_all_gk_metrics(filename="resources/gk_metrics.json"):
    with open(filename, "r") as f:
        return json.load(f)


# Load positions from JSON file
def load_postions(filename="resources/players_positions.json"):
    with open(filename, "r") as f:
        return json.load(f)


# Save metrics and weights to a new JSON file with a timestamp
def save_metrics(data, filename_prefix="resources/metric_weights/metrics_weights"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.json"
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


def get_newest_datetime(df: pd.DataFrame) -> pd.Timestamp | None:
    """
    Finds the latest datetime value across 'match_date' + 'kick_off', 'last_updated', and 'last_updated_360' columns.
    Handles None values in these columns.

    Parameters:
    df (pd.DataFrame): DataFrame containing columns 'match_date', 'kick_off', 'last_updated', and 'last_updated_360'.

    Returns:
    pd.Timestamp | None: The newest datetime value across all rows, or None if all are missing.
    """
    # Create a full datetime from match_date and kick_off
    df["match_datetime"] = pd.to_datetime(df["match_date"] + " " + df["kick_off"], errors="coerce")
    df["last_updated"] = pd.to_datetime(df["last_updated"], errors="coerce")
    df["last_updated_360"] = pd.to_datetime(df["last_updated_360"], errors="coerce")

    # Find the latest datetime across all specified columns
    newest_datetime = df[["match_datetime", "last_updated", "last_updated_360"]].max().max()

    return newest_datetime


def clean_weights(weights_dict):
    """Remove metrics with zero weights and renormalize remaining weights."""
    # Remove zero weights
    cleaned_weights = {k: round(v, 4) for k, v in weights_dict.items() if v > 0}

    # Renormalize remaining weights
    total = sum(cleaned_weights.values())
    if total > 0:  # Avoid division by zero
        cleaned_weights = {k: v / total for k, v in cleaned_weights.items()}

    return cleaned_weights
