import os

import numpy as np
import pandas as pd
import streamlit as st
from statsbombpy import sb

creds = {"user": st.secrets["user"], "passwd": st.secrets["password"]}

from plots_and_charts.benchmark_chart import BenchmarkChart
from plots_and_charts.final_third_touches_plot import FinalThirdTouchesPlots
from plots_and_charts.game_openings_pitches import GameOpeningsPitches
from plots_and_charts.goals_and_chances_tables import GoalChancesTables
from plots_and_charts.high_turnovers import HighTurnovers
from plots_and_charts.individual_stats import IndividualStats
from plots_and_charts.key_passes_pitches import KeyPassesPitches
from plots_and_charts.line_breaking_passes import LineBreakingPasses
from plots_and_charts.match_events_tables import (RecoveriesTables,
                                                  ShotsTables, ThrowInsTables)
from plots_and_charts.obv_pitches import ObvPitches
from plots_and_charts.shot_maps import ShotMaps
from plots_and_charts.top_5_players import Top5Players
from plots_and_charts.xpass_chart import ExpectedPassChart
from plots_and_charts.zone_14_passes import Zone14Passes
from table_of_contents import Toc
from utils import get_data

st.set_page_config(
    page_title="Legia Warszawa Match Reports",
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
    unsafe_allow_html=True
)

# Custom CSS for vertical centering
st.markdown("""
    <style>
    .custom-title {
        font-size: 40px;  /* Adjust font size as needed */
        font-weight: bold;  /* Optional: make the text bold */
    }
    </style>
    """, unsafe_allow_html=True)

col1, col2= st.columns([1, 10])
with col1:
    st.image("resources/legia.ico")
with col2:
    # st.title("Legia Warszawa match reports")
    st.markdown('<div class="centered"><h1 class="custom-title">Legia Warszawa match reports</h1></div>', unsafe_allow_html=True)
st.subheader("Choose competition and match!")

team_name = "Legia Warszawa"
season_id = 317
competitions = (38, 353)

visualizations = ["Benchmark", "OBV Heatmap", "Goals Analysis", "Chances Analysis", "Shots Maps", "Shots Outcome", 
                  "High Turnovers", "Throw-Ins Outcome", "Recoveries Stats", "Passing Performance", "Final Third Touches", 
                  "Game Openings", "Key Passes", "Zone 14 Passes", "Offensive Individual Statistics", 
                  "Defensive Individual Statistics", "Top 5 Players"]
visualizations_360 = ["Line-breaking Passes"]


matches = pd.DataFrame()
for comp_id in competitions:
    comp_matches = sb.matches(competition_id=comp_id, season_id=season_id, creds=creds)
    matches = pd.concat([matches, comp_matches])

available_matches = matches[((matches["home_team"] == team_name) | (matches["away_team"] == team_name)) & (matches["match_status"] == "available")]

col, _ = st.columns([6, 2])
with col:
    competition = st.selectbox("Select a competition:", available_matches["competition"].sort_values().unique(), index=None)
    match_selection = available_matches[available_matches["competition"] == competition].sort_values("match_date", ascending=False)
    match_selection = {f"{home_team} vs {away_team}": match_id for match_id, home_team, away_team in zip(match_selection['match_id'], match_selection['home_team'], match_selection['away_team'])}
    match = st.selectbox("Select a match:", match_selection.keys(), index=None)

if match:
    toc = Toc()
    toc.placeholder(sidebar=True)

    match_id = match_selection[match]
    directory = f"matches/{match_id}"
    if not os.path.exists(directory):
        os.makedirs(directory)

    match_details = available_matches[available_matches["match_id"] == match_id]
    data_360 = match_details["match_status_360"].item()
    opponent = np.where(match_details['home_team'] == team_name, match_details['away_team'], match_details['home_team']).item()
    match_visualizations = visualizations if data_360 == "available" else [v for v in visualizations if v not in visualizations_360]
    col, _ = st.columns([6, 2])
    with col:
        selection = st.multiselect("Choose visualization to show:", match_visualizations, default=match_visualizations)
    col, _ = st.columns([6, 2])
    with col:
        left, right = st.columns(2)
        clicked = False
        if left.button("Show", use_container_width=True):
            clicked = True
            REGENERATE = False
        if right.button("Regenerate", use_container_width=True):
            clicked = True
            REGENERATE = True
    
    if clicked:
        match_events = get_data(match_id=match_id, data_type="events", creds=creds)
        players_match_stats = get_data(match_id=match_id, data_type="player_match_stats", creds=creds)

        passes = match_events[match_events["type"] == "Pass"]
        shots = match_events[match_events["type"] == "Shot"]
        goals = match_events[match_events["shot_outcome"] == "Goal"]
        goal_kick = match_events[match_events["pass_type"] == "Goal Kick"]


        score = f'{match_details["home_team"].item()} {int(match_details["home_score"].item())} : {int(match_details["away_score"].item())} {match_details["away_team"].item()}'
        st.header(score)
        st.subheader(f'Date: {match_details["match_date"].item()}')
        st.subheader(f'Referee: {match_details["referee"].item()}')

        if "Benchmark" in selection:
            toc.header("Benchmark")
            col, _ = st.columns([6, 2])
            with col:
                path = f"matches/{match_id}/match_benchmark.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    benchmark_chart = BenchmarkChart(matches=matches, game_id=match_id, team_for=team_name, team_against=opponent, creds=creds)
                    st.pyplot(benchmark_chart.plot_benchmark(directory=directory), clear_figure=True)

        if "OBV Heatmap" in selection:
            toc.header("OBV Heatmap")
            col1, col2, _ = st.columns([3, 3, 2])
            obv_heatmap = ObvPitches(match_events, team_for=team_name)
            with col1:
                path = f"matches/{match_id}/obv_map_for.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(obv_heatmap.plot_obv_heatmap(team_for=True, directory=directory), clear_figure=True)
            with col2:
                path = f"matches/{match_id}/obv_map_against.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(obv_heatmap.plot_obv_heatmap(team_for=False, directory=directory), clear_figure=True)

        data_files = {
            "goals_type": f"data/{match_id}_goals_type.json",
            "chances_time": f"data/{match_id}_chances_time.json",
            "chances_place": f"data/{match_id}_chances_place.json",
            "chances_type": f"data/{match_id}_chances_type.json"
        }
        goals_chances_tables = GoalChancesTables(goals, team_for=team_name, data_files=data_files)
        
        if "Goals Analysis" in selection:
            toc.header("Goals Analysis")    
            col1, col2, col3, _ = st.columns([3.5, 3.5, 5, 4])
            with col1:
                path = f"matches/{match_id}/goals_time.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(goals_chances_tables.generate_single_table("goals_time", directory=directory), clear_figure=True)
            with col2:
                path = f"matches/{match_id}/goals_place.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(goals_chances_tables.generate_single_table("goals_place", directory=directory), clear_figure=True)
            with col3:
                path = f"matches/{match_id}/goals_type.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(goals_chances_tables.generate_single_table("goals_type", directory=directory), clear_figure=True)

        if "Chances Analysis" in selection:
            toc.header("Chances Analysis")
            col1, col2, col3, _ = st.columns([3.5, 3.5, 5, 4])
            with col1:
                path = f"matches/{match_id}/chances_time.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(goals_chances_tables.generate_single_table("chances_time", directory=directory), clear_figure=True)
            with col2:
                path = f"matches/{match_id}/chances_place.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(goals_chances_tables.generate_single_table("chances_place", directory=directory), clear_figure=True)
            with col3:
                path = f"matches/{match_id}/chances_type.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(goals_chances_tables.generate_single_table("chances_type", directory=directory), clear_figure=True)
        
        if "Shots Maps" in selection:
            toc.header("Shots Maps")
            shot_maps = ShotMaps(shots, team_for=team_name)
            col1, col2, _ = st.columns([3, 3, 2])
            with col1:
                path = f"matches/{match_id}/shot_maps_for.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(shot_maps.plot_advanced_shot_map(directory=directory, team_for=True), clear_figure=True)
            with col2:
                path = f"matches/{match_id}/shot_maps_against.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(shot_maps.plot_advanced_shot_map(directory=directory, team_for=False), clear_figure=True)
        
        if "Shots Outcome" in selection:
            toc.header("Shots Outcome")
            shot_tables = ShotsTables(shots, team_for=team_name)
            col1, col2, _ = st.columns([2, 4, 2])
            with col1:
                path = f"matches/{match_id}/shots_outcome.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(shot_tables.plot_team_shots_table(directory=directory), clear_figure=True)
            with col2:
                path = f"matches/{match_id}/individual_shots.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(shot_tables.plot_individual_shots_table(directory=directory), clear_figure=True)

        if "High Turnovers" in selection:
            toc.header("High Turnovers")
            high_turnovers = HighTurnovers(match_events=match_events, team_for=team_name)
            col1, col2, _ = st.columns([3, 3, 2])
            with col1:
                path = f"matches/{match_id}/high_turnovers_for.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(high_turnovers.plot_high_turnover_map(directory=directory, team_for=True), clear_figure=True)
            with col2:
                path = f"matches/{match_id}/high_turnovers_against.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(high_turnovers.plot_high_turnover_map(directory=directory, team_for=False), clear_figure=True)

        grand_col1, grand_col2 = st.columns(2)
        with grand_col1:
            throw_ins_tables = ThrowInsTables(passes, team_for=team_name)
            if "Throw-Ins Outcome" in selection:
                toc.header("Throw-Ins Outcome")
                col1, col2, _ = st.columns([3, 3, 1])
                with col1:
                    path = f"matches/{match_id}/throw_ins_for.png"
                    if os.path.isfile(path) and not REGENERATE:
                        st.image(path, use_column_width=True)
                    else:
                        st.pyplot(throw_ins_tables.plot_throw_ins(directory=directory, team_for=True), clear_figure=True)
                with col2:
                    path = f"matches/{match_id}/throw_ins_against.png"
                    if os.path.isfile(path) and not REGENERATE:
                        st.image(path, use_column_width=True)
                    else:
                        st.pyplot(throw_ins_tables.plot_throw_ins(directory=directory, team_for=False), clear_figure=True)
        with grand_col2:
            if "Recoveries Stats" in selection:
                toc.header("Recoveries Stats")
                recoveries_tables = RecoveriesTables(match_events, team_for=team_name)
                col, _, = st.columns(2)
                with col:
                    path = f"matches/{match_id}/recoveries.png"
                    if os.path.isfile(path) and not REGENERATE:
                        st.image(path, use_column_width=True)
                    else:
                        st.pyplot(recoveries_tables.plot_recovery_stats(directory=directory), clear_figure=True)
            
        if "Passing Performance" in selection:
            toc.header("Passing Performance")
            xpass_charts = ExpectedPassChart(passes, team_for=team_name)
            col, _, = st.columns([6, 2])
            with col:
                path = f"matches/{match_id}/players_passing_performance.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(xpass_charts.plot_xpass_plot(directory=directory), clear_figure=True)

        if "Final Third Touches" in selection:
            toc.header("Final Third Touches")
            final_third_touches = FinalThirdTouchesPlots(match_events, team_for=team_name)
            col, _, = st.columns([6, 2])
            with col:
                path = f"matches/{match_id}/touches_in_final_3rd.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(final_third_touches.plot_final_third_touches(directory=directory), clear_figure=True)

        if "Game Openings" in selection:
            toc.header("Game Openings")
            col1, col2, _, = st.columns([3, 3, 2])
            game_openings = GameOpeningsPitches(goal_kick, team_for=team_name)
            with col1:
                path = f"matches/{match_id}/openings_for.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(game_openings.plot_game_openings(team_for=True, directory=directory), clear_figure=True)
            with col2:
                path = f"matches/{match_id}/openings_against.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(game_openings.plot_game_openings(team_for=False, directory=directory), clear_figure=True)

        if "Key Passes" in selection:
            toc.header("Key Passes")
            col1, col2, _, = st.columns([3, 3, 2])
            key_passes = KeyPassesPitches(match_events, team_for=team_name)
            with col1:
                path = f"matches/{match_id}/key_passes_for.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(key_passes.plot_key_passes(team_for=True, directory=directory), clear_figure=True)
            with col2:
                path = f"matches/{match_id}/key_passes_against.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(key_passes.plot_key_passes(team_for=False, directory=directory), clear_figure=True)

        if data_360 == "available":
            if not "ball_receipt_in_space" in match_events.columns:
                match_events = get_data(match_id=match_id, data_type="events", creds=creds, force_redownload=True)
                players_match_stats = get_data(match_id=match_id, data_type="player_match_stats", creds=creds, force_redownload=True)

            if "Line-breaking Passes" in selection:
                toc.header("Line-breaking Passes")
                line_breaking_passes = LineBreakingPasses(match_events, team_for=team_name)
                col1, col2, _, = st.columns([3, 3, 2])
                with col1:
                    path = f"matches/{match_id}/line_breaking_passes_for.png"
                    if os.path.isfile(path) and  REGENERATE:
                        st.image(path, use_column_width=True)
                    else:
                        st.pyplot(line_breaking_passes.plot_line_breaking_passes(team_for=True, directory=directory), clear_figure=True)
                with col2:
                    path = f"matches/{match_id}/line_breaking_passes_against.png"
                    if os.path.isfile(path) and  REGENERATE:
                        st.image(path, use_column_width=True)
                    else:
                        st.pyplot(line_breaking_passes.plot_line_breaking_passes(team_for=False, directory=directory), clear_figure=True)

        if "Zone 14 Passes" in selection:
            toc.header("Zone 14 Passes")
            col1, col2, _, = st.columns([3, 3, 2])
            zone_14_passes = Zone14Passes(passes, team_for=team_name)
            with col1:
                path = f"matches/{match_id}/passes_to_zone_14_for.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(zone_14_passes.plot_passes_to_zone_14(team_for=True, directory=directory), clear_figure=True)
            with col2:
                path = f"matches/{match_id}/passes_to_zone_14_against.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(zone_14_passes.plot_passes_to_zone_14(team_for=False, directory=directory), clear_figure=True)

            with col1:
                path = f"matches/{match_id}/passes_from_zone_14_for.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(zone_14_passes.plot_passes_from_zone_14(team_for=True, directory=directory), clear_figure=True)
            with col2:
                path = f"matches/{match_id}/passes_from_zone_14_against.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(zone_14_passes.plot_passes_from_zone_14(team_for=False, directory=directory), clear_figure=True)

        if "Offensive Individual Statistics" in selection:
            toc.header("Offensive Individual Statistics")
            col, _, = st.columns([6, 2])
            individual_stats = IndividualStats(players_match_stats, team_for=team_name)
            with col:
                path = f"matches/{match_id}/individual_attack.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(individual_stats.plot_offensive_table(directory=directory), clear_figure=True)
        
        if "Offensive Individual Statistics" in selection:
            toc.header("Offensive Individual Statistics")
            col, _, = st.columns([6, 2])
            individual_stats = IndividualStats(players_match_stats, team_for=team_name)
            with col:
                path = f"matches/{match_id}/individual_defence.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(individual_stats.plot_defensive_table(directory=directory), clear_figure=True)

        if "Top 5 Players" in selection:
            toc.header("Top 5 Players")
            col1, col2, _, = st.columns([3, 3, 2])
            top_5_players = Top5Players(match_events, team_for=team_name)
            with col1:
                path = f"matches/{match_id}/top_5_obv.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(top_5_players.plot_obv_gain(directory=directory), clear_figure=True)

                path = f"matches/{match_id}/top_5_def_1.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(top_5_players.plot_defensive_1(directory=directory), clear_figure=True)

            with col2:
                path = f"matches/{match_id}/top_5_progressors.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(top_5_players.plot_progressions(directory=directory), clear_figure=True)
                
                path = f"matches/{match_id}/top_5_def_2.png"
                if os.path.isfile(path) and not REGENERATE:
                    st.image(path, use_column_width=True)
                else:
                    st.pyplot(top_5_players.plot_defensive_2(directory=directory), clear_figure=True)

        
        toc.generate()
