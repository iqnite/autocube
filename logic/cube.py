"""
Contains representations of Cubes and Algorithms, with helper methods for manipulation.
"""

import json
import re
from enum import Enum

from logic.mappings import BANDS, CORNER_MAP, EDGE_MAP, TRANSLATION_MAPPING


class Face(Enum):
    D = "D"
    U = "U"
    F = "F"
    B = "B"
    R = "R"
    L = "L"


class Cube:
    def __init__(self, state=None, on_move=None):
        self.state: dict[str, list[list[str]]] = state or {
            face.value: [[face.value for _ in range(3)] for _ in range(3)]
            for face in Face
        }
        self.on_move = on_move
        self.move_history = []

    @classmethod
    def from_json(cls, json_data, on_move=None):
        cls.validate_json(json_data)
        return cls(state=json_data.get("faces"), on_move=on_move)

    @staticmethod
    def validate_json(json_data: dict):
        faces = json_data.get("faces")
        if faces is None:
            raise ValueError("No 'faces' attribute found.")
        if len(faces) != 6:
            raise ValueError(f"Expected 6 faces, found {len(faces)}.")
        for face, rows in faces.items():
            if len(rows) != 3:
                raise ValueError(
                    f"Expected 3 rows on each face, found {len(rows)} on '{face}' face."
                )
            for row in rows:
                if len(row) != 3:
                    raise ValueError(
                        f"Expected 3 facelet in each row, found {len(row)} on '{face}' face."
                    )
                for facelet in row:
                    if facelet not in Face:
                        raise ValueError(
                            "Colors must be one of the following: U, D, R, L, F, B."
                        )

    def to_json(self):
        return json.dumps(self.state, indent=2)

    def _rotate_matrix(self, face: str, clockwise: bool):
        grid = self.state[face]
        if clockwise:
            # Transpose and reverse rows
            self.state[face] = [list(row) for row in zip(*grid[::-1])]
        else:
            # Reverse rows and transpose
            self.state[face] = [list(row) for row in zip(*grid)][::-1]

    def _cycle_band(self, band: list[Facelet], clockwise: bool):
        values = [self.state[edge.face][edge.row][edge.col] for edge in band]
        if clockwise:
            values = values[-3:] + values[:-3]
        else:
            values = values[3:] + values[:3]
        for edge, val in zip(band, values):
            self.state[edge.face][edge.row][edge.col] = val

    def apply_move(self, move: str):
        self.move_history.append(move)
        clockwise = not move.endswith("'")
        face = move[0]
        self._rotate_matrix(face, clockwise)
        self._cycle_band(
            list(map(lambda args: Facelet(*args), BANDS[face])),
            clockwise,
        )

    def apply_algorithm(self, algorithm: "Algorithm", on_move=None):
        algorithm.apply(self, on_move=on_move or self.on_move)

    def get_edges_of_color(self, color: str = "D") -> list[Facelet]:
        edges = []
        valid_coords = [(0, 1), (1, 0), (1, 2), (2, 1)]
        for face in ["U", "D", "L", "R", "F", "B"]:
            for row, col in valid_coords:
                if self.state[face][row][col] == color:
                    edges.append(Facelet(face, row, col))
        return edges

    @staticmethod
    def get_face_adjacent_to_edge(edge: Facelet) -> str:
        return EDGE_MAP[edge.tuple][0]

    def get_color_adjacent_to_edge(self, edge: Facelet) -> str:
        adj_face, adj_row, adj_col = EDGE_MAP[edge.tuple]
        return self.state[adj_face][adj_row][adj_col]

    def edge_is_bleeding(self, edge: Facelet) -> bool:
        adj_color = self.get_color_adjacent_to_edge(edge)
        adj_face = self.get_face_adjacent_to_edge(edge)
        return adj_color == self.state[adj_face][1][1]

    def get_corners_of_color(self, color: str = "D") -> list[Facelet]:
        corners = []
        valid_coords = [(0, 0), (0, 2), (2, 0), (2, 2)]
        for face in ["U", "D", "L", "R", "F", "B"]:
            for row, col in valid_coords:
                if self.state[face][row][col] == color:
                    corners.append(Facelet(face, row, col))
        return corners

    @staticmethod
    def get_faces_adjacent_to_corner(corner: Facelet) -> tuple[str, str]:
        return CORNER_MAP[corner.tuple][0][0], CORNER_MAP[corner.tuple][1][0]

    def get_colors_adjacent_to_corner(self, corner: Facelet) -> tuple[str, str]:
        adj_coord_1, adj_coord_2 = CORNER_MAP[corner.tuple]
        color_1 = self.state[adj_coord_1[0]][adj_coord_1[1]][adj_coord_1[2]]
        color_2 = self.state[adj_coord_2[0]][adj_coord_2[1]][adj_coord_2[2]]
        return color_1, color_2


class Algorithm:
    def __init__(
        self, moves: str | list[str], translation_reference: str | None = None
    ):
        if isinstance(moves, str):
            self.moves = list(self.parse(moves))
        else:
            self.moves = moves
        if translation_reference:
            self.moves = [
                self.translate_move(move, translation_reference) for move in self.moves
            ]

    def __add__(self, other: Algorithm | str | list):
        if isinstance(other, Algorithm):
            return Algorithm(" ".join(self.moves + other.moves))
        elif isinstance(other, str):
            return Algorithm(" ".join(self.moves + list(self.parse(other))))
        elif isinstance(other, list):
            return Algorithm(" ".join(self.moves + other))
        else:
            raise TypeError(f"Unsupported type for addition: {type(other)}")

    def __mul__(self, other: int):
        return Algorithm(" ".join(self.moves * other))

    def __neg__(self):
        inverted_moves = [
            move[:-1] if move.endswith("'") else move + "'"
            for move in reversed(self.moves)
        ]
        return Algorithm(" ".join(inverted_moves))

    def __str__(self):
        return " ".join(self.moves)

    def apply(self, cube: Cube, on_move=None):
        for move in self.moves:
            cube.apply_move(move)
            on_move = on_move or cube.on_move
            if on_move is not None:
                on_move()

    @staticmethod
    def parse(text: str):
        repeat_pattern = re.compile(r"(\D+)(\d*)")
        for move in text.split():
            matched_move = repeat_pattern.match(move)
            if not matched_move:
                raise ValueError(f"Invalid move format: {move}")
            base_move, repeat_count = matched_move.groups()
            repeat_count = int(repeat_count) if repeat_count else 1
            for _ in range(repeat_count):
                yield base_move

    def translate(self, reference_front: str) -> "Algorithm":
        translated_moves = [
            self.translate_move(move, reference_front) for move in self.moves
        ]
        return Algorithm(" ".join(translated_moves))

    @staticmethod
    def translate_move(move: str, reference_front: str) -> str:
        if move[0] in "UD":
            return move
        return (
            TRANSLATION_MAPPING[reference_front][move[0]] + move[1:]
            if len(move) > 1
            else TRANSLATION_MAPPING[reference_front][move[0]]
        )

    def optimize(self) -> "Algorithm":
        return Algorithm(self.optimize_move_string(str(self)))

    @staticmethod
    def optimize_move_string(moves: str) -> str:
        moves = moves + " "
        for move in Algorithm.CubeRotation:
            move_str = move.value
            moves = (
                moves.replace(f"{move_str} " * 4, " ")
                .replace(f"{move_str} " * 3, f"{move_str}' ")
                .replace(f"{move} {move}' ", " ")
                .replace(f"{move}' {move} ", " ")
                .replace(f"{move_str} " * 2, f"{move_str}2 ")
                .replace("'2", "2")
                .replace("2'", "2")
                .replace("''", "")
                .replace("  ", " ")
                .replace("  ", " ")
            )
        return moves

    class CubeRotation(Enum):
        U = "U"
        U_PRIME = "U'"
        D = "D"
        D_PRIME = "D'"
        L = "L"
        L_PRIME = "L'"
        R = "R"
        R_PRIME = "R'"
        F = "F"
        F_PRIME = "F'"
        B = "B"
        B_PRIME = "B'"


class Facelet:
    def __init__(self, face: str, row: int, col: int):
        self.tuple = self.face, self.row, self.col = face, row, col
