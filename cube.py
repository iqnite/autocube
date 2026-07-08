import json
import re
from enum import Enum


class Cube:
    def __init__(self, face_data=None):
        self.faces = (
            face_data.get("faces")
            if face_data
            else [[i for _ in range(9)] for i in [-3, -2, -1, 1, 2, 3]]
        )
        self.orientation = 0

    def to_json(self):
        return json.dumps({"faces": self.faces}, indent=2)

    def apply_move(self, move: str):
        if move == "U":
            self._rotate_face(3)
            self._cycle_edges([0, 1, 2], [0, 1, 2], [0, 1, 2], [0, 1, 2])
        elif move == "U'":
            self._rotate_face(3, clockwise=False)
            self._cycle_edges([0, 1, 2], [0, 1, 2], [0, 1, 2], [0, 1, 2], reverse=True)
        elif move == "D":
            self._rotate_face(4)
            self._cycle_edges([5, 4, 3], [5, 4, 3], [5, 4, 3], [5, 4, 3])
        elif move == "D'":
            self._rotate_face(4, clockwise=False)
            self._cycle_edges([5, 4, 3], [5, 4, 3], [5, 4, 3], [5, 4, 3], reverse=True)
        elif move == "L":
            self._rotate_face(0)
            self._cycle_edges([0, 3, 5], [0, 3, 5], [0, 3, 5], [0, 3, 5])
        elif move == "L'":
            self._rotate_face(0, clockwise=False)
            self._cycle_edges([0, 3, 5], [0, 3, 5], [0, 3, 5], [0, 3, 5], reverse=True)
        elif move == "R":
            self._rotate_face(1)
            self._cycle_edges([2, 4, 1], [2, 4, 1], [2, 4, 1], [2, 4, 1])
        elif move == "R'":
            self._rotate_face(1, clockwise=False)
            self._cycle_edges([2, 4, 1], [2, 4, 1], [2, 4, 1], [2, 4, 1], reverse=True)
        elif move == "F":
            self._rotate_face(2)
            self._cycle_edges([3, -1, 0], [3, -1, 0], [3, -1, 0], [3, -1, 0])
        elif move == "F'":
            self._rotate_face(2, clockwise=False)
            self._cycle_edges(
                [3, -1, 0], [3, -1, 0], [3, -1, 0], [3, -1, 0], reverse=True
            )
        elif move == "B":
            self._rotate_face(5)
            self._cycle_edges([1, -3, 2], [1, -3, 2], [1, -3, 2], [1, -3, 2])
        elif move == "B'":
            self._rotate_face(5, clockwise=False)
            self._cycle_edges(
                [1, -3, 2], [1, -3, 2], [1, -3, 2], [1, -3, 2], reverse=True
            )

    def _rotate_face(self, face_index: int, clockwise: bool = True):
        face = self.faces[face_index]
        if clockwise:
            self.faces[face_index] = [
                face[0],
                face[7],
                face[8],
                face[1],
                face[2],
                face[3],
                face[4],
                face[5],
                face[6],
            ]
        else:
            self.faces[face_index] = [
                face[0],
                face[3],
                face[4],
                face[5],
                face[6],
                face[7],
                face[8],
                face[1],
                face[2],
            ]

    def _cycle_edges(self, *edges, reverse=False):
        if reverse:
            edges = edges[::-1]
        temp = [self.faces[edge[0]][edge[1]] for edge in edges]
        for i in range(len(edges)):
            self.faces[edges[i][0]][edges[i][1]] = temp[i - 1]


class Algorithm:
    def __init__(self, moves: str):
        self.moves = list(self.parse(moves))

    def apply(self, cube: Cube):
        for move in self.moves:
            cube.apply_move(move)

    @staticmethod
    def parse(moves: str):
        repeat_pattern = re.compile(r"(\w+)(\d*)")
        for move in moves.split():
            matched_move = repeat_pattern.match(move)
            if matched_move:
                base_move, repeat_count = matched_move.groups()
                repeat_count = int(repeat_count) if repeat_count else 1
                for _ in range(repeat_count):
                    yield base_move
            raise ValueError(f"Invalid move format: {move}")

    class AvailableMoves(Enum):
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
