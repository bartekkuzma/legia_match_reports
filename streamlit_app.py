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
from plots_and_charts.key_passes_pitches import KeyPassesPitches
from plots_and_charts.match_events_tables import (RecoveriesTables,
                                                  ShotsTables, ThrowInsTables)
from plots_and_charts.obv_pitches import ObvPitches
from plots_and_charts.xpass_chart import ExpectedPassChart
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

matches = pd.DataFrame()
for comp_id in competitions:
    comp_matches = sb.matches(competition_id=comp_id, season_id=season_id, creds=creds)
    matches = pd.concat([matches, comp_matches])

available_matches = matches[((matches["home_team"] == team_name) | (matches["away_team"] == team_name)) & (matches["match_status"] == "available")]

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
    opponent = np.where(match_details['home_team'] == team_name, match_details['away_team'], match_details['home_team']).item()

    match_events = get_data(match_id=match_id, data_type="events", creds=creds)
    players_match_stats = get_data(match_id=match_id, data_type="player_match_stats", creds=creds)

    # match_events = match_events.replace("Rúben Gonçalo Silva Nascimento Vinagre","Rúben Vinagre")
    # match_events = match_events.replace("Lucas Lima Linhares","Luquinhas")
    # match_events = match_events.replace("Marc Gual Huguet","Marc Gual")
    # match_events = match_events.replace("Joaquim Claude Gonçalves Araújo","Claude Gonçalves")
    # match_events = match_events.replace("Sergio Barcia Laranxeira","Sergio Barcia")
    # match_events = match_events.replace("Maximiliano Oyedele","Maxi Oyedele")

    # players_match_stats = sb.player_match_stats(match_id=match_id, creds=creds)
    # players_match_stats = players_match_stats.replace("Rúben Gonçalo Silva Nascimento Vinagre","Rúben Vinagre")
    # players_match_stats = players_match_stats.replace("Lucas Lima Linhares","Luquinhas")
    # players_match_stats = players_match_stats.replace("Marc Gual Huguet","Marc Gual")
    # players_match_stats = players_match_stats.replace("Joaquim Claude Gonçalves Araújo","Claude Gonçalves")
    # players_match_stats = players_match_stats.replace("Sergio Barcia Laranxeira","Sergio Barcia")
    # players_match_stats = players_match_stats.replace("Maximiliano Oyedele","Maxi Oyedele")


    score = f'{match_details["home_team"].item()} {int(match_details["home_score"].item())} : {int(match_details["away_score"].item())} {match_details["away_team"].item()}'
    st.header(score)
    st.subheader(f'Date: {match_details["match_date"].item()}')
    st.subheader(f'Referee: {match_details["referee"].item()}')

    toc.header("Benchmark")
    col, _, = st.columns([5, 1])
    with col:
        benchmark_chart = BenchmarkChart(matches=matches, game_id=match_id, team_for=team_name, team_against=opponent, creds=creds)
        st.pyplot(benchmark_chart.plot_benchmark(directory=directory))

    toc.header("OBV Heatmap")
    col1, col2, _, = st.columns([3, 3, 2])
    obv_heatmap = ObvPitches(match_events, team_for=team_name)
    with col1:
        st.pyplot(obv_heatmap.plot_obv_heatmap(team_for=True, directory=directory))
    with col2:
        st.pyplot(obv_heatmap.plot_obv_heatmap(team_for=False, directory=directory))   


    goals = match_events[match_events["shot_outcome"] == "Goal"]
    soccer_analysis = GoalChancesTables(goals, team_for=team_name)
    data_files = {
        "goals_type": "goals_type.json",
        "chances_time": "chances_time.json",
        "chances_place": "chances_place.json",
        "chances_type": "chances_type.json"
    }
    figs = soccer_analysis.generate_all_tables(directory, data_files)

    toc.header("Goals Analysis")    
    col1, col2, col3, _ = st.columns([4, 4, 6, 4])
    with col1:
        st.pyplot(figs["goals_time"])
    with col2:
        st.pyplot(figs["goals_place"])
    with col3:
        st.pyplot(figs["goals_type"])

    toc.header("Chances Analysis")
    col1, col2, col3, _ = st.columns([4, 4, 6, 4])
    with col1:
        st.pyplot(figs["chances_time"])
    with col2:
        st.pyplot(figs["chances_place"])
    with col3:
        st.pyplot(figs["chances_type"])
    
    toc.header("Shots Outcome")
    shots = match_events[match_events["type"] == "Shot"]
    shot_tables = ShotsTables(shots, team_for=team_name)
    col1, col2, _ = st.columns([2, 5, 2])
    with col1:
        st.pyplot(shot_tables.plot_team_shots_table(directory=directory))
    with col2:
        st.pyplot(shot_tables.plot_individual_shots_table(directory=directory))

    toc.header("Throw-Ins Outcome")
    passes = match_events[match_events["type"] == "Pass"]
    throw_ins_tables = ThrowInsTables(passes, team_for=team_name)
    col1, col2, _,  _ = st.columns(4)
    with col1:
        st.pyplot(throw_ins_tables.plot_throw_ins(directory=directory, team_for=True))
    with col2:
        st.pyplot(throw_ins_tables.plot_throw_ins(directory=directory, team_for=False))

    toc.header("Recoveries Stats")
    col, _, _, _ = st.columns(4)
    with col:
        recoveries_tables = RecoveriesTables(match_events, team_for=team_name)
        st.pyplot(recoveries_tables.plot_recovery_stats(directory=directory))
        
    toc.header("Passing Performance")
    col, _, = st.columns([5, 2])
    with col:
        xpass_charts = ExpectedPassChart(passes, team_for=team_name)
        st.pyplot(xpass_charts.plot_xpass_plot(directory=directory))

    toc.header("Final Third Touches")
    col, _, = st.columns([5, 2])
    with col:
        final_third_touches = FinalThirdTouchesPlots(match_events, team_for=team_name)
        st.pyplot(final_third_touches.plot_final_third_touches(directory=directory))

    toc.header("Game Openings")
    col1, col2, _, = st.columns([3, 3, 2])
    goal_kick = match_events[match_events["pass_type"] == "Goal Kick"]
    game_openings = GameOpeningsPitches(goal_kick, team_for=team_name)
    with col1:
        st.pyplot(game_openings.plot_game_openings(team_for=True, directory=directory))
    with col2:
        st.pyplot(game_openings.plot_game_openings(team_for=False, directory=directory))   

    toc.header("Key Passes")
    col1, col2, _, = st.columns([3, 3, 2])
    key_passes = KeyPassesPitches(match_events, team_for=team_name)
    with col1:
        st.pyplot(key_passes.plot_key_passes(team_for=True, directory=directory))
    with col2:
        st.pyplot(key_passes.plot_key_passes(team_for=False, directory=directory))   
    
    
    
    toc.generate()
