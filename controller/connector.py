"""
Contains classes for interfacing the EV3 robot and manipulating the cube via the motors.
"""

import math
import socket
import time
from typing import Literal

from controller import mappings
from logic import mappings as logic_mappings
from logic.cube import Algorithm, Cube


class Robot:
    def __init__(self, host="192.168.0.2", port=65432):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, retry: bool = True):
        print(f"Connecting to EV3 at {self.host}:{self.port}...", end="")
        while True:
            try:
                self.socket.connect((self.host, self.port))
            except ConnectionRefusedError:
                if retry:
                    print(".", end="")
                    time.sleep(3)
                    continue
                raise
            else:
                break
        print("\nConnected successfully!\n")

    def __enter__(self):
        self.socket.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.socket.__exit__(exc_type, exc_val, exc_tb)

    def execute(self, command: str) -> str:
        self.socket.sendall(command.encode("utf-8"))
        response = self.socket.recv(1024)
        return response.decode("utf-8")

    def apply_motor_algorithm(self, algorithm: Algorithm):
        commands = []
        merged_moves = algorithm.merge_repeated_moves()
        for move in merged_moves:
            parsed_move = (
                move.lower().replace("t", "a").replace("s", "a").replace("v", "b")
            )
            commands.append(f"m {parsed_move}")
        response = self.execute(";".join(commands))
        if "ERROR" in response:
            print(f"Error executing command: {response}")

    def scan_color(self, position: int | None = None) -> tuple[float, float, float]:
        command = "s rgb"
        if position is not None:
            angle = position  # TODO: Adjust
            command = f"t c 400 {angle};" + command
        response = self.execute(command)
        r, g, b = map(float, response.split(","))
        return r, g, b


class CubeManipulator:
    def __init__(self):
        self.face_locations = {
            "U": "U",
            "F": "F",
            "D": "D",
            "B": "B",
            "L": "L",
            "R": "R",
        }
        self._move_history = []

    def cube_to_motor_algorithm(self, algorithm: Algorithm) -> Algorithm:
        self._move_history = []
        for move in algorithm.moves:
            face = move[0]
            if face not in self.face_locations:
                raise ValueError(f"Invalid face '{face}' in algorithm.")
            target_face = self.face_locations[face]
            modifier = "" if "'" in move else "'"
            self.bring_face_down(target_face)
            self._move_history.append("S")
            self._move_history.append(f"V{modifier}")
            self._move_history.append("S'")
        return Algorithm(self._move_history).optimize()

    def _apply_motor_algorithm(self, algorithm: Algorithm):
        for move in algorithm.moves:
            self._move_history.append(move)
            if move == "T":
                self._tilt_cube()
            elif move in ("V", "V'"):
                self._rotate_cube("counterclockwise" if "'" in move else "clockwise")

    def bring_face_down(self, face: str):
        if face == "D":
            return
        moves = " S T A A' A' S' "
        if face == "U":
            moves *= 2
        elif face == "F":
            moves = "V2" + moves
        elif face == "R":
            moves = "V'" + moves
        elif face == "L":
            moves = "V" + moves
        self._apply_motor_algorithm(Algorithm(moves))

    def _tilt_cube(self):
        for face, current_pos in self.face_locations.items():
            self.face_locations[face] = mappings.TILT_MAP[current_pos]

    def _rotate_cube(self, direction: Literal["clockwise", "counterclockwise"]):
        for face, current_pos in self.face_locations.items():
            self.face_locations[face] = mappings.ROTATION_MAP[direction][current_pos]


class CubeScanner:
    def __init__(
        self,
        robot: Robot,
        cube_manipulator: CubeManipulator,
        calibration: dict[str, tuple[float, float, float]] | None = None,
    ):
        self.robot = robot
        self.cube_manipulator = cube_manipulator
        self.calibration = calibration

    def scan(self) -> Cube:
        cube_state = {}
        if not self.calibration:
            self.calibrate()
        for face in mappings.FACE_SCAN_ORDER:
            face_colors = [face]
            for i in range(8):
                if i % 2 == 0:
                    position = 2
                else:
                    position = 1
                r, g, b = self.scan_face_position(face, position)
                calibrated_color = self._get_closest_calibrated_color(r, g, b)
                face_colors.append(calibrated_color)
                self.robot.execute(f"a b 1000 {-135}")
            for faces, position_map in mappings.FACE_SCAN_POSITIONS.items():
                if face in faces:
                    for row in position_map:
                        for col, color_index in enumerate(row):
                            cube_state[face][row][col] = face_colors[color_index]
                    break
            else:
                raise ValueError(f"Face '{face}' not found in FACE_SCAN_POSITIONS.")
            self.robot.scan_color(0)
        return Cube(cube_state)

    def calibrate(self):
        faces = mappings.FACE_SCAN_ORDER
        self.calibration = {face: self.scan_face_position(face, 3) for face in faces}

    def scan_face_position(
        self, face: str, position: int
    ) -> tuple[float, float, float]:
        self.cube_manipulator.bring_face_down(logic_mappings.OPPOSITE_FACES[face])
        self.robot.apply_motor_algorithm(Algorithm(self.cube_manipulator._move_history))
        return self.robot.scan_color(position)

    def _get_closest_calibrated_color(self, r: float, g: float, b: float) -> str:
        if not self.calibration:
            raise ValueError("Calibration data is not available.")
        closest_color = None
        min_distance = float("inf")
        for name, (r2, g2, b2) in self.calibration.items():
            distance = math.sqrt((r - r2) ** 2 + (g - g2) ** 2 + (b - b2) ** 2)
            if distance < min_distance:
                min_distance = distance
                closest_color = name
        if closest_color is None:
            raise ValueError(
                "No closest color found. Calibration data may be incomplete."
            )
        return closest_color
