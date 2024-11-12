import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler


def per_90(row, stat):
    if row[stat] == np.NaN:
        return np.NaN
    per_1 = row[stat] / row["minutes_played"]
    return round(per_1 * 90, 2)


def preprocess_metrics(df):
    minmax_scaler = MinMaxScaler()

    cols = [
        col
        for col in df.columns
        if col
        not in [
            "player",
            "match_id",
            "minutes_played",
            "match_date",
            "opponent",
            "match_result",
        ]
    ]
    cols = [col for col in cols if "ratio" not in col]

    df_per_90 = df.copy()
    for col in cols:
        df_per_90[col] = df_per_90.apply(lambda x: per_90(x, col), axis=1)
    df_per_90_normalized = df_per_90.copy()

    df_normalized_cols = pd.DataFrame(
        minmax_scaler.fit_transform(df_per_90[cols]), columns=cols
    )

    df_per_90_normalized.update(df_normalized_cols)

    return df_per_90_normalized


def calculate_player_index(preprocessed_df: pd.DataFrame, weights: dict[str, float]):
    """
    Calculate player performance index using pre-normalized metrics and ratios.

    Parameters:
    df: pandas DataFrame with player metrics
        - Ratio columns should be between 0-1 or np.nan
        - Per90 metrics should already be normalized using min-max scaling
    weights: dictionary with metric names as keys and weights as values

    Returns:
    DataFrame with original data and calculated performance index
    """
    # Verify weights sum to 1
    if abs(sum(weights.values()) - 1) > 0.001:
        raise ValueError("Weights must sum to 1")

    # Calculate weighted sum while handling NaN values
    weighted_scores = []
    for metric, weight in weights.items():
        weighted_scores.append(preprocessed_df[metric].fillna(0) * weight)

    # Sum all weighted scores
    preprocessed_df["performance_index"] = sum(weighted_scores)

    # Scale to 0-100 for easier interpretation
    preprocessed_df["performance_index"] = preprocessed_df["performance_index"] * 100

    preprocessed_df = preprocessed_df[
        [
            "player",
            "match_id",
            "minutes_played",
            "match_date",
            "opponent",
            "match_result",
            "performance_index",
        ]
    ]

    preprocessed_df = preprocessed_df.reset_index(drop=True).copy()

    return preprocessed_df
