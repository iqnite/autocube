import json
import re
from enum import Enum

from logic.constants import CORNER_MAP, EDGE_MAP


class Face(Enum):
    D = "D"
    U = "U"
    F = "F"
    B = "B"
    R = "R"
    L = "L"


class Cube:
    def __init__(self, state=None):
        self.state = state or {
            face.value: [[face.value for _ in range(3)] for _ in range(3)]
            for face in Face
        }

    @classmethod
    def from_json(cls, json_data):
        return cls(state=json_data.get("faces"))

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

    def _cycle_band(self, band: list[tuple[str, int, int]], clockwise: bool):
        values = [self.state[f][r][c] for f, r, c in band]
        if clockwise:
            values = values[-3:] + values[:-3]
        else:
            values = values[3:] + values[:3]
        for (f, r, c), val in zip(band, values):
            self.state[f][r][c] = val

    def apply_move(self, move: str):
        clockwise = not move.endswith("'")
        face = move[0]
        self._rotate_matrix(face, clockwise)
        if face == "U":
            band = [
                ("B", 0, 2),
                ("B", 0, 1),
                ("B", 0, 0),
                ("R", 0, 2),
                ("R", 0, 1),
                ("R", 0, 0),
                ("F", 0, 2),
                ("F", 0, 1),
                ("F", 0, 0),
                ("L", 0, 2),
                ("L", 0, 1),
                ("L", 0, 0),
            ]
            self._cycle_band(band, clockwise)
        elif face == "D":
            band = [
                ("F", 2, 0),
                ("F", 2, 1),
                ("F", 2, 2),
                ("R", 2, 0),
                ("R", 2, 1),
                ("R", 2, 2),
                ("B", 2, 0),
                ("B", 2, 1),
                ("B", 2, 2),
                ("L", 2, 0),
                ("L", 2, 1),
                ("L", 2, 2),
            ]
            self._cycle_band(band, clockwise)
        elif face == "F":
            band = [
                ("U", 2, 0),
                ("U", 2, 1),
                ("U", 2, 2),
                ("R", 0, 0),
                ("R", 1, 0),
                ("R", 2, 0),
                ("D", 0, 2),
                ("D", 0, 1),
                ("D", 0, 0),
                ("L", 2, 2),
                ("L", 1, 2),
                ("L", 0, 2),
            ]
            self._cycle_band(band, clockwise)
        elif face == "B":
            band = [
                ("U", 0, 2),
                ("U", 0, 1),
                ("U", 0, 0),
                ("L", 0, 0),
                ("L", 1, 0),
                ("L", 2, 0),
                ("D", 2, 0),
                ("D", 2, 1),
                ("D", 2, 2),
                ("R", 2, 2),
                ("R", 1, 2),
                ("R", 0, 2),
            ]
            self._cycle_band(band, clockwise)
        elif face == "R":
            band = [
                ("U", 2, 2),
                ("U", 1, 2),
                ("U", 0, 2),
                ("B", 0, 0),
                ("B", 1, 0),
                ("B", 2, 0),
                ("D", 2, 2),
                ("D", 1, 2),
                ("D", 0, 2),
                ("F", 2, 2),
                ("F", 1, 2),
                ("F", 0, 2),
            ]
            self._cycle_band(band, clockwise)
        elif face == "L":
            band = [
                ("U", 0, 0),
                ("U", 1, 0),
                ("U", 2, 0),
                ("F", 0, 0),
                ("F", 1, 0),
                ("F", 2, 0),
                ("D", 0, 0),
                ("D", 1, 0),
                ("D", 2, 0),
                ("B", 2, 2),
                ("B", 1, 2),
                ("B", 0, 2),
            ]
            self._cycle_band(band, clockwise)
        else:
            raise NotImplementedError(f"Move {move} is not fully mapped yet.")

    def apply_algorithm(self, algorithm: "Algorithm"):
        algorithm.apply(self)

    def find_edges_of_color(self, color: str = "D") -> list[tuple[str, int, int]]:
        edges = []
        valid_coords = [(0, 1), (1, 0), (1, 2), (2, 1)]
        for face in ["U", "D", "L", "R", "F", "B"]:
            for row, col in valid_coords:
                if self.state[face][row][col] == color:
                    edges.append((face, row, col))
        return edges

    @staticmethod
    def get_face_adjacent_to_edge(edge: tuple[str, int, int]) -> str:
        return EDGE_MAP[edge][0]

    def get_color_adjacent_to_edge(self, edge: tuple[str, int, int]) -> str:
        adj_face, adj_row, adj_col = EDGE_MAP[edge]
        return self.state[adj_face][adj_row][adj_col]

    def edge_is_bleeding(self, edge: tuple[str, int, int]) -> bool:
        adj_color = self.get_color_adjacent_to_edge(edge)
        adj_face = self.get_face_adjacent_to_edge(edge)
        return adj_color == self.state[adj_face][1][1]

    def find_corners_of_color(self, color: str = "D") -> list[tuple[str, int, int]]:
        corners = []
        valid_coords = [(0, 0), (0, 2), (2, 0), (2, 2)]
        for face in ["U", "D", "L", "R", "F", "B"]:
            for row, col in valid_coords:
                if self.state[face][row][col] == color:
                    corners.append((face, row, col))
        return corners

    @staticmethod
    def get_faces_adjacent_to_corner(corner: tuple[str, int, int]) -> tuple[str, str]:
        return CORNER_MAP[corner][0][0], CORNER_MAP[corner][1][0]

    def get_colors_adjacent_to_corner(
        self, corner: tuple[str, int, int]
    ) -> tuple[str, str]:
        adj_coord_1, adj_coord_2 = CORNER_MAP[corner]
        color_1 = self.state[adj_coord_1[0]][adj_coord_1[1]][adj_coord_1[2]]
        color_2 = self.state[adj_coord_2[0]][adj_coord_2[1]][adj_coord_2[2]]
        return color_1, color_2


class Algorithm:
    def __init__(self, moves: str, translation_reference: str | None = None):
        self.moves = list(self.parse(moves))
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

    def apply(self, cube: Cube):
        for move in self.moves:
            cube.apply_move(move)

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
        face_mapping = {
            "F": {"F": "F", "B": "B", "L": "L", "R": "R"},
            "B": {"F": "B", "B": "F", "L": "R", "R": "L"},
            "L": {"F": "L", "B": "R", "L": "B", "R": "F"},
            "R": {"F": "R", "B": "L", "L": "F", "R": "B"},
        }
        return (
            face_mapping[reference_front][move[0]] + move[1:]
            if len(move) > 1
            else face_mapping[reference_front][move[0]]
        )

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
