"""
Main entry point for the robot controller.
"""

import sys

from controller.connector import CubeManipulator, CubeScanner, Robot
from logic import solver
from logic.cube import Algorithm
from script.visualizer import visualize_cube

PORT = 65432


def main():
    ev3_ip = sys.argv[1] if len(sys.argv) > 1 else "ev3dev.local"
    manipulator = CubeManipulator()
    with Robot(ev3_ip, PORT) as robot:
        robot.connect()
        while True:
            user_input = input("Enter algorithm or command: ")
            if not user_input:
                continue
            if user_input == "quit":
                break
            if user_input == "reset":
                manipulator = CubeManipulator()
                continue
            if user_input == "solve":
                print("Scanning cube...")
                cube = CubeScanner(robot, manipulator).scan()
                print("Finding solution...")
                solution = solver.solve_cube(cube)
                print("Solving cube...")
                robot.apply_motor_algorithm(
                    manipulator.cube_to_motor_algorithm(Algorithm(solution))
                )
                print("Cube solved!")
                continue
            if user_input == "scan":
                scanner = CubeScanner(robot, manipulator)
                cube = scanner.scan()
                visualize_cube(cube)
                continue
            if user_input.startswith("cmd"):
                command = user_input[4:]
                print(robot.execute(command))
                continue
            robot.apply_motor_algorithm(
                manipulator.cube_to_motor_algorithm(Algorithm(user_input))
            )


if __name__ == "__main__":
    main()
