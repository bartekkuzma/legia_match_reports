import json
import os

import pandas as pd
from statsbombpy import sb


def save_data(data: pd.DataFrame, path_to_save: str) -> None:
    # Convert all columns that are lists or dicts to JSON strings
    data.to_pickle(path_to_save)

def get_data(match_id: str, data_type: str, creds: dict[str, str], directory: str = "data") -> pd.DataFrame:
    path_to_data = f"{directory}/{match_id}_{data_type}.pkl"
    if os.path.isfile(path_to_data):
        data = pd.read_pickle(path_to_data)
    else:
        data = sb.events(match_id=match_id, creds=creds, include_360_metrics=True) if data_type == "events" else sb.player_match_stats(match_id=match_id, creds=creds)
        save_data(data=data, path_to_save=path_to_data)
    data = replace_player_names(data)
    return data

def load_name_mappings(file_path: str) -> dict[str, str]:
    """Load player name mappings from a JSON file."""
    if file_path:
        with open(file_path, 'r') as f:
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