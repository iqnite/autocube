import matplotlib.pyplot as plt
import matplotlib.patches as patches

from logic.cube import Cube


def draw_cube_net(cube_state: dict[str, list[list[str]]]) -> None:
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_aspect("equal")
    ax.axis("off")

    #      [U]
    #   [L][F][R][B]
    #      [D]
    offsets = {
        "U": (3, 6),
        "L": (0, 3),
        "F": (3, 3),
        "R": (6, 3),
        "B": (9, 3),
        "D": (3, 0),
    }
    color_map = {
        "D": "#FFFFFF",  # White
        "U": "#FFD500",  # Yellow
        "R": "#C41E3A",  # Red
        "L": "#FF5800",  # Orange
        "F": "#009E60",  # Green
        "B": "#0051BA",  # Blue
    }
    for face_name, (start_x, start_y) in offsets.items():
        face_grid = cube_state[face_name]
        for row in range(3):
            for col in range(3):
                color_initial = face_grid[row][col]
                hex_color = color_map.get(color_initial, "#888888")
                rect_x = start_x + col
                rect_y = start_y + (2 - row)
                rect = patches.Rectangle(
                    (rect_x, rect_y),
                    1,
                    1,
                    linewidth=2,
                    edgecolor="black",
                    facecolor=hex_color,
                )
                ax.add_patch(rect)
    ax.set_xlim(-1, 13)
    ax.set_ylim(-1, 10)
    plt.tight_layout()


def visualize_cube(cube: Cube, live: bool = False):
    draw_cube_net(cube.state)
    if live:
        plt.pause(0.1)
    else:
        plt.show()
