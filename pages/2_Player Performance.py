import os

import pandas as pd
import streamlit as st

from data_processing.create_index import calculate_player_index, preprocess_metrics
from data_processing.regeneration import regenerate_data
from plots_and_charts.player_benchmark import plot_player_benchmark
from plots_and_charts.player_trendline import plot_player_trendline
from table_of_contents import Toc
from utils import (
    calculate_match_statistics,
    ensure_player_directory,
    get_credentials,
    get_players_list,
    load_all_gk_metrics,
    load_all_match_events,
    load_all_metrics,
    load_matches,
    load_metrics,
    load_postions,
    save_metrics,
)

st.set_page_config(
    page_title="Player Performance",
    layout="wide",
)
st.markdown(
    """
    <style>
    .main {
        max-width: 85%;  /* Adjust this value for more or less width */
        margin: 0 auto;  /* Center the content */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Custom CSS for vertical centering
st.markdown(
    """
    <style>
    .custom-title {
        font-size: 40px;  /* Adjust font size as needed */
        font-weight: bold;  /* Optional: make the text bold */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

col1, col2 = st.columns([1, 10])
with col1:
    st.image("resources/legia.ico")
with col2:
    # st.title("Legia Warszawa match reports")
    st.markdown(
        '<div class="centered"><h1 class="custom-title">Legia Warszawa Player Performance Analysis</h1></div>',
        unsafe_allow_html=True,
    )
st.subheader("Choose player and match to show his performance analysis!")

team_name = "Legia Warszawa"
season_id = 317
competitions = (38, 353)

visualizations = ["Benchmark", "Trendlines"]


creds = get_credentials()

available_matches = load_matches(team_name, season_id, competitions, creds)
available_matches = calculate_match_statistics(available_matches, team_name)

all_matches_events = load_all_match_events(available_matches, creds)
players = get_players_list(all_matches_events, available_matches, team_name)
regenerate_data(players, available_matches, all_matches_events, team_name)

col, _ = st.columns([6, 2])
with col:
    chosen_player = st.selectbox("Select a player:", players, index=None)

    if chosen_player:
        players_matches = players[chosen_player]["available_matches"]
        match_selection = available_matches[
            available_matches["match_id"].isin(players_matches)
        ].sort_values("match_date", ascending=False)
        match_selection = {
            f"{opponent} ({match_date})": match_id
            for match_id, opponent, match_date in zip(
                match_selection["match_id"],
                match_selection["opponent"],
                match_selection["match_date"],
            )
        }
        chosen_match = st.selectbox(
            "Select a match:", match_selection.keys(), index=None
        )
        if chosen_match:
            position = load_postions()[chosen_player]
            # Load initial metrics and weights
            metrics_data = load_metrics()[position]

            # Define potential additional metrics
            all_possible_metrics = (
                load_all_metrics()
                if position != "Goalkeeper"
                else load_all_gk_metrics()
            )

            # Display phases and select a game phase
            phases = list(metrics_data.keys())
            chosen_game_phase = st.selectbox("Select a game phase:", phases, index=None)

            if chosen_game_phase:
                # Load default metrics and weights for the selected phase
                default_metrics = metrics_data[chosen_game_phase]
                st.write(f"Default metrics and weights for {chosen_game_phase}")
                # TODO: reversed metrics
                # TODO: remove metrics with weight 0 when saving
                # TODO: warning in individual stats
                weights = {}
                total_weight = 0

                # Display existing metrics and allow weight adjustments
                for metric, weight in default_metrics.items():
                    weights[metric] = st.number_input(
                        f"Weight for {metric}",
                        min_value=0.0,
                        max_value=1.0,
                        value=weight,
                        step=0.01,
                    )
                    total_weight += weights[metric]

                # Multi-select for new metrics, excluding already chosen ones
                remaining_metrics = list(
                    set(all_possible_metrics) - set(weights.keys())
                )
                new_metrics = st.multiselect(
                    "Select additional metrics", remaining_metrics
                )

                # Display weight input fields for each newly selected metric
                for metric in new_metrics:
                    weight = st.number_input(
                        f"Weight for {metric}",
                        min_value=0.0,
                        max_value=1.0,
                        step=0.01,
                    )
                    weights[metric] = weight
                    total_weight += weight

                # Validate that weights sum to 1.0 and show the actual total
                if round(total_weight, 4) != 1.0:
                    st.error(
                        f"The sum of weights must equal 1.0. Csurrent sum is: {total_weight:.2f}"
                    )
                else:
                    st.success("The KPI system is set up correctly!")

                    # Option to save updated metrics and weights to a new JSON file
                    if st.button("Save KPI configuration"):
                        metrics_data[chosen_game_phase] = weights
                        save_metrics(metrics_data)
                        st.success("Updated KPI configuration saved with timestamp!")

                match_id = match_selection[chosen_match]

                toc = Toc()
                toc.placeholder(sidebar=True)

                player_directory = ensure_player_directory(chosen_player)
                team_directory = ensure_player_directory("Team")

                player_file_path = os.path.join(
                    player_directory, f"{chosen_player}_stats.tsv"
                )
                team_file_path = (
                    os.path.join(team_directory, f"Team_stats.tsv")
                    if position != "Goalkeeper"
                    else os.path.join(team_directory, f"Team_gk_stats.tsv")
                )

                team_stats = pd.read_csv(team_file_path, sep="\t")
                normalized_team_stats = preprocess_metrics(team_stats)
                normalized_player_stats = normalized_team_stats[
                    normalized_team_stats["player"] == chosen_player
                ]
                player_indexes = calculate_player_index(
                    normalized_player_stats, weights
                )

                player_stats = pd.read_csv(player_file_path, sep="\t")

                if col.button("Show", use_container_width=True):
                    st.header(chosen_player)
                    toc.header(f"Trendline Performance Index")
                    st.pyplot(
                        plot_player_trendline(
                            player=chosen_player,
                            game_id=match_id,
                            df=player_indexes,
                            title_stat="Index",
                            y_stat="performance_index",
                            directory=player_directory,
                        )
                    )
                    toc.header(f"Benchmark")
                    st.pyplot(
                        plot_player_benchmark(
                            player=chosen_player,
                            game_id=match_id,
                            player_df=player_stats,
                            metrics=list(weights),
                            reverse_metrics=[],
                            directory=player_directory,
                        )
                    )
                    for metric in weights:
                        metric_to_display = metric.replace("_", " ").title()
                        toc.header(f"Trendline {metric_to_display}")
                        st.pyplot(
                            plot_player_trendline(
                                player=chosen_player,
                                game_id=match_id,
                                df=player_stats,
                                title_stat=metric_to_display,
                                y_stat=metric,
                                directory=player_directory,
                            )
                        )
                    toc.generate()
