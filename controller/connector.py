"""
Contains classes for interfacing the EV3 robot and manipulating the cube via the motors.
"""

import socket
from typing import Literal

from controller.mappings import FACE_RELOCATION_MOVES
from logic.cube import Algorithm, Cube


class Robot:
    def __init__(self, host="192.168.0.2", port=65432):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        print(f"Connecting to EV3 at {self.host}:{self.port}...")
        self.socket.connect((self.host, self.port))
        print("Connected successfully!\n")

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
        self.apply_motor_algorithm(Algorithm(FACE_RELOCATION_MOVES[face]))
        if face in ("D", "B"):
            return
        return self._bring_face_down("B")

    def _tilt_cube(self):
        self.face_locations.update(
            {
                "U": self.face_locations["B"],
                "F": self.face_locations["U"],
                "D": self.face_locations["F"],
                "B": self.face_locations["D"],
            }
        )

    def _rotate_cube(self, direction: Literal["clockwise", "counterclockwise"]):
        if direction == "clockwise":
            self.face_locations.update(
                {
                    "F": self.face_locations["R"],
                    "R": self.face_locations["B"],
                    "B": self.face_locations["L"],
                    "L": self.face_locations["F"],
                }
            )
        elif direction == "counterclockwise":
            self.face_locations.update(
                {
                    "F": self.face_locations["L"],
                    "L": self.face_locations["B"],
                    "B": self.face_locations["R"],
                    "R": self.face_locations["F"],
                }
            )

    def _lock_cube(self):
        self.apply_motor_algorithm(Algorithm("S"))

    def _unlock_cube(self):
        self.apply_motor_algorithm(Algorithm("S'"))
