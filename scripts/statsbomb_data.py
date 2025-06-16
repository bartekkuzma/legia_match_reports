import json
import os
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from statsbombpy import sb
from tqdm import tqdm


class StatsBombDataProcessor:
    def __init__(self, user: str, password: str):
        """
        Initialize the StatsBomb Data Processor

        Args:
            user (str): StatsBomb API username
            password (str): StatsBomb API password
        """
        self.creds = {"user": user, "passwd": password}

        # Position mapping for standardizing positions
        self.position_mapping = {
            "Goalkeeper": "Goalkeeper",
            "Right Back": "Full Back",
            "Right Center Back": "Center Back",
            "Center Back": "Center Back",
            "Left Center Back": "Center Back",
            "Left Back": "Full Back",
            "Right Wing Back": "Full Back",
            "Left Wing Back": "Full Back",
            "Right Defensive Midfield": "Defensive Midfield",
            "Center Defensive Midfield": "Defensive Midfield",
            "Left Defensive Midfield": "Defensive Midfield",
            "Right Midfield": "Center Midfield",
            "Right Center Midfield": "Center Midfield",
            "Center Midfield": "Center Midfield",
            "Left Center Midfield": "Center Midfield",
            "Left Midfield": "Center Midfield",
            "Right Wing": "Winger",
            "Left Wing": "Winger",
            "Right Attacking Midfield": "Winger",
            "Left Attacking Midfield": "Winger",
            "Center Attacking Midfield": "Center Midfield",
            "Right Center Forward": "Striker",
            "Striker": "Striker",
            "Left Center Forward": "Striker",
            "Secondary Striker": "Striker",
            "Center Forward": "Striker",
        }

        # Name mappings to standardize player names
        self.names_mappings = {
            "Rúben Gonçalo Silva Nascimento Vinagre": "Rúben Vinagre",
            "Lucas Lima Linhares": "Luquinhas",
            "Marc Gual Huguet": "Marc Gual",
            "Joaquim Claude Gonçalves Araújo": "Claude Gonçalves",
            "Sergio Barcia Laranxeira": "Sergio Barcia",
            "Maximilano Oyedele": "Maxi Oyedele",
            "Bartosz Biedrzycki ": "Bartosz Biedrzycki",
            "Borja Galán González": "Borja Galán",
            "Filipe Guterres Nascimento": "Filipe Nascimento",
            "José Manuel Sánchez Guillén": "Josema Sánchez",
            "Manuel Sánchez García": "Manu Sánchez",
            "Adrián Diéguez Grande": "Adrián Diéguez",
            "Jesús Imaz Ballesté": "Jesús Imaz",
            "João Gervásio Bragança Moutinho": "João Moutinho",
            "Kristoffer Normann Hansen": "Kristoffer Hansen",
            "Maksymilian Stryjek": "Max Stryjek",
            "Miguel Villar Alonso": "Miky Villar",
            "Mohamed Lamine Diaby Fadiga": "Mohamed Lamine Diaby",
            "Rui Filipe Cunha Correia": "Nené",
            "Tomás Costa Silva": "Tomás Silva",
            "Adrián Dalmau Vaquer": "Adrián Dalmau",
            "Hubert Zwozny": "H.Zwozny",
            "Marcel Zapytowski": "Marcel Zapytowski",  ##probably only got yellow card all season
            "Pau Resta Tell": "Pau Resta",
            "Pedro Nuno Fernandes Ferreira": "Pedro Nuno",
            "Afonso Gamelas De Pinho Sousa": "Afonso Sousa",
            "Joel Vieira Pereira": "Joel Pereira",
            "Camilo Andrés Mena Márquez": "Camilo Mena",
            "Conrado Buchanelli Holz": "Conrado",
            "Serhii Buletsa": "Sergiy Buletsa",
            "Sergi Samper Montaña": "Sergi Samper",
            "Jorge Félix Muñoz García": "Jorge Félix",
            "Miguel Muñoz Fernández": "Miguel Muñoz",
            "Miguel Raimundo Nóbrega": "Miguel Nóbrega",
            "João Pedro Costa Gamboa": "João Gamboa",
            "Leonardo Borges da Silva": "Leonardo Borges",
            "Valentin Alexandru Cojocaru": "Valentin Cojocaru",
            "Jin-Hyun Lee": "Lee Jin-Hyun",
            "Bruno André Cavaco Jordão": "Bruno Jordão",
            "Francisco Augusto Neto Ramos": "Francisco Ramos",
            "Guilherme da Gama Zimovski": "G.da Gama Zimovski",
            "João Gabriel Martins Peglow": "João Peglow",
            "Leonardo Miramar Rocha": "Rocha Miramar",
            "Luiz Gustavo Novaes Palhares": "Luizão",
            "Osvaldo Pedro Capemba": "Capita",
            "Paulo Henrique Rodrigues Cabral": "Paulo Henrique",
            "Roberto Emanuel Oliveira Alves": "Roberto Alves",
            "Vágner José Dias Gonçalves": "Vagner",
            "Zié Mohamed Ouattara": "Zié Ouattara",
            "Dušan Kuciak": "Dušan Kuciak",  ##probably only got yellow card all season
            "Erick  Ouma Otieno": "Erick Otieno",
            "Iván López Álvarez": "Ivi López",
            "Jean Carlos Silva Rocha": "Jean Carlos",
            "Jesús Antonio Díaz Gómez": "Jesús Díaz",
            "Francisco Javier Alvarez Rodríguez": "Fran Álvarez",
            "Hillary Chukwah Gong": "Hilary Gong",
            "Juan Fernández Blanco": "Juan Fernández",
            "Lirim Kastrati": "Lirim Kastrati II",
            "Luis Marques Almeida Vieira Silva": "Luís Silva",
            "Luís Carlos Machado Mata": "Luís Mata",
            "Marcel Wojciech Reguła": "Marcel Regula",
            "Arnau Ortiz Sanchez": "Arnau Ortiz",
            "Junior Flor Eyamba": "Junior Eyamba",
            "Matías Nahuel Leiva Esquivel": "Matías Nahuel",
            "Tudor Cristian Băluţă": "Tudor Baluta",
        }

    def fetch_matches(self, season_ids: List[int], competition_ids: List[int]) -> pd.DataFrame:
        """
        Fetch matches for given seasons and competitions

        Args:
            season_ids (List[int]): List of season IDs to fetch
            competition_ids (List[int]): List of competition IDs to fetch

        Returns:
            pd.DataFrame: DataFrame of available matches
        """
        all_matches = pd.DataFrame()

        for season_id in season_ids:
            for comp_id in competition_ids:
                comp_matches = sb.matches(competition_id=comp_id, season_id=season_id, creds=self.creds)
                all_matches = pd.concat([all_matches, comp_matches])

        # Filter available matches and select relevant columns
        available_matches = all_matches[all_matches["match_status"] == "available"][
            ["match_id", "match_date", "season", "home_team", "away_team", "home_score", "away_score"]
        ].sort_values("match_date", ascending=False)

        return available_matches

    def process_players_data(self, matches: pd.DataFrame) -> Dict[str, Any]:
        """
        Process player data for given matches

        Args:
            matches (pd.DataFrame): DataFrame of matches to process

        Returns:
            Dict containing processed player data
        """
        all_players_stats = pd.DataFrame()
        all_players_events = pd.DataFrame()

        # Fetch data for each match
        for match_id in tqdm(matches["match_id"].to_list(), total=len(matches)):
            temp_stats = sb.player_match_stats(match_id, creds=self.creds)
            all_players_stats = pd.concat([all_players_stats, temp_stats])

            temp_events = sb.events(match_id, creds=self.creds)
            all_players_events = pd.concat([all_players_events, temp_events])

        # Process player positions
        pos = (
            all_players_events.groupby(["team", "player", "match_id", "position"])
            .count()["index"]
            .to_frame()
            .reset_index()
        )
        pos = (
            pos.loc[pos.groupby(["team", "player", "match_id"])["index"].idxmax()]
            .reset_index(drop=True)
            .drop("index", axis=1)
        )

        # Apply name mappings
        pos["player"] = pos["player"].apply(lambda x: self.names_mappings.get(x, x))

        # Create nested dictionary of player positions
        player_positions = self._create_player_positions_dict(pos)

        # Prepare enhanced player stats
        pos["position"] = pos["position"].apply(lambda x: self.position_mapping.get(x, np.NaN))
        pos.columns = ["team_name", "player_name", "match_id", "position"]

        enhanced_players_stats = pos.merge(all_players_stats, on=["team_name", "player_name", "match_id"])

        return {
            "player_positions": player_positions,
            "enhanced_players_stats": enhanced_players_stats,
            "players_events": all_players_events,
        }

    def _create_player_positions_dict(self, positions_df: pd.DataFrame) -> Dict[str, Dict[str, Dict[str, List[int]]]]:
        """
        Create a nested dictionary of player positions

        Args:
            positions_df (pd.DataFrame): DataFrame of player positions

        Returns:
            Nested dictionary of player positions
        """
        result = {}
        for _, row in positions_df.iterrows():
            team = row["team"]
            player = row["player"]
            position = row["position"]
            match_id = row["match_id"]

            if team not in result:
                result[team] = {}
            if player not in result[team]:
                result[team][player] = {}
            if position not in result[team][player]:
                result[team][player][position] = []

            result[team][player][position].append(match_id)

        return result

    def save_data(self, data: Dict[str, Any], output_dir: str = "processed_data"):
        """
        Save processed data to TSV and JSON files

        Args:
            data (Dict): Processed data dictionary
            output_dir (str, optional): Directory to save files. Defaults to 'processed_statsbomb_data'.
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Save player positions to JSON
        with open(os.path.join(output_dir, "player_positions.json"), "w", encoding="utf-8") as f:
            json.dump(data["player_positions"], f, indent=4, ensure_ascii=False)

        # Save enhanced players stats to TSV
        data["enhanced_players_stats"].to_csv(
            os.path.join(output_dir, "enhanced_players_stats.tsv"), sep="\t", index=False
        )

        # Save players events to TSV
        data["players_events"].to_csv(os.path.join(output_dir, "players_events.tsv"), sep="\t", index=False)

        print(f"Data saved to {output_dir}")

    def process_data(self, season_ids: List[int], competition_ids: List[int]):
        """
        Main method to process StatsBomb data

        Args:
            season_ids (List[int]): List of season IDs to process
            competition_ids (List[int]): List of competition IDs to process
        """
        # Fetch matches
        matches = self.fetch_matches(season_ids, competition_ids)

        # Process player data
        processed_data = self.process_players_data(matches)

        # Save processed data
        self.save_data(processed_data)


# Example usage
if __name__ == "__main__":
    # Replace with actual credentials
    processor = StatsBombDataProcessor(user="bartkuzma@gmail.com", password="v1x6CQUt")

    # Process data for specific seasons and competitions
    processor.process_data(season_ids=[317], competition_ids=[38])  # Example season ID  # Example competition ID
