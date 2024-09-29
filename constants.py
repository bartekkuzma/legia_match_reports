import seaborn as sns
from matplotlib import font_manager


class Constants:
    """
    A class to store constant values used in the GoalsAnalysis class.
    """
    PITCH_DIMS = {
        "pitch_length": 120.0,
        "pitch_width": 80.0,
        "penalty_box_length": 18.0,
        "penalty_box_left_band": 18.0,
        "eleven_metres": 12.0,
        "final_third": 40.0,
        "six_yard_box": 30.0,
        "b2_zone": 50.0,
        "p1": 20.0,
        "p2": 50.0,
        "p3": 70.0,
        "zone_14_x": 80.0,
        "zone_14_y": 26.67,
        "zone_14_length": 20.0,
        "zone_14_width": 26.67,
    }

    COLORS = {
        "green": (46/255, 204/255, 113/255, 0.75),
        "yellow": (255/255, 240/255, 0/255, 0.75),
        "red": (242/255, 38/255, 19/255, 0.75),
        "blue": (3/255, 138/255, 255/255, 0.75),
        "black": "black",
        "white": "white",
        "sb_red": '#e21017',
        "sb_grey": '#9a9a9a',
        "dark_grey": "#4A4A4A",
        "medium_dark_grey": "#696969",
        "medium_grey": "#808080",
        "medium_light_grey": "#A9A9A9",
        "light_grey": "#C0C0C0",
        "very_light_grey": "#D3D3D3",
        "almost_white": "#F5F5F5",
        "very_pale_red": "#FFF0F0",
        "pale_red": "#FFE0E0",
        "light_pale_red": "#FFD0D0",
        "light_red": "#FFA0A0",
        "medium_light_red": "#FF7070",
        "medium_red": "#FF4040",
        "strong_red": "#FF0000",
        "sbred": "#E21017",
        "cyan": "cyan",
        "full_yelow": (255/255, 240/255, 0/255, 1),
    }

    STREAMLIT_COLOR = '#0E1117'
    TEXT_COLOR = '#222222'
    BACKGROUND_COLOR = '#d4af37'
    EVEN_ROW_COLOR = "#fffae6"
    ODD_ROW_COLOR = "#fff1d5"
    HEADER_COLOR = "#cdb79e"
    EDGE_COLOR = "black"
    TEAM_FOR_COLOR = "#002B54"
    TEAM_AGAINST_COLOR = "#e2001a"
    DARK_BACKGROUND_COLOR = "#2D2D34"
    LIGHT_TEXT_COLOR = '#FBFEFB'
    SALMON_COLOR = "#B97375"
    OFF_WHITE_COLOR = "#E2DCDE"
    DARKGREEN_COLOR = "#466362"

    # Additional color mappings
    POSITIVE_COLOR = COLORS["green"]
    NEGATIVE_COLOR = COLORS["red"]
    NEUTRAL_COLOR = COLORS["full_yelow"]

    DPI = 300
    PAD_INCHES = 0.1

    CMAPLIST_XPASS = sns.color_palette("Spectral")
    CMAP_FOR_HEATMAP = [
        COLORS["dark_grey"], COLORS["medium_dark_grey"], COLORS["medium_grey"], COLORS["medium_light_grey"],
        COLORS["light_grey"], COLORS["very_light_grey"], COLORS["almost_white"], COLORS["white"], 
        COLORS["very_pale_red"], COLORS["pale_red"], COLORS["light_pale_red"], COLORS["light_red"], 
        COLORS["medium_light_red"], COLORS["medium_red"], COLORS["strong_red"], COLORS["sbred"]
    ]
    CMAP_IND_GOOD = [EVEN_ROW_COLOR, "#fffae6", "#f2fbd2", "#c9ecb4", "#93d3ab", "#35b0ab"]
    CMAP_IND_BAD = ["#fffae6", "#ffbaba", '#ff7b7b', "#ff0000"]
    SHOT_MAP_CMAP = ["#115f9a", "#a6d75b", "#c9e52f", "#d0ee11"]

        # Load the custom font from file and set it up
    FONT_PATH = "resources/Raleway-Regular.ttf"  # Replace this with the actual path to your font file

    @classmethod
    def load_font(cls):
        """Loads and registers the custom font."""
        font_manager.fontManager.addfont(cls.FONT_PATH)
        font_prop = font_manager.FontProperties(fname=cls.FONT_PATH)
        cls.FONT = font_prop.get_name()  # Set the font name to be used

# Initialize font loading at the class level so it is executed once
Constants.load_font()
