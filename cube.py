import json
import re
from enum import Enum


class Cube:
    def __init__(self, face_data=None):
        self.pieces: list[Piece] = []
        for i, face in (
            enumerate(face_data)
            if face_data
            else enumerate(
                [
                    [[Piece.Color.WHITE] * 3] * 3,
                    [[Piece.Color.YELLOW] * 3] * 3,
                    [[Piece.Color.RED] * 3] * 3,
                    [[Piece.Color.ORANGE] * 3] * 3,
                    [[Piece.Color.GREEN] * 3] * 3,
                    [[Piece.Color.BLUE] * 3] * 3,
                ]
            )
        ):
            for j, row in enumerate(face):
                for k, color in enumerate(row):
                    center_color = face[1][1]
                    try:
                        piece = self.get_piece(i, j, k)
                        piece.colors[center_color] = color
                    except IndexError:
                        self.pieces.append(Piece({center_color: color}))

    def to_json(self):
        return json.dumps(
            {
                "faces": [
                    [
                        [
                            piece.get_color_on_face(face_color).value
                            for piece in self.get_pieces_on_face(face_color)
                        ]
                        for face_color in Piece.Color
                    ]
                ]
            },
            indent=2,
        )

    def apply_algorithm(self, algorithm: Algorithm):
        algorithm.apply(self)

    def apply_move(self, move: Algorithm.CubeRotation):
        if move == Algorithm.CubeRotation.U:
            self.rotate_face(0, clockwise=True)
        elif move == Algorithm.CubeRotation.U_PRIME:
            self.rotate_face(0, clockwise=False)
        elif move == Algorithm.CubeRotation.D:
            self.rotate_face(1, clockwise=True)
        elif move == Algorithm.CubeRotation.D_PRIME:
            self.rotate_face(1, clockwise=False)
        elif move == Algorithm.CubeRotation.L:
            self.rotate_face(2, clockwise=True)
        elif move == Algorithm.CubeRotation.L_PRIME:
            self.rotate_face(2, clockwise=False)
        elif move == Algorithm.CubeRotation.R:
            self.rotate_face(3, clockwise=True)
        elif move == Algorithm.CubeRotation.R_PRIME:
            self.rotate_face(3, clockwise=False)
        elif move == Algorithm.CubeRotation.F:
            self.rotate_face(4, clockwise=True)
        elif move == Algorithm.CubeRotation.F_PRIME:
            self.rotate_face(4, clockwise=False)
        elif move == Algorithm.CubeRotation.B:
            self.rotate_face(5, clockwise=True)
        elif move == Algorithm.CubeRotation.B_PRIME:
            self.rotate_face(5, clockwise=False)
        else:
            raise ValueError(f"Invalid move: {move}")

    def rotate_face(self, face_index: int, clockwise: bool = True):
        if face_index < 0 or face_index >= 6:
            raise ValueError("Invalid face index.")
        face_pieces = self.pieces[face_index * 9 : (face_index + 1) * 9]
        if clockwise:
            new_positions = [
                (0, 2),
                (1, 2),
                (2, 2),
                (2, 1),
                (2, 0),
                (1, 0),
                (0, 0),
                (0, 1),
                (1, 1),
            ]
        else:
            new_positions = [
                (2, 0),
                (2, 1),
                (2, 2),
                (1, 2),
                (0, 2),
                (0, 1),
                (0, 0),
                (1, 0),
                (1, 1),
            ]
        for piece, new_pos in zip(face_pieces, new_positions):
            row, col = new_pos
            self.pieces[face_index * 9 + row * 3 + col] = piece

    def get_piece(self, face: int, row: int, col: int) -> "Piece":
        if face < 0 or face >= 6:
            raise IndexError("Invalid face index.")
        if row < 0 or row >= 3:
            raise IndexError("Invalid row index.")
        if col < 0 or col >= 3:
            raise IndexError("Invalid column index.")
        piece_index = face * 9 + row * 3 + col
        return self.pieces[piece_index]

    def get_pieces_on_face(self, face_color: Piece.Color) -> list["Piece"]:
        return [piece for piece in self.pieces if piece.is_on_face(face_color)]


class Piece:
    def __init__(self, colors: dict[Piece.Color, Piece.Color]):
        self.colors: dict[Piece.Color, Piece.Color] = {
            Piece.Color(k): Piece.Color(v) for k, v in colors.items()
        }

    def get_color_on_face(self, face_color: Piece.Color) -> Piece.Color:
        return self.colors[face_color]

    def is_on_face(self, face_color: Piece.Color) -> bool:
        return face_color in self.colors

    class PieceType(Enum):
        CORNER = "corner"
        EDGE = "edge"
        CENTER = "center"

    class Color(Enum):
        WHITE = "W"
        YELLOW = "Y"
        RED = "R"
        ORANGE = "O"
        GREEN = "G"
        BLUE = "B"

    @property
    def piece_type(self) -> PieceType:
        if len(self.colors) == 3:
            return self.PieceType.CORNER
        if len(self.colors) == 2:
            return self.PieceType.EDGE
        if len(self.colors) == 1:
            return self.PieceType.CENTER
        raise ValueError("Invalid number of colors for a piece.")


class Algorithm:
    def __init__(self, moves: str):
        self.moves = list(self.parse(moves))

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
                yield Algorithm.CubeRotation(base_move)

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


if __name__ == "__main__":
    with open("examples/solved.json", "r", encoding="utf-8") as f:
        face_data = json.load(f)["faces"]
    cube = Cube(face_data)
    cube.apply_algorithm(Algorithm("U R U' L D2 F'"))
    print(cube.to_json())
