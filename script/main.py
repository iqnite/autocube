"""
Entry point for the command line solver script.
"""

import json
import random
import sys
import time
from argparse import ArgumentParser

from matplotlib import pyplot as plt

from logic.cube import Algorithm, Cube
from logic.solver import solve_cube
from script.visualizer import visualize_cube


def main():
    parser = ArgumentParser(
        prog="Autocube",
        description="Solve a Rubik's cube from a JSON file.",
        epilog="If no file is supplied, a random cube will be solved."
        " If only moves are supplied, they will be performed on a solved cube.",
        add_help=True,
        allow_abbrev=True,
        suggest_on_error=True,
    )
    parser.add_argument(
        "-f",
        "--file",
        metavar="PATH",
        nargs="?",
        type=str,
        help="path to a JSON file containing a Rubik's cube state",
    )
    parser.add_argument(
        "-m",
        "--moves",
        dest="moves",
        metavar='"MOVE1 MOVE2 ..."',
        nargs="?",
        const="",
        type=str,
        required=False,
        help="perform custom moves on the cube and print the state afterwards",
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
        help="show the solution steps live (reduces performance)",
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
        help="only print the optimized moves (or state if used with --moves)",
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
            print(f"Using cube from {file_path}...")
    else:
        cube = Cube()
        if args.moves is None:
            shuffle_moves = " ".join(
                random.choices(["U", "D", "L", "R", "F", "B"], k=40)
            )
            cube.apply_algorithm(Algorithm(shuffle_moves))
        if args.moves is None and not args.quiet:
            print("No file provided, using random cube...")
    if args.live:
        cube.on_move = lambda: visualize_cube(cube, live=True)
    start_time = time.time()
    solution = ""
    if args.moves is None:
        solution = solve_cube(cube)
    elif args.moves != "":
        cube.apply_algorithm(Algorithm(args.moves))
    duration = time.time() - start_time
    if not args.quiet:
        print(f"Finished in {duration:.2f}s!")
    if args.moves is None:
        if len(solution) > 0:
            if not args.quiet:
                print("Moves: ", end="")
            print(solution)
    if args.moves is not None:
        if not args.quiet:
            print("Cube state:")
        print(cube.to_json())
    if not args.live and not args.quiet and args.moves is not None:
        visualize_cube(cube)
    if not args.quiet:
        plt.show(block=True)


if __name__ == "__main__":
    main()
