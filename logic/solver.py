from typing import Literal

from logic.cube import Algorithm, Cube
from logic.constants import RIGHT_EDGE_INSERTIONS, FRONT_FACE_FOR_CORNER


def solve_cube(cube: Cube):
    down_cross(cube)
    down_corners(cube)
    center_edges(cube)


def down_cross(cube: Cube):
    correct = 0
    while correct < 4:
        correct = 0
        white_edges = cube.get_edges_of_color(color="D")
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
                    if cube.edge_is_bleeding((face, 2, 1)):
                        cube.apply_algorithm(Algorithm("U"))
                        break
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
        white_corners = cube.get_corners_of_color(color="D")
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


def center_edges(cube: Cube):
    while True:
        unsolved_edges = []
        for face in ["F", "R", "B", "L"]:
            edge = (face, 1, 0)
            adj_face = cube.get_face_adjacent_to_edge(edge)
            if cube.state[face][1][1] != cube.state[adj_face][1][1]:
                unsolved_edges.append((face, adj_face))
        if not unsolved_edges:
            break
        up_edge_positions = [("U", 1, 0), ("U", 1, 2), ("D", 1, 0), ("D", 1, 2)]
        for edge_position in up_edge_positions:
            edge = (edge_position[0], edge_position[1], edge_position[2])
            edge_colors = (
                cube.state[edge[0]][edge[1]][edge[2]],
                cube.get_color_adjacent_to_edge(edge),
            )
            if edge_colors in unsolved_edges:
                face, adj_face = edge_colors
                if cube.edge_is_bleeding(edge):
                    cube.apply_algorithm(
                        insert_edge(
                            (
                                "right"
                                if frozenset([face, adj_face]) in RIGHT_EDGE_INSERTIONS
                                else "left"
                            ),
                            face,
                        )
                    )
                    break
                else:
                    cube.apply_algorithm(Algorithm("U"))
                    break
        else:
            # If no edges are in the up layer, move one there
            face, adj_face = unsolved_edges[0]
            cube.apply_algorithm(
                insert_edge(
                    (
                        "right"
                        if frozenset([face, adj_face]) in RIGHT_EDGE_INSERTIONS
                        else "left"
                    ),
                    face,
                )
            )


def sexy_move(reference_front: str | None = None) -> Algorithm:
    return Algorithm("R U R' U'", translation_reference=reference_front)


def insert_edge(
    side: Literal["left", "right"], reference_front: str | None = None
) -> Algorithm:
    if side == "right":
        return Algorithm("U F' R U' R' F R U R'", translation_reference=reference_front)
    return Algorithm("U' F L U L' F' L U' L'", translation_reference=reference_front)
