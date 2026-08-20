"""
Contains functions to automatically fix invalid cube states.
"""

import copy

from logic import mappings as logic_mappings


def is_cube_valid(state: dict[str, list[list[str]]]) -> bool:
    counts = {c: 0 for c in "UDFBRL"}
    for face in state.values():
        for row in face:
            for color in row:
                counts[color] += 1
    if any(v != 9 for v in counts.values()):
        return False
    seen_edges = set()
    unique_edges = set(frozenset([k, v]) for k, v in logic_mappings.EDGE_MAP.items())
    for coord_pair in unique_edges:
        (f1, r1, c1), (f2, r2, c2) = tuple(coord_pair)
        color1, color2 = state[f1][r1][c1], state[f2][r2][c2]
        # Law of Opposites (e.g., U and D cannot be on the same piece)
        if logic_mappings.OPPOSITE_FACES[color1] == color2 or color1 == color2:
            return False
        # Law of Uniqueness
        color_pair = frozenset([color1, color2])
        if color_pair in seen_edges:
            return False
        seen_edges.add(color_pair)
    seen_corners = set()
    unique_corners = set(
        frozenset([k, v[0], v[1]]) for k, v in logic_mappings.CORNER_MAP.items()
    )
    for coord_triplet in unique_corners:
        colors = [state[f][r][c] for f, r, c in coord_triplet]
        # Law of Opposites
        if (
            logic_mappings.OPPOSITE_FACES[colors[0]] in colors
            or logic_mappings.OPPOSITE_FACES[colors[1]] in colors
            or len(set(colors)) < 3
        ):
            return False
        # Law of Uniqueness
        color_triplet = frozenset(colors)
        if color_triplet in seen_corners:
            return False
        seen_corners.add(color_triplet)
    return True


def autofix_scan(
    state: dict[str, list[list[str]]],
) -> tuple[dict[str, list[list[str]]], str]:
    counts = {c: 0 for c in "UDFBRL"}
    for face in state.values():
        for row in face:
            for color in row:
                counts[color] += 1
    surplus = [c for c, count in counts.items() if count > 9]
    deficit = [c for c, count in counts.items() if count < 9]
    if not surplus and not deficit:
        if is_cube_valid(state):
            return state, ""
        else:
            return (
                state,
                "Warning: Counts are correct, but piece geometry is impossible.",
            )
    if sum(count - 9 for count in counts.values() if count > 9) == 1:
        surplus_color = surplus[0]
        deficit_color = deficit[0]
        for face_name, grid in state.items():
            for r in range(3):
                for c in range(3):
                    if r == 1 and c == 1:
                        continue
                    if grid[r][c] == surplus_color:
                        test_state = copy.deepcopy(state)
                        test_state[face_name][r][c] = deficit_color
                        if is_cube_valid(test_state):
                            return (
                                test_state,
                                f"Autofix: Changed {surplus_color} to {deficit_color} at {face_name}[{r}][{c}]",
                            )
    return state, "Warning: Vision error too complex for Autofix. Please rescan."
