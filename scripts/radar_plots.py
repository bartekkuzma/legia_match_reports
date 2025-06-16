import matplotlib.pyplot as plt
from mplsoccer import Radar, grid

from ..constants import Constants


def plot_single_player_radar(
    single_radar, params, low, high, lower_is_better, directory="/Users/bartek/test_vizualizations/"
):

    radar = Radar(
        params,
        low,
        high,
        lower_is_better=lower_is_better,
        # whether to round any of the labels to integers instead of decimal places
        round_int=[False] * len(params),
        num_rings=4,  # the number of concentric circles (excluding center circle)
        # if the ring_width is more than the center_circle_radius then
        # the center circle radius will be wider than the width of the concentric circles
        ring_width=1,
        center_circle_radius=1,
    )

    # creating the figure using the grid function from mplsoccer:
    fig, axs = grid(
        figheight=14,
        grid_height=0.915,
        title_height=0.06,
        endnote_height=0.025,
        title_space=0,
        endnote_space=0,
        grid_key="radar",
        axis=False,
    )
    fig.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
    for ax in axs.values():
        ax.set_facecolor(Constants.DARK_BACKGROUND_COLOR)

    # plot the radar
    radar.setup_axis(ax=axs["radar"], facecolor=Constants.DARK_BACKGROUND_COLOR)
    rings_inner = radar.draw_circles(
        ax=axs["radar"], facecolor=Constants.LIGHTGREY_COLOR, edgecolor=Constants.SALMON_COLOR, lw=1.5
    )

    radar_output = radar.draw_radar(
        single_radar["values"],
        ax=axs["radar"],
        kwargs_radar={"facecolor": single_radar["color1"]},
        kwargs_rings={"facecolor": single_radar["color2"]},
    )
    radar_poly, rings_outer, vertices = radar_output
    range_labels = radar.draw_range_labels(
        ax=axs["radar"], fontsize=25, color=Constants.LIGHT_TEXT_COLOR, font=Constants.FONT
    )
    param_labels = radar.draw_param_labels(
        ax=axs["radar"], fontsize=25, color=Constants.LIGHT_TEXT_COLOR, font=Constants.FONT
    )

    # adding the endnote and title text (these axes range from 0-1, i.e. 0, 0 is the bottom left)
    # Note we are slightly offsetting the text from the edges by 0.01 (1%, e.g. 0.99)
    endnote_text = axs["endnote"].text(
        0.99,
        0.5,
        "Values are per-90 minutes.\nRadar limits based on Ekstraklasa players\nwith 300+ minutes in the position.",
        color=Constants.LIGHT_TEXT_COLOR,
        font=Constants.FONT,
        fontsize=15,
        ha="right",
        va="center",
    )
    title1_text = axs["title"].text(
        0.01,
        0.65,
        single_radar["name"],
        fontsize=25,
        font=Constants.FONT,
        ha="left",
        va="center",
        color=Constants.LIGHT_TEXT_COLOR,
    )
    title2_text = axs["title"].text(
        0.01,
        0.25,
        single_radar["team"],
        fontsize=20,
        font=Constants.FONT,
        ha="left",
        va="center",
        color=Constants.SALMON_COLOR,
    )
    title3_text = axs["title"].text(
        0.99,
        0.65,
        single_radar["title"],
        fontsize=25,
        font=Constants.FONT,
        ha="right",
        va="center",
        color=Constants.LIGHT_TEXT_COLOR,
    )
    title4_text = axs["title"].text(
        0.99,
        0.25,
        single_radar["subtitle"],
        fontsize=20,
        font=Constants.FONT,
        ha="right",
        va="center",
        color=Constants.SALMON_COLOR,
    )

    fig.savefig(
        f"{directory}/single_{single_radar['type']}_{single_radar['name'].replace(' ', '_').lower()}_{single_radar['team'].replace('/', '_').replace(' ', '_').lower()}_radar.png",
        facecolor=fig.get_facecolor(),
        dpi=Constants.DPI,
        bbox_inches="tight",
        pad_inches=Constants.PAD_INCHES,
    )
    plt.show()
    return fig


def plot_comparison_players_radar(
    player1,
    player2,
    params,
    low,
    high,
    lower_is_better,
    directory="/Users/bartek/test_vizualizations/",
    avg=None,
    avg_color="mediumspringgreen",
):

    radar = Radar(
        params,
        low,
        high,
        lower_is_better=lower_is_better,
        # whether to round any of the labels to integers instead of decimal places
        round_int=[False] * len(params),
        num_rings=4,  # the number of concentric circles (excluding center circle)
        # if the ring_width is more than the center_circle_radius then
        # the center circle radius will be wider than the width of the concentric circles
        ring_width=1,
        center_circle_radius=1,
    )

    # creating the figure using the grid function from mplsoccer:
    fig, axs = grid(
        figheight=14,
        grid_height=0.915,
        title_height=0.06,
        endnote_height=0.025,
        title_space=0,
        endnote_space=0,
        grid_key="radar",
        axis=False,
    )
    fig.set_facecolor(Constants.DARK_BACKGROUND_COLOR)
    for ax in axs.values():
        ax.set_facecolor(Constants.DARK_BACKGROUND_COLOR)

    # plot the radar
    radar.setup_axis(ax=axs["radar"], facecolor=Constants.DARK_BACKGROUND_COLOR)
    rings_inner = radar.draw_circles(
        ax=axs["radar"], facecolor=Constants.LIGHTGREY_COLOR, edgecolor=Constants.SALMON_COLOR, lw=1.5
    )

    if isinstance(avg, list) or avg is None:
        compare_dict = {
            "facecolor": player2["color"],
            "alpha": 0.4,
            "edgecolor": player2["color"],
            "lw": 3,
            "zorder": 5,
        }
    else:
        compare_dict = {
            "facecolor": (0, 0, 0, 0),
            "edgecolor": player2["color"],
            "lw": 3,
            "zorder": 6,
        }

    radar_output = radar.draw_radar_compare(
        player1["values"],
        player2["values"],
        ax=axs["radar"],
        kwargs_radar={
            "facecolor": player1["color"],
            "alpha": 0.4,
            "edgecolor": player1["color"],
            "lw": 3,
            "zorder": 4,
        },
        kwargs_compare=compare_dict,
    )
    if isinstance(avg, list):
        radar3, vertices3 = radar.draw_radar_solid(
            avg, ax=axs["radar"], kwargs={"facecolor": (0, 0, 0, 0), "edgecolor": avg_color, "lw": 3, "zorder": 10}
        )

    radar_poly, radar_poly2, vertices1, vertices2 = radar_output
    range_labels = radar.draw_range_labels(
        ax=axs["radar"], fontsize=25, font=Constants.FONT, color=Constants.LIGHT_TEXT_COLOR
    )

    param_labels = radar.draw_param_labels(
        ax=axs["radar"], fontsize=25, font=Constants.FONT, color=Constants.LIGHT_TEXT_COLOR
    )

    axs["radar"].scatter(
        vertices1[:, 0],
        vertices1[:, 1],
        c=player1["color"],
        edgecolors=Constants.LIGHT_TEXT_COLOR,
        marker="o",
        s=100,
        zorder=6,
    )
    axs["radar"].scatter(
        vertices2[:, 0],
        vertices2[:, 1],
        c=player2["color"],
        edgecolors=Constants.LIGHT_TEXT_COLOR,
        marker="o",
        s=100,
        zorder=6,
    )

    # adding the endnote and title text (these axes range from 0-1, i.e. 0, 0 is the bottom left)
    # Note we are slightly offsetting the text from the edges by 0.01 (1%, e.g. 0.99)
    endnote_text = axs["endnote"].text(
        0.99,
        0.5,
        "Values are per-90 minutes.\nRadar limits based on Ekstraklasa players\nwith 500+ minutes in the position\nfrom 2019/2020 season.",
        color=Constants.LIGHT_TEXT_COLOR,
        font=Constants.FONT,
        fontsize=15,
        ha="right",
        va="center",
    )
    title1_text = axs["title"].text(
        0.01, 0.65, player1["name"], fontsize=25, font=Constants.FONT, ha="left", va="center", color=player1["color"]
    )
    title2_text = axs["title"].text(
        0.01, 0.25, player1["team"], fontsize=20, font=Constants.FONT, ha="left", va="center", color=player1["color"]
    )
    title3_text = axs["title"].text(
        0.99, 0.65, player2["name"], fontsize=25, font=Constants.FONT, ha="right", va="center", color=player2["color"]
    )
    title4_text = axs["title"].text(
        0.99, 0.25, player2["team"], fontsize=20, font=Constants.FONT, ha="right", va="center", color=player2["color"]
    )

    fig.savefig(
        f"{directory}/comparison_{player1['type']}_{player1['name'].replace(' ', '_').lower()}_{player1['team'].replace('/', '_').replace(' ', '_').lower()}_vs_{player2['name'].replace(' ', '_').lower()}_{player2['team'].replace('/', '_').replace(' ', '_').lower()}_radar.png",
        facecolor=fig.get_facecolor(),
        dpi=Constants.DPI,
        bbox_inches="tight",
        pad_inches=Constants.PAD_INCHES,
    )
    plt.show()
    return fig
