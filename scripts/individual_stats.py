from pathlib import Path

import pandas as pd

from scripts.individual_stats_shots import Shots

PathLike = str | Path


class IndividualStats:

    def __init__(
        self,
        match_id: int,
        input_path: PathLike = "/Users/bartek/resources/data/match_events",
        output_path: PathLike = "/Users/bartek/resources/data/individual_stats",
    ):
        self.data = self.load_match_data(match_id=match_id, input_path=input_path)

    def load_match_data(self, match_id: int, input_path: PathLike) -> pd.DataFrame:
        """Load match data from pickle file."""
        return pd.read_pickle(Path(input_path) / f"{match_id}_events.pkl")

    def get_shots_stats(self) -> dict[str, int]:
        """Get shots data."""
        return Shots(data=self.data).get_stats()
