from dataclasses import dataclass
from enum import Enum, auto

import pandas as pd


class ShotOutcome(Enum):
    """Shot outcome types."""

    BLOCKED = "Blocked"
    OFF_TARGET = "Off T"
    SAVED = "Saved"
    GOAL = "Goal"
    SAVED_TO_POST = "Saved To Post"
    POST = "Post"
    WAYWARD = "Wayward"
    SAVED_OFF_TARGET = "Saved Off T"


@dataclass
class OutcomeCategory:
    """Represents a category of shot outcomes."""

    name: str
    outcomes: set[ShotOutcome]
    is_main: bool = True


class Shots:

    OUTCOME_CATEGORIES = [
        OutcomeCategory("on_target", {ShotOutcome.SAVED, ShotOutcome.GOAL, ShotOutcome.SAVED_TO_POST}),
        OutcomeCategory("off_target", {ShotOutcome.OFF_TARGET, ShotOutcome.POST, ShotOutcome.SAVED_OFF_TARGET}),
        OutcomeCategory("blocked", {ShotOutcome.BLOCKED}),
        OutcomeCategory("wayward", {ShotOutcome.WAYWARD}),
        # Additional categories
        OutcomeCategory("goal", {ShotOutcome.GOAL}, is_main=False),
        OutcomeCategory("post", {ShotOutcome.POST, ShotOutcome.SAVED_TO_POST}, is_main=False),
    ]

    def __init__(self, data: pd.DataFrame):
        self.data = data

    def get_stats(self) -> dict[str, int]:
        """Get shots data."""
        shots = self.data[self.data["type"] == "Shot"]
        try:
            Shots.validate_shot_outcome(shots)
        except ValueError as e:
            raise f"Error processing shot data: {e}"

        outcome_stats = self.get_outcome_stats(shots)

        return outcome_stats

    @classmethod
    def get_outcome_stats(cls, shots: pd.DataFrame) -> dict[str, int]:
        """Get shots outcome data."""

        # Create copy to avoid modifying original DataFrame
        outcome_stats = shots.copy()
        # Convert shot outcome string to ShotOutcome enum
        outcome_stats["shot_outcome_enum"] = outcome_stats["shot_outcome"].map(
            lambda x: next((outcome for outcome in ShotOutcome if outcome.value == x), None)
        )
        # Initialize results DataFrame with team and player columns
        results = pd.DataFrame(outcome_stats.groupby(["team", "player"])["id"].count()).reset_index()

        # Calculate counts for each outcome category
        for category in cls.OUTCOME_CATEGORIES:
            category_counts = (
                outcome_stats[outcome_stats["shot_outcome_enum"].isin(category.outcomes)]
                .groupby(["team", "player"])
                .size()
                .reset_index(name=category.name)
            )

            results = results.merge(category_counts, on=["team", "player"], how="left")
            results[category.name] = results[category.name].fillna(0)

        # Calculate total shots
        main_categories = [category.name for category in cls.OUTCOME_CATEGORIES if category.is_main]
        results["total"] = results[main_categories].sum(axis=1)

        # Ensure integer data types
        numeric_cols = [col for col in results.columns if col not in ["team", "player"]]
        results = results.astype({col: int for col in numeric_cols})

        # Order columns
        column_order = (
            ["team", "player", "total"]
            + [cat.name for cat in cls.OUTCOME_CATEGORIES if cat.is_main]
            + [cat.name for cat in cls.OUTCOME_CATEGORIES if not cat.is_main]
        )
        return results[column_order]

    @classmethod
    def validate_shot_outcome(cls, shots: pd.DataFrame) -> None:
        """Validate that the input DataFrame has the required structure."""
        required_columns = {"team", "player", "shot_outcome", "id"}
        if not all(col in shots.columns for col in required_columns):
            raise ValueError(f"DataFrame must contain columns: {required_columns}")

        valid_outcomes = {outcome.value for outcome in ShotOutcome}
        invalid_outcomes = set(shots["shot_outcome"].unique()) - valid_outcomes
        if invalid_outcomes:
            raise ValueError(f"Invalid shot outcomes found: {invalid_outcomes}")
