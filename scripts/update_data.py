#!/usr/bin/env python3
"""
StatsBomb Data Fetcher - A tool to download and manage football match data from StatsBomb API.
"""

import argparse
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from statsbombpy import sb
from tqdm import tqdm

# Type aliases
PathLike = str | Path
DatetimeType = datetime | pd.Timestamp


@dataclass
class Credentials:
    """Credentials for StatsBomb API access."""

    user: str
    passwd: str

    def to_dict(self) -> dict[str, str]:
        """Convert credentials to dictionary format."""
        return {"user": self.user, "passwd": self.passwd}


class DataManager:
    """Manages data operations for StatsBomb match data."""

    def __init__(self, credentials: Credentials, data_directory: PathLike, max_concurrent: int = 5):
        self.credentials = credentials
        self.data_directory = Path(data_directory)
        self.data_directory.mkdir(parents=True, exist_ok=True)
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging with timestamp in filename."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        log_file = self.data_directory / f"statsbomb_fetcher_{timestamp}.log"

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def save_data(data: pd.DataFrame, path: PathLike) -> None:
        """Save DataFrame to pickle file."""
        data.to_pickle(path)

    @staticmethod
    def get_newest_datetime(row: pd.Series) -> pd.Timestamp | None:
        """Get the newest datetime from a match row."""
        if pd.isna(row["kick_off"]):
            row["kick_off"] = "00:00:00.000"

        match_datetime = pd.to_datetime(f"{row['match_date']} {row['kick_off']}", errors="coerce")
        last_updated = pd.to_datetime(row["last_updated"], errors="coerce")
        last_updated_360 = pd.to_datetime(row["last_updated_360"], errors="coerce")

        if row["match_status_360"] != "available":
            last_updated_360 = match_datetime

        return max(dt for dt in [match_datetime, last_updated, last_updated_360] if pd.notna(dt))

    def get_matches_list(self) -> pd.DataFrame:
        """Fetch list of all available matches."""
        self.logger.info("Fetching competitions list...")
        comps = list(
            sb.competitions(creds=self.credentials.to_dict())[["competition_id", "season_id"]].itertuples(
                index=False, name=None
            )
        )

        matches_list = []
        self.logger.info("Fetching matches for each competition...")
        for comp_id, season_id in tqdm(comps, desc="Fetching matches"):
            try:
                matches = sb.matches(competition_id=comp_id, season_id=season_id, creds=self.credentials.to_dict())
                matches = matches[matches["match_status"] == "available"]
                matches_list.append(matches)
            except Exception as e:
                self.logger.error(f"Error fetching matches for competition {comp_id}, season {season_id}: {e}")

        matches_df = pd.concat(matches_list)
        self.logger.info(f"Found {len(matches_df)} available matches")
        return matches_df

    def get_existing_data_info(self) -> dict[int, datetime]:
        """Get information about existing data files."""
        existing_data = {}
        for file_path in self.data_directory.glob("*.pkl"):
            try:
                match_id = int(file_path.stem.split("_")[0])
                mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                existing_data[match_id] = mod_time
            except (ValueError, IndexError) as e:
                self.logger.warning(f"Skipping invalid filename: {file_path} - {e}")
        return existing_data

    def get_data_to_download(self, matches_df: pd.DataFrame) -> pd.DataFrame:
        """Determine which matches need to be downloaded or updated."""
        self.logger.info("Analyzing matches for updates...")
        existing_data = self.get_existing_data_info()

        matches_df["newest_date"] = matches_df.apply(self.get_newest_datetime, axis=1)
        matches_df = matches_df[["match_id", "newest_date"]].copy()
        matches_df["file_date"] = matches_df["match_id"].map(existing_data.get)

        def is_file_up_to_date(row: pd.Series, time_interval: int = 0) -> bool:
            if pd.isna(row["file_date"]):
                return False
            time_difference = row["file_date"] - row["newest_date"]
            return time_difference > timedelta(hours=time_interval)

        matches_df["is_file_up_to_date"] = matches_df.apply(is_file_up_to_date, axis=1)
        to_download = matches_df[~matches_df["is_file_up_to_date"]].reset_index(drop=True)

        # Save to_download list with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        to_download.to_csv(self.data_directory / f"to_download_{timestamp}.tsv", sep="\t")

        self.logger.info(f"Found {len(to_download)} matches to download/update")
        return to_download

    async def fetch_match_data(self, match_id: int, progress_bar: tqdm) -> None:
        """Fetch and save data for a single match asynchronously."""
        try:
            async with self.semaphore:
                self.logger.info(f"Downloading match {match_id}")
                match_data = sb.events(match_id, creds=self.credentials.to_dict())
                filepath = self.data_directory / f"{match_id}_events.pkl"
                self.save_data(match_data, filepath)
                self.logger.info(f"Successfully saved match {match_id}")
                progress_bar.update(1)
        except Exception as e:
            self.logger.error(f"Error downloading match {match_id}: {e}")
            progress_bar.update(1)  # Still update progress even if there's an error

    async def download_matches(self, match_ids: list[int]) -> None:
        """Download multiple matches asynchronously."""
        self.logger.info("Starting async download of match data...")

        # Create progress bar before starting downloads
        with tqdm(total=len(match_ids), desc="Downloading matches") as pbar:
            tasks = [self.fetch_match_data(match_id, pbar) for match_id in match_ids]
            await asyncio.gather(*tasks)

    def process_all_matches(self) -> None:
        """Process all matches that need updating."""
        # Synchronous part
        matches_df = self.get_matches_list()
        to_download = self.get_data_to_download(matches_df)

        # Asynchronous download part
        if not to_download.empty:
            asyncio.run(self.download_matches(to_download["match_id"].tolist()))
        else:
            self.logger.info("No matches to download")


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Download and update StatsBomb match data.")
    parser.add_argument(
        "--data-dir",
        type=str,
        default="/Users/bartek/resources/data/match_events",
        help="Directory for storing match data",
    )
    parser.add_argument(
        "--user", type=str, default="bartkuzma@gmail.com", required=False, help="StatsBomb API username"
    )
    parser.add_argument("--passwd", type=str, default="v1x6CQUt", required=False, help="StatsBomb API password")
    parser.add_argument("--max-concurrent", type=int, default=10, help="Maximum number of concurrent downloads")

    args = parser.parse_args()

    credentials = Credentials(user=args.user, passwd=args.passwd)
    manager = DataManager(credentials=credentials, data_directory=args.data_dir, max_concurrent=args.max_concurrent)
    manager.process_all_matches()


if __name__ == "__main__":
    main()
