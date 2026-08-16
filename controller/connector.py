"""
Contains classes for interfacing the EV3 robot and manipulating the cube via the motors.
"""

import socket
import time
from typing import Literal

from controller import mappings
from logic.cube import Algorithm


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

    def apply_motor_algorithm(self, algorithm: Algorithm, on_move=None):
        for move in algorithm.moves:
            motor_id = move[0].lower()
            if motor_id in ("t", "s"):
                motor_id = "a"
            speed_modifier = 1 if "'" not in move else -1
            speed = 1000 * speed_modifier
            angle = 90
            if motor_id == "b":
                angle *= 3
            command = f"m {motor_id} {speed} {angle}"
            response = self.execute(command)
            if response.startswith("ERROR"):
                print(f"Error executing command '{command}': {response}")
                break
            if on_move is not None:
                on_move()


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
            modifier = "'" if "'" in move else ""
            self._bring_face_down(target_face)
            self._lock_cube()
            self.apply_motor_algorithm(Algorithm(f"B{modifier}"))
            self._unlock_cube()
        return Algorithm(self._move_history).optimize()

    def apply_motor_algorithm(self, algorithm: Algorithm):
        for move in algorithm.moves:
            self._move_history.append(move)
            if move == "T":
                self._tilt_cube()
            elif move in ("B", "B'"):
                self._rotate_cube("counterclockwise" if "'" in move else "clockwise")

    def _bring_face_down(self, face: str):
        if face == "D":
            return
        moves = " S T A A' A' S' "
        if face == "U":
            moves *= 2
        elif face == "F":
            moves = "B2" + moves
        elif face == "R":
            moves = "B" + moves
        elif face == "L":
            moves = "B'" + moves
        self.apply_motor_algorithm(Algorithm(moves))

    def _tilt_cube(self):
        for face, current_pos in self.face_locations.items():
            self.face_locations[face] = mappings.TILT_MAP[current_pos]

    def _rotate_cube(self, direction: Literal["clockwise", "counterclockwise"]):
        for face, current_pos in self.face_locations.items():
            self.face_locations[face] = mappings.ROTATION_MAP[direction][current_pos]

    def _lock_cube(self):
        self.apply_motor_algorithm(Algorithm("S"))

    def _unlock_cube(self):
        self.apply_motor_algorithm(Algorithm("S'"))
