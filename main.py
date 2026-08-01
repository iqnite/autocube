import json
import random
import sys

from matplotlib import pyplot as plt

from logic.cube import Algorithm, Cube
from logic.solver import solve_cube
from tools.visualizer import visualize_cube

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)
            cube = Cube.from_json(json_data)
        except FileNotFoundError:
            print(f"ERROR: Couldn't find file {file_path}.")
            sys.exit(1)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"ERROR: {e}")
            sys.exit(1)
        print(f"Solving cube from {file_path}...")
    else:
        cube = Cube()
        shuffle_moves = " ".join(random.choices(["U", "D", "L", "R", "F", "B"], k=40))
        cube.apply_algorithm(Algorithm(shuffle_moves))
        print("No file provided, solving random cube...")
    # cube.on_move = lambda: visualize_cube(cube, live=True)
    cube.move_history.clear()
    solve_cube(cube)
    print("Cube solved!")
    history_algorithm = Algorithm(cube.move_history)
    print("Moves:", history_algorithm)
    print("Moves (optimized):", Algorithm.optimize_move_string(str(history_algorithm)))
    visualize_cube(cube)
    plt.show(block=True)
