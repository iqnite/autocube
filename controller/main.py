"""
Main entry point for the robot controller.
"""

import sys

from controller.connector import CubeManipulator, Robot
from logic.cube import Algorithm

PORT = 65432


def main():
    ev3_ip = sys.argv[1] if len(sys.argv) > 1 else "ev3dev.local"
    manipulator = CubeManipulator()
    with Robot(ev3_ip, PORT) as robot:
        robot.connect()
        while True:
            user_input = input("Enter algorithm (or 'quit' or 'reset'): ")
            if not user_input:
                continue
            if user_input == "quit":
                break
            if user_input == "reset":
                manipulator = CubeManipulator()
                continue
            robot.apply_motor_algorithm(
                manipulator.cube_to_motor_algorithm(Algorithm(user_input))
            )


if __name__ == "__main__":
    main()
