from logic.cube import Algorithm, Cube

from tools.visualizer import visualize_cube


def solve_cube(cube: Cube):
    down_cross(cube)


def down_cross(cube: Cube):
    correct = 0
    while correct < 4:
        # visualize_cube(cube, live=True)
        white_edges = cube.find_edges_of_color(color="D")
        correct = 0

        for edge in white_edges:
            face, row, col = edge
            if face == "D":
                adj_face = cube.get_face_adjacent_to_edge(edge)
                if cube.get_color_adjacent_to_edge(edge) == cube.state[adj_face][1][1]:
                    correct += 1
                    continue
                cube.apply_algorithm(Algorithm(f"{adj_face}2"))
                break

            if face == "U":
                if not cube.is_bleeding_edge(edge):
                    cube.apply_algorithm(Algorithm("U"))
                    break
                adj_face = cube.get_face_adjacent_to_edge(edge)
                cube.apply_algorithm(Algorithm(f"{adj_face}2"))
                break

            if face in ["L", "R", "F", "B"]:
                adj_face = cube.get_face_adjacent_to_edge(edge)
                if adj_face in ["U", "D"]:
                    cube.apply_algorithm(Algorithm(face))
                    break
                is_two_steps_away = row == 0
                is_clockwise = (not is_two_steps_away) and col == 0
                if cube.is_bleeding_edge(edge):
                    modifier = "2" if is_two_steps_away else "" if is_clockwise else "'"
                    cube.apply_algorithm(Algorithm(f"{adj_face}{modifier}"))
                    break
                mod_first = "'" if is_clockwise else ""
                mod_last = "" if is_clockwise else "'"
                cube.apply_algorithm(Algorithm(f"{adj_face}{mod_first}"))
                cube.apply_algorithm(Algorithm("U"))
                cube.apply_algorithm(Algorithm(f"{adj_face}{mod_last}"))
                break
