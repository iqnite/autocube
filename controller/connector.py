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
        self._command_queue = []

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
        self.queue(command)
        self.socket.sendall(";".join(self._command_queue).encode("utf-8"))
        self._command_queue.clear()
        response = self.socket.recv(1024)
        return response.decode("utf-8")

    def queue(self, command: str):
        self._command_queue.append(command)

    def apply_manipulations(self, manipulator: "CubeManipulator"):
        if manipulator._moves_to_apply:
            algorithm = Algorithm(" ".join(manipulator._moves_to_apply))
            self.apply_motor_algorithm(algorithm)
            manipulator._moves_to_apply.clear()

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

    def scan_color(
        self, position: int | None = None, reset_position: bool = False
    ) -> tuple[float, float, float]:
        command = "s rgb"
        if position is not None:
            if position == 0:
                angle = 0
            elif position == 1:
                angle = -140
            elif position == 2:
                angle = -180
            elif position == 3:
                angle = -360
            else:
                angle = position * -90
            command = f"t c 1000 {angle};" + command
        if reset_position:
            command += ";t c 1000 0"
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
        self._moves_to_apply = []

    def cube_to_motor_algorithm(self, algorithm: Algorithm) -> Algorithm:
        for move in algorithm.moves:
            face = move[0]
            if face not in self.face_locations:
                raise ValueError(f"Invalid face '{face}' in algorithm.")
            modifier = "" if "'" in move else "'"
            self.bring_face_down(face, is_logical=True)
            self._moves_to_apply.append("S")
            self._moves_to_apply.append(f"V{modifier}")
            self._moves_to_apply.append("S'")
        return Algorithm(self._moves_to_apply).optimize()

    def _stage_motor_algorithm(self, algorithm: Algorithm):
        for move in algorithm.moves:
            self._moves_to_apply.append(move)
            if move == "T":
                self._tilt_cube()
            elif move in ("V", "V'"):
                self._rotate_cube("counterclockwise" if "'" in move else "clockwise")

    def bring_face_down(self, face: str, is_logical: bool = True):
        if is_logical:
            face = self.face_locations[face]
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
        self._stage_motor_algorithm(Algorithm(moves))

    def bring_face_front(self, face: str, is_logical: bool = True):
        if is_logical:
            face = self.face_locations[face]
        if face == "F":
            return
        if face == "D":
            moves = "S T A A' A' S'"
        elif face == "U":
            moves = "S T A A' A' S' V2"
        elif face == "B":
            moves = "V2"
        elif face == "R":
            moves = "V"
        else:  # face == "L"
            moves = "V'"
        self._stage_motor_algorithm(Algorithm(moves))

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
        cube = Cube()
        if not self.calibration:
            self.calibrate()
        self.cube_manipulator.bring_face_down("D", is_logical=True)
        self.cube_manipulator.bring_face_front("F", is_logical=True)
        self.robot.apply_manipulations(self.cube_manipulator)
        for face in mappings.FACE_SCAN_ORDER:
            face_colors = [face]
            for i in range(8):
                if i % 2 == 0:
                    position = 2
                else:
                    position = 1
                r, g, b = self.scan_face_position(
                    face, position, reset_position=(i == 7)
                )
                calibrated_color = self._get_closest_calibrated_color(r, g, b)
                face_colors.append(calibrated_color)
                self.robot.queue("a b 1000 -135")
            for faces, position_map in mappings.FACE_SCAN_POSITIONS.items():
                if face in faces:
                    for row, row_data in enumerate(position_map):
                        for col, color_index in enumerate(row_data):
                            cube.state[face][row][col] = face_colors[color_index]
                    break
            else:
                raise ValueError(f"Face '{face}' not found in FACE_SCAN_POSITIONS.")
            self.robot.scan_color(0)
        self.cube_manipulator.bring_face_down("D", is_logical=True)
        self.cube_manipulator.bring_face_front("F", is_logical=True)
        self.robot.apply_manipulations(self.cube_manipulator)
        return cube

    def calibrate(self):
        faces = mappings.FACE_SCAN_ORDER
        self.calibration = {
            face: self.scan_face_position(face, 3, reset_position=True)
            for face in faces
        }
        self.cube_manipulator.bring_face_down("D", is_logical=True)
        self.cube_manipulator.bring_face_front("F", is_logical=True)
        self.robot.apply_manipulations(self.cube_manipulator)

    def scan_face_position(
        self, face: str, position: int, reset_position: bool = False
    ) -> tuple[float, float, float]:
        self.cube_manipulator.bring_face_down(
            logic_mappings.OPPOSITE_FACES[face], is_logical=True
        )
        self.robot.apply_manipulations(self.cube_manipulator)
        return self.robot.scan_color(position, reset_position=reset_position)

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
