"""
Main entry point for the robot controller.
"""

import sys

from controller.connector import CubeManipulator, Robot
from logic.cube import Algorithm

PORT = 65432

if __name__ == "__main__":
    ev3_ip = sys.argv[1] if len(sys.argv) > 1 else "ev3dev.local"
    with Robot(ev3_ip, PORT) as robot:
        robot.connect()
        while True:
            user_input = input("Enter algorithm (or 'q' to exit): ")
            if not user_input:
                continue
            if user_input == "q":
                break
            response = robot.apply_motor_algorithm(
                CubeManipulator().cube_to_motor_algorithm(Algorithm(user_input))
            )
