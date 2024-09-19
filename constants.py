import seaborn as sns


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
        "p3": 70.0
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
    }

    FONT = "Avenir"
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

    # Additional color mappings
    POSITIVE_COLOR = COLORS["green"]
    NEGATIVE_COLOR = COLORS["red"]
    NEUTRAL_COLOR = COLORS["yellow"]

    DPI = 300
    PAD_INCHES = 0

    CMAPLIST_XPASS = sns.color_palette("Spectral")
    