"""
Contains functions for solving every layer of the cube.
"""

from typing import Literal

from logic import mappings
from logic.cube import Algorithm, Cube, Facelet


def solve_cube(cube: Cube):
    fl_cross(cube)
    fl_corners(cube)
    ml(cube)
    eoll(cube)
    ocll(cube)
    cpll(cube)
    epll(cube)
    last_rotation(cube)


def fl_cross(cube: Cube):
    correct = 0
    non_bleeding_u_edges = 0
    while correct < 4:
        correct = 0
        white_edges = cube.get_edges_of_color(color="D")
        for edge in white_edges:
            face, row, col = edge.tuple
            adj_face = cube.get_face_adjacent_to_edge(edge)
            if face == "D":
                if cube.get_color_adjacent_to_edge(edge) == cube.state[adj_face][1][1]:
                    correct += 1
                    continue
                cube.apply_algorithm(Algorithm(f"{adj_face}2"))
                break
            if face == "U":
                if cube.edge_is_bleeding(edge):
                    non_bleeding_u_edges = 0
                    cube.apply_algorithm(Algorithm(f"{adj_face}2"))
                    break
                non_bleeding_u_edges += 1
                if non_bleeding_u_edges >= 4:
                    non_bleeding_u_edges = 0
                    cube.apply_algorithm(Algorithm("U"))
                    break
            if face in ["L", "R", "F", "B"]:
                if adj_face == "D":
                    cube.apply_algorithm(Algorithm(f"{face}2"))
                    break
                if adj_face == "U":
                    opposite_facelet = Facelet(face, 2, 1)
                    if opposite_facelet.face == face and cube.edge_is_bleeding(
                        opposite_facelet
                    ):
                        # Do not rotate the face if it is already correct
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


def fl_corners(cube: Cube):
    while True:
        white_corners = cube.get_corners_of_color(color="D")
        unsolved_corners = []
        for corner in white_corners:
            face, row, col = corner.tuple
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
        front_face = mappings.FRONT_FACE_FOR_CORNER[frozenset(target["side_faces"])]
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


def ml(cube: Cube):
    up_rotations = 0
    while True:
        unsolved_edges: list[frozenset[str]] = []
        for face in ["F", "R", "B", "L"]:
            edge = Facelet(face, 1, 0)
            adj_face = cube.get_face_adjacent_to_edge(edge)
            if (
                cube.state[face][1][1] == cube.state[face][1][0]
                and cube.state[adj_face][1][1] == cube.state[adj_face][1][2]
            ):
                continue
            unsolved_edges.append(frozenset((face, adj_face)))
        if not unsolved_edges:
            break
        up_edges = list(map(lambda args: Facelet(*args), mappings.UP_EDGES))
        for edge in up_edges:
            edge_colors = (
                cube.state[edge.face][edge.row][edge.col],
                cube.get_color_adjacent_to_edge(edge),
            )
            if frozenset(edge_colors) in unsolved_edges:
                adj_face, face = edge_colors
                if cube.edge_is_bleeding(edge):
                    up_rotations = 0
                    cube.apply_algorithm(
                        insert_edge(
                            (
                                "right"
                                if (face, adj_face) in mappings.RIGHT_EDGE_INSERTIONS
                                else "left"
                            ),
                            face,
                        )
                    )
                    break
        else:
            cube.apply_algorithm(Algorithm("U"))
            up_rotations += 1
            if up_rotations >= 4:
                up_rotations = 0
                # If no edges are in the up layer, move one there
                face, adj_face = unsolved_edges[0]
                cube.apply_algorithm(
                    insert_edge(
                        (
                            "right"
                            if (face, adj_face) in mappings.RIGHT_EDGE_INSERTIONS
                            else "left"
                        ),
                        face,
                    )
                )


def eoll(cube: Cube):
    up_state = cube.state["U"]
    for _, row, col in mappings.UP_EDGES:
        if up_state[row][col] != "U":
            break
    else:
        return
    for pattern, algorithm in (
        (mappings.UP_CROSS_CORNERS, "F U R U' R' F'"),
        (mappings.UP_CROSS_LINES, "R U R' U' R' F R F'"),
    ):
        for ((r1, c1), (r2, c2)), ref_face in pattern.items():
            if up_state[r1][c1] == "U" and up_state[r2][c2] == "U":
                cube.apply_algorithm(
                    Algorithm(algorithm, translation_reference=ref_face)
                )
                return
    cube.apply_algorithm(Algorithm("R U2 R2 F R F' U2 R' F R F'"))


def ocll(cube: Cube):
    for _ in range(4):
        up_adj_colors = tuple(
            cube.state[face][0][col] for face in ("B", "R", "F", "L") for col in (2, 0)
        )
        adj_ups = tuple(i for i, color in enumerate(up_adj_colors) if color == "U")
        if len(adj_ups) == 0:
            return
        if adj_ups in mappings.UP_CORNER_ALGORITHMS:
            cube.apply_algorithm(Algorithm(mappings.UP_CORNER_ALGORITHMS[adj_ups]))
            return
        cube.apply_algorithm(Algorithm("U"))
    raise RuntimeError("Cannot find solution for last layer corners.")


def cpll(cube: Cube):
    headlights_found = 0
    headlights_face = None
    for face in ("F", "B", "R", "L"):
        if cube.state[face][0][0] == cube.state[face][0][2]:
            headlights_found += 1
            if headlights_found > 1:
                return
            headlights_face = face
    if headlights_found == 1:
        cube.apply_algorithm(
            Algorithm(
                "U' R2 B2 R F R' B2 R F' R", translation_reference=headlights_face
            )
        )
        return
    cube.apply_algorithm(Algorithm("F R U' R' U' R U R' F' R U R' U' R' F R F'"))


def epll(cube: Cube):
    for face in ("F", "B", "R", "L"):
        right_face = mappings.EDGE_MAP[(face, 1, 2)][0]
        if (
            cube.state[face][0][0] == cube.state[mappings.OPPOSITE_FACES[face]][0][1]
            and cube.state[face][0][1]
            == cube.state[mappings.OPPOSITE_FACES[face]][0][0]
        ):
            cube.apply_algorithm(
                Algorithm("R2 L2 D R2 L2 D2 R2 L2 D R2 L2 D2", translation_reference=face)
            )
            return
        if (
            cube.state[face][0][1] == cube.state[right_face][0][0]
            and cube.state[face][0][0] == cube.state[right_face][0][1]
        ):
            cube.apply_algorithm(
                Algorithm(
                    "R' U' R2 U R U R' U' R U R U' R U' R'", translation_reference=face
                )
            )
            return
        if cube.state[face][0][0] == cube.state[face][0][1]:
            if (
                cube.state[mappings.OPPOSITE_FACES[face]][0][0]
                == cube.state[mappings.OPPOSITE_FACES[face]][0][1]
            ):
                return
            if (
                cube.state[right_face][0][1]
                == cube.state[mappings.OPPOSITE_FACES[right_face]][0][0]
            ):
                cube.apply_algorithm(
                    Algorithm(
                        "R' U R' U' R' U' R' U R U R2", translation_reference=face
                    )
                )
                return
            cube.apply_algorithm(
                Algorithm("R2 U' R' U' R U R U R U' R", translation_reference=face)
            )
            return
    raise RuntimeError("Cannot find solution for last layer edge orientation.")


def last_rotation(cube: Cube):
    while cube.state["F"][0][0] != "F":
        cube.apply_algorithm(Algorithm("U"))


def sexy_move(reference_front: str | None = None) -> Algorithm:
    return Algorithm("R U R' U'", translation_reference=reference_front)


def insert_edge(
    side: Literal["left", "right"], reference_front: str | None = None
) -> Algorithm:
    if side == "right":
        return Algorithm("U F' R' U' R F R' U R", translation_reference=reference_front)
    return Algorithm("U' F L U L' F' L U' L'", translation_reference=reference_front)
