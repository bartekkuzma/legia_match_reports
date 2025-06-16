import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from statsbombpy import sb
from tqdm import tqdm

creds = {"user": "bartkuzma@gmail.com", "passwd": "v1x6CQUt"}


def save_data(data: pd.DataFrame, path_to_save: str) -> None:
    # Convert all columns that are lists or dicts to JSON strings
    data.to_pickle(path_to_save)


def get_newest_datetime(df: pd.DataFrame) -> pd.Timestamp | None:
    # Create a full datetime from match_date and kick_off
    if df["kick_off"] is np.NaN:
        df["kick_off"] = "00:00:00.000"
    df["match_datetime"] = pd.to_datetime(df["match_date"] + " " + df["kick_off"], errors="coerce")
    df["last_updated"] = pd.to_datetime(df["last_updated"], errors="coerce")
    df["last_updated_360"] = pd.to_datetime(df["last_updated_360"], errors="coerce")
    if df["match_status_360"] != "available":
        df["last_updated_360"] = df["match_datetime"]
    # Find the latest datetime across all specified columns
    newest_datetime = df[["match_datetime", "last_updated", "last_updated_360"]].max()

    return newest_datetime


def get_file_modification_date(file_path):
    if os.path.exists(file_path):
        return datetime.fromtimestamp(os.path.getmtime(file_path))


def is_file_up_to_date(newest_date, file_date, time_interval=0):
    if file_date is None:
        return False
    time_difference = file_date - newest_date
    return True if time_difference > timedelta(hours=time_interval) else False


def get_matches_list(creds):
    comps = list(sb.competitions(creds=creds)[["competition_id", "season_id"]].itertuples(index=False, name=None))
    matches_list = []
    for comp_id, season_id in tqdm(comps, total=len(comps)):
        matches = sb.matches(competition_id=comp_id, season_id=season_id, creds=creds)
        matches = matches[matches["match_status"] == "available"]
        matches_list.append(matches)
    matches_df = pd.concat(matches_list)
    matches_df.to_csv("matches.csv")
    return matches_df


def get_existing_data_info(directory):
    existing_data_list = os.listdir(directory)
    existing_data_list = [f for f in existing_data_list if ".pkl" in f]
    existing_data = {
        int(game.split("_")[0]): get_file_modification_date(os.path.join(directory, game))
        for game in existing_data_list
    }
    return existing_data


def get_data_to_download(all_games, existing_data):
    all_games["newest_date"] = all_games.apply(lambda x: get_newest_datetime(x), axis=1)
    all_games = all_games[["match_id", "newest_date"]].copy()
    all_games["file_date"] = all_games["match_id"].apply(lambda x: existing_data.get(x, None))
    all_games["is_file_up_to_date"] = all_games.apply(
        lambda x: is_file_up_to_date(x["newest_date"], x["file_date"]), axis=1
    )
    return all_games[all_games["is_file_up_to_date"] == False].reset_index(drop=True)


def get_data(creds=creds, directory="/Users/bartek/resources/data/match_events"):
    existing_data = get_existing_data_info(directory)
    all_games = pd.read_csv("matches.csv")  # get_matches_list(creds)

    to_download = get_data_to_download(all_games, existing_data)
    to_download.to_csv("test_to_download.tsv", sep="\t")

    for match_id in to_download:
        match_data = sb.events(match_id, creds=creds)
        filepath = os.path.join(directory, f"{match_id}_events.pkl")
        save_data(match_data, filepath)


if __name__ == "__main__":
    get_data()
