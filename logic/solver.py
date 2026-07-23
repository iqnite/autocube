from logic.cube import Algorithm, Cube
from tools.visualizer import visualize_cube
from logic.constants import FRONT_FACE_FOR_CORNER


def solve_cube(cube: Cube):
    down_cross(cube)
    down_corners(cube)


def down_cross(cube: Cube):
    correct = 0
    while correct < 4:
        correct = 0
        white_edges = cube.find_edges_of_color(color="D")
        for edge in white_edges:
            face, row, col = edge
            adj_face = cube.get_face_adjacent_to_edge(edge)
            if face == "D":
                if cube.get_color_adjacent_to_edge(edge) == cube.state[adj_face][1][1]:
                    correct += 1
                    continue
                cube.apply_algorithm(Algorithm(f"{adj_face}2"))
                break
            if face == "U":
                if not cube.edge_is_bleeding(edge):
                    cube.apply_algorithm(Algorithm("U"))
                    break
                cube.apply_algorithm(Algorithm(f"{adj_face}2"))
                break
            if face in ["L", "R", "F", "B"]:
                if adj_face in ["U", "D"]:
                    cube.apply_algorithm(Algorithm(face))
                    break
                is_two_steps_away = row == 0
                is_clockwise = (not is_two_steps_away) and col == 0
                if cube.edge_is_bleeding(edge):
                    modifier = "2" if is_two_steps_away else "" if is_clockwise else "'"
                    cube.apply_algorithm(Algorithm(f"{adj_face}{modifier}"))
                    break
                mod_first = "'" if is_clockwise else ""
                mod_last = "" if is_clockwise else "'"
                cube.apply_algorithm(
                    Algorithm(f"{adj_face}{mod_first} U {adj_face}{mod_last}")
                )
                break


def down_corners(cube: Cube):
    while True:
        visualize_cube(cube, live=True)
        white_corners = cube.find_corners_of_color(color="D")
        unsolved_corners = []
        for corner in white_corners:
            face, row, col = corner
            adj_faces = cube.get_faces_adjacent_to_corner(corner)
            colors = cube.get_colors_adjacent_to_corner(corner)
            if face in ("U", "D"):
                side_faces = adj_faces
            else:
                side_1 = face
                side_2 = (
                    adj_faces[0] if adj_faces[0] not in ("U", "D") else adj_faces[1]
                )
                side_faces = (side_1, side_2)

            center1 = cube.state[side_faces[0]][1][1]
            center2 = cube.state[side_faces[1]][1][1]
            is_correct_column = {colors[0], colors[1]} == {center1, center2}
            if face == "D" and is_correct_column:
                continue

            unsolved_corners.append(
                {
                    "corner": corner,
                    "side_faces": side_faces,
                    "is_correct_column": is_correct_column,
                    "face": face,
                    "adj_faces": adj_faces,
                    "colors": colors,
                }
            )

        if not unsolved_corners:
            break

        unsolved_corners.sort(key=lambda x: sorted(x["colors"]))
        target = unsolved_corners[0]
        front_face = FRONT_FACE_FOR_CORNER[frozenset(target["side_faces"])]
        in_bottom_layer = target["face"] == "D" or "D" in target["adj_faces"]
        if in_bottom_layer:
            cube.apply_algorithm(
                Algorithm("R U R' U'", translation_reference=front_face)
            )
        else:
            if target["is_correct_column"]:
                if target["face"] == "U":
                    cube.apply_algorithm(sexy_move(front_face) * 3)
                elif target["face"] == front_face:
                    cube.apply_algorithm(-sexy_move(front_face))
                else:
                    cube.apply_algorithm(
                        Algorithm("R U R'", translation_reference=front_face)
                    )
            else:
                cube.apply_algorithm(Algorithm("U"))


def sexy_move(reference_front: str) -> Algorithm:
    return Algorithm("R U R' U'", translation_reference=reference_front)
