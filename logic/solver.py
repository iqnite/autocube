from logic.cube import Algorithm, Cube

from tools.visualizer import visualize_cube

EDGE_MAP = {
    # Up layer edges
    ("U", 2, 1): ("F", 0, 1),
    ("F", 0, 1): ("U", 2, 1),
    ("U", 0, 1): ("B", 0, 1),
    ("B", 0, 1): ("U", 0, 1),
    ("U", 1, 0): ("L", 0, 1),
    ("L", 0, 1): ("U", 1, 0),
    ("U", 1, 2): ("R", 0, 1),
    ("R", 0, 1): ("U", 1, 2),
    # Down layer edges
    ("D", 0, 1): ("F", 2, 1),
    ("F", 2, 1): ("D", 0, 1),
    ("D", 2, 1): ("B", 2, 1),
    ("B", 2, 1): ("D", 2, 1),
    ("D", 1, 0): ("L", 2, 1),
    ("L", 2, 1): ("D", 1, 0),
    ("D", 1, 2): ("R", 2, 1),
    ("R", 2, 1): ("D", 1, 2),
    # Middle layer edges
    ("F", 1, 0): ("L", 1, 2),
    ("L", 1, 2): ("F", 1, 0),
    ("F", 1, 2): ("R", 1, 0),
    ("R", 1, 0): ("F", 1, 2),
    ("B", 1, 0): ("R", 1, 2),
    ("R", 1, 2): ("B", 1, 0),
    ("B", 1, 2): ("L", 1, 0),
    ("L", 1, 0): ("B", 1, 2),
}


def solve_cube(cube: Cube):
    down_cross(cube)


def down_cross(cube: Cube):
    correct = 0
    while correct < 4:
        # visualize_cube(cube, live=True)
        white_edges = find_edges_of_color(cube, color="D")
        correct = 0

        for edge in white_edges:
            face, row, col = edge
            if face == "D":
                adj_face = get_adjacent_face(edge)
                if get_adjacent_color(cube, edge) == cube.state[adj_face][1][1]:
                    correct += 1
                    continue
                cube.apply_algorithm(Algorithm(f"{adj_face}2"))
                break

            if face == "U":
                if not is_bleeding_edge(cube, edge):
                    cube.apply_algorithm(Algorithm("U"))
                    break
                adj_face = get_adjacent_face(edge)
                cube.apply_algorithm(Algorithm(f"{adj_face}2"))
                break

            if face in ["L", "R", "F", "B"]:
                adj_face = get_adjacent_face(edge)
                if adj_face in ["U", "D"]:
                    cube.apply_algorithm(Algorithm(face))
                    break
                is_two_steps_away = row == 0
                is_clockwise = (not is_two_steps_away) and col == 0
                if is_bleeding_edge(cube, edge):
                    modifier = "2" if is_two_steps_away else "" if is_clockwise else "'"
                    cube.apply_algorithm(Algorithm(f"{adj_face}{modifier}"))
                    break
                mod_first = "'" if is_clockwise else ""
                mod_last = "" if is_clockwise else "'"
                cube.apply_algorithm(Algorithm(f"{adj_face}{mod_first}"))
                cube.apply_algorithm(Algorithm("U"))
                cube.apply_algorithm(Algorithm(f"{adj_face}{mod_last}"))
                break


def find_edges_of_color(cube: Cube, color: str = "D") -> list[tuple[str, int, int]]:
    edges = []
    valid_coords = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for face in ["U", "D", "L", "R", "F", "B"]:
        for row, col in valid_coords:
            if cube.state[face][row][col] == color:
                edges.append((face, row, col))
    return edges


def get_adjacent_face(edge: tuple[str, int, int]) -> str:
    return EDGE_MAP[edge][0]


def get_adjacent_color(cube: Cube, edge: tuple[str, int, int]) -> str:
    adj_face, adj_row, adj_col = EDGE_MAP[edge]
    return cube.state[adj_face][adj_row][adj_col]


def is_bleeding_edge(cube: Cube, edge: tuple[str, int, int]) -> bool:
    adj_color = get_adjacent_color(cube, edge)
    adj_face = get_adjacent_face(edge)
    return adj_color == cube.state[adj_face][1][1]
