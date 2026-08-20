"""
Main entry point for the robot controller.
"""

import sys
import time

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
            if user_input.strip().startswith("scan"):
                if "cont" in user_input:
                    while True:
                        try:
                            print_color(robot.scan_color())
                            time.sleep(0.5)
                        except KeyboardInterrupt:
                            break
                    continue
                else:
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


def print_color(rgb: tuple[float, float, float], text: str = "████████"):
    r, g, b = map(lambda x: int((max(0, min(100, x)) / 100.0) * 255), rgb)
    color_code = f"\033[38;2;{r};{g};{b}m"
    reset_code = "\033[0m"
    print(f"{color_code}{text}{reset_code} RGB: ({r:^5.1f}, {g:^5.1f}, {b:^5.1f})")


if __name__ == "__main__":
    main()
