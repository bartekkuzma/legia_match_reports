import os

import pandas as pd


class SkillCornerDataProcessor:
    def __init__(self, file_date, match_date_filter):
        """
        Initialize the SkillCorner Data Processor

        Args:
            file_date (str): Date used in the filename (e.g., '2024-12-09')
            match_date_filter (str): Minimum match date to filter data
        """
        self.file_date = file_date
        self.match_date_filter = match_date_filter

        # Define name and team mappings
        self.names_to_change = {
            "Rúben Gonçalo Silva Nascimento Vinagre": "Rúben Vinagre",
            "Jean-Pierre Nsamé": "Jean Pierre Nsamé",
            "Joaquim Claude  Gonçalves Araújo": "Claude Gonçalves",
            "Lucas Lima Linhares": "Luquinhas",
            "Marc Gual Huguet": "Marc Gual",
            "Sergio Barcia Laranxeira": "Sergio Barcia",
            "Maximillian Oyedele": "Maxi Oyedele",
            "Wojciech Urbanski": "Wojciech Urbański",
            "Dino Hotič": "Dino Hotić",
            "Afonso Gamelas De Pinho Sousa": "Afonso Sousa",
            "Joel Vieira Pereira": "Joel Pereira",
            "Daniel Noel Mikael Håkans": "Daniel Håkans",
            "Alex Douglas": "Alex Raymond Douglas",
            "Luís Carlos Machado Mata": "Luís Mata",
            "Francisco Augusto Neto Ramos": "Francisco Ramos",
            "Bruno André Cavaco Jordão": "Bruno Jordão",
            "Vagner José Dias Gonçalves": "Vagner",
            "Leonardo Miramar Rocha": "Rocha Miramar",
            "Luiz Gustavo Novaes Palhares": "Luizão",
            "Osvaldo Pedro Capemba": "Capita",
            "João Gabriel Martins Peglow": "João Peglow",
            "Zié Mohamed Ouattara": "Zié Ouattara",
            "Michal Kaput": "Michał Kaput",
            "Paulo Henrique Rodrigues Cabral": "Paulo Henrique",
            "Roberto Emanuel Oliveira Alves": "Roberto Alves",
            "Guilherme da Gama Zimovski": "G.da Gama Zimovski",
            "João Pedro Costa Gamboa": "João Gamboa",
            "Vahan Bichakhchyan": "Vahan Vardani Bichakhchyan",
            "Leonardo Borges da Silva": "Leonardo Borges",
            "Olaf Korczakowski": "Olaf Igor Korczakowski",
            "Jorge Félix Muñoz García": "Jorge Félix",
            "Miguel Muñoz Fernández": "Miguel Muñoz",
            "Miguel Raimundo Nóbrega": "Miguel Nóbrega",
            "Hilary Gong Chukwah": "Hilary Gong",
            "Luís Marques Almeida Vieira Silva ": "Luís Silva",
            "Lirim Kastrati": "Lirim Kastrati II",
            "Juan Fernández Blanco": "Juan Fernández",
            "Francisco Javier Álvarez Rodríguez": "Fran Álvarez",
            "Saïd Hamulić": "Saïd Hamulic",
            "Jin-Hyun Lee": "Lee Jin-Hyun",
            "Matías Nahuel Leiva Esquivel": "Matías Nahuel",
            "Tudor Băluţă": "Tudor Baluta",
            "Peter Pokorný": "Peter Pokorny",
            "Arnau Ortiz Sánchez": "Arnau Ortiz",
            "Aleks Petkov": "Alex Petkov",
            "Krzystof Kurowski": "Krzysztof Kurowski",
            "Yegor Sharabura ": "Yehor Sharabura",
            "Taras Romanczuk": "Taras Wiktorowicz Romanczuk",
            "Adrián Diéguez Grande": "Adrián Diéguez",
            "Mohamed Lamine Diaby-Fadiga": "Mohamed Lamine Diaby",
            "Jesús Imaz Ballesté": "Jesús Imaz",
            "João Gervásio Bragança Moutinho": "João Moutinho",
            "Rui Filipe Cunha Correia": "Nené",
            "Tomás Costa Silva": "Tomás Silva",
            "Kristoffer Normann Hansen": "Kristoffer Hansen",
            "Miguel Villar Alonso": "Miky Villar",
            "Presley Pululu": "Afimico Pululu",
            "Andreas Skovgaard Larsen": "Andreas Skovgaard",
            "Virgil-Eugen Ghiţă": "Virgil Eugen Ghiță",
            "Amir Al Ammari": "Amir Al-Ammari",
            "Mikkel Maigaard Jakobsen": "Mikkel Maigaard",
            "Borja Galán González": "Borja Galán",
            "Adrian Błąd": "Adrian Blad",
            "Alan Bród": "Alan Brod",
            "Sergiy Krykun": "Serhii Krykun",
            "Ravve Assayag": "Rave Assayag",
            "Rafał Janicki": "Rafal Janicki",
            "José Manuel Sánchez Guillén": "Josema Sánchez",
            "Filipe Guterres Nascimento": "Filipe Nascimento",
            "Kamil Lukoszek ": "Kamil Lukoszek",
            "Manuel Sánchez García": "Manu Sánchez",
            "Taofeek Ismaheel": "Taofeek Ajibade Ismaheel",
            "Sergi Samper Montaña": "Sergi Samper",
            "Michal Król": "Michał Król",
            "Christopher Serge Simon": "Christopher Simon",
            "Filip Wójcik": "Filip Wojcik",
            "Mbaye Jacques Ndiaye": "Mbaye Ndiaye",
            "Kacper Wełniak": "Kacper Welniak",
            "Pedro Nuno Fernandes Ferreira": "Pedro Nuno",
            "Adrián Dalmau Vaquer": "Adrián Dalmau",
            "Pau Resta Tell": "Pau Resta",
            "Danny Trejo": "Daniel Trejo Del Río",
            "Martin Remacle": "Martin Christophe Jannick Remacle",
            "Hubert Zwoźny": "H.Zwozny",
            "Stratos Svarnas": "Efstratios Svarnas",
            "Iván López Álvarez": "Ivi López",
            "Jean Carlos Silva Rocha": "Jean Carlos",
            "Jonatan Braut Brunes": "Jonatan Braut-Brunes",
            "Erick Ouma Otieno": "Erick Otieno",
            "Peter Baráth": "Péter Baráth",
            "Adriano Luís Amorim Santos": "Adriano Luis Amorim Santos",
            "Jesus Antonio Diaz Gomez": "Jesús Díaz",
            "Conrado Buchanelli Holz": "Conrado",
            "Bogdan Viunnyk": "Bohdan Vyunnyk",
            "Camilo Andrés Mena Márquez": "Camilo Mena",
            "Loup-Diwan Gueho": "Loup Diwan Gueho",
        }

        self.teams_to_change = {
            "Lech Poznań": "Lech Poznan",
            "Cracovia": "Cracovia Kraków",
            "WKS Slask Wrocław": "Śląsk Wrocław",
            "FKS Stal Mielec": "Stal Mielec",
            "KS Gornik Zabrze": "Górnik Zabrze",
            "Motor Lublin SA": "Motor Lublin",
            "KS Raków Czestochowa": "Raków Częstochowa",
            "MKS Puszcza Niepołomice": "Puszcza Niepołomice",
        }

    def _format_columns(self, df):
        """
        Format columns, converting to appropriate data types

        Args:
            df (pd.DataFrame): Input DataFrame

        Returns:
            pd.DataFrame: Formatted DataFrame
        """
        for col in df.columns:
            if col not in ["player_name", "minutes_skillcorner"]:
                df[col] = df[col].astype(int, errors="ignore")
            elif col in ["minutes_skillcorner"]:
                df[col] = df[col].round(2)
        return df

    def _clean_data(self, df, columns_to_keep):
        """
        Clean and prepare the DataFrame

        Args:
            df (pd.DataFrame): Input DataFrame
            columns_to_keep (list): List of columns to retain

        Returns:
            pd.DataFrame: Cleaned and filtered DataFrame
        """
        # Replace extra spaces in player names
        df["player_name"] = df["player_name"].apply(lambda x: x.replace("  ", " "))

        # Apply name changes
        df["player_name"] = df.apply(lambda x: self.names_to_change.get(x["player_name"], x["player_name"]), axis=1)

        # Apply team changes
        df["team_name"] = df.apply(lambda x: self.teams_to_change.get(x["team_name"], x["team_name"]), axis=1)

        # Apply match name changes
        df["match_name"] = df.apply(lambda x: self.teams_to_change.get(x["match_name"], x["match_name"]), axis=1)

        # Filter and select columns
        return df[columns_to_keep]

    def process_physical_output(self):
        """
        Process physical output data

        Returns:
            pd.DataFrame: Processed physical output DataFrame
        """
        # Read CSV file
        df = pd.read_csv(f"/Users/bartek/Downloads/SkillCorner-{self.file_date}-physical-output.csv", sep=";")

        # Filter for specific season
        df = df[df["Season"] == "2024/2025"]

        # Columns to keep and rename
        columns_to_keep = [
            "Player",
            "Team",
            "Match",
            "Date",
            "Competition",
            "Minutes",
            "Distance",
            "Running Distance",
            "HSR Distance",
            "HSR Count",
            "Sprint Distance",
            "Sprint Count",
            "HI Distance",
            "HI Count",
        ]

        # Rename columns
        column_mapping = {
            "Player": "player_name",
            "Team": "team_name",
            "Match": "match_name",
            "Date": "match_date",
            "Competition": "competition_name",
            "Minutes": "minutes_played_per_match",
        }
        df = df.rename(columns=column_mapping)

        # Clean and filter data
        processed_df = self._clean_data(
            df,
            [
                "player_name",
                "team_name",
                "match_name",
                "match_date",
                "competition_name",
                "minutes_played_per_match",
                "Distance",
                "Running Distance",
                "HSR Distance",
                "HSR Count",
                "Sprint Distance",
                "Sprint Count",
                "HI Distance",
                "HI Count",
            ],
        )

        return processed_df

    def process_overcoming_pressure(self):
        """
        Process overcoming pressure data

        Returns:
            pd.DataFrame: Processed overcoming pressure DataFrame
        """
        # Read CSV file
        df = pd.read_csv(f"/Users/bartek/Downloads/SkillCorner-{self.file_date}-overcoming-pressure.csv", sep=";")

        # Filter for match date
        df = df[df["match_date"] >= self.match_date_filter]

        # Clean and filter data
        processed_df = self._clean_data(
            df,
            [
                "player_name",
                "team_name",
                "match_name",
                "match_date",
                "competition_name",
                "minutes_played_per_match",
                "count_pressures_received_per_match",
                "count_forced_losses_under_pressure_per_match",
                "count_ball_retentions_under_pressure_per_match",
                "count_difficult_pass_attempts_under_pressure_per_match",
                "count_completed_difficult_passes_under_pressure_per_match",
                "count_pass_attempts_under_pressure_per_match",
                "count_completed_passes_under_pressure_per_match",
                "count_dangerous_pass_attempts_under_pressure_per_match",
                "count_completed_dangerous_passes_under_pressure_per_match",
            ],
        )

        return processed_df

    def process_passing(self):
        """
        Process passing data

        Returns:
            pd.DataFrame: Processed passing DataFrame
        """
        # Read CSV file
        df = pd.read_csv(f"/Users/bartek/Downloads/SkillCorner-{self.file_date}-passing.csv", sep=";")

        # Filter for match date
        df = df[df["match_date"] >= self.match_date_filter]

        # Clean and filter data
        processed_df = self._clean_data(
            df,
            [
                "player_name",
                "team_name",
                "match_name",
                "match_date",
                "competition_name",
                "minutes_played_per_match",
                "count_opportunities_to_pass_to_runs_per_match",
                "count_pass_attempts_to_runs_per_match",
                "count_completed_pass_to_runs_per_match",
                "count_runs_by_teammate_per_match",
                "count_completed_pass_to_runs_leading_to_shot_per_match",
                "count_completed_pass_to_runs_leading_to_goal_per_match",
                "count_pass_opportunities_to_dangerous_runs_per_match",
                "count_pass_attempts_to_dangerous_runs_per_match",
                "count_completed_pass_to_dangerous_runs_per_match",
            ],
        )

        return processed_df

    def process_running_off_ball(self):
        """
        Process running off-ball data

        Returns:
            pd.DataFrame: Processed running off-ball DataFrame
        """
        # Read CSV file
        df = pd.read_csv(f"/Users/bartek/Downloads/SkillCorner-{self.file_date}-running-off-ball.csv", sep=";")

        # Filter for match date
        df = df[df["match_date"] >= self.match_date_filter]

        # Clean and filter data
        processed_df = self._clean_data(
            df,
            [
                "player_name",
                "team_name",
                "match_name",
                "match_date",
                "competition_name",
                "minutes_played_per_match",
                "count_runs_per_match",
                "count_dangerous_runs_per_match",
                "count_runs_leading_to_goal_per_match",
                "count_runs_targeted_per_match",
                "count_runs_received_per_match",
                "count_runs_leading_to_shot_per_match",
                "count_dangerous_runs_targeted_per_match",
                "count_dangerous_runs_received_per_match",
            ],
        )

        return processed_df

    def save_processed_data(self, output_dir="processed_data"):
        """
        Save processed data to TSV files

        Args:
            output_dir (str, optional): Directory to save processed files. Defaults to 'processed_data'.
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Process and save each dataset
        datasets = {
            "physical_output": self.process_physical_output(),
            "overcoming_pressure": self.process_overcoming_pressure(),
            "passing": self.process_passing(),
            "running_off_ball": self.process_running_off_ball(),
        }

        # Save each dataset to a TSV file
        for name, df in datasets.items():
            output_path = os.path.join(output_dir, f"{name}_{self.file_date}.tsv")
            df.to_csv(output_path, sep="\t", index=False)
            print(f"Saved {name} data to {output_path}")


# Example usage
if __name__ == "__main__":
    processor = SkillCornerDataProcessor(file_date="2024-12-09", match_date_filter="2024-06-01")
    processor.save_processed_data()
