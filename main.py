import json
import random
import sys
import time
from argparse import ArgumentParser

from matplotlib import pyplot as plt

from logic.cube import Algorithm, Cube
from logic.solver import solve_cube
from tools.visualizer import visualize_cube

if __name__ == "__main__":
    parser = ArgumentParser(
        prog="Autocube",
        description="Solve a Rubik's cube from a JSON file.",
        add_help=True,
        allow_abbrev=True,
        suggest_on_error=True,
    )
    parser.add_argument(
        "file",
        metavar="PATH",
        nargs="?",
        type=str,
        help="A JSON file containing a Rubik's cube state."
        " If omitted, a random cube will be solved instead.",
    )
    parser.add_argument(
        "-l",
        "--live",
        dest="live",
        metavar="",
        nargs="?",
        type=bool,
        default=False,
        const=True,
        help="Show the solution steps live. Will drastically reduce performance.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        dest="quiet",
        metavar="",
        nargs="?",
        type=bool,
        default=False,
        const=True,
        help="Only print the optimized moves.",
    )
    args = parser.parse_args()
    if args.file is not None:
        file_path = args.file
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
        if not args.quiet:
            print(f"Solving cube from {file_path}...")
    else:
        cube = Cube()
        shuffle_moves = " ".join(random.choices(["U", "D", "L", "R", "F", "B"], k=40))
        cube.apply_algorithm(Algorithm(shuffle_moves))
        if not args.quiet:
            print("No file provided, solving random cube...")
    if args.live:
        cube.on_move = lambda: visualize_cube(cube, live=True)
    cube.move_history.clear()
    start_time = time.time()
    solve_cube(cube)
    duration = time.time() - start_time
    if not args.quiet:
        print(f"Cube solved in {duration:.2f}s!")
    history_algorithm = Algorithm(cube.move_history)
    if not args.quiet:
        print("Moves:", history_algorithm)
    if not args.quiet:
        print("Moves (optimized): ", end="")
    print(Algorithm.optimize_move_string(str(history_algorithm)))
    if not args.live and not args.quiet:
        visualize_cube(cube)
    plt.show(block=True)
