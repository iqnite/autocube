import json

from logic.cube import Algorithm, Cube
from tools.visualizer import visualize_cube

if __name__ == "__main__":
    with open("examples/solved.json", "r", encoding="utf-8") as f:
        face_data = json.load(f)["faces"]
    cube = Cube.from_json(face_data)
    cube.apply_algorithm(Algorithm("R"))
    print(cube.to_json())
    visualize_cube(cube)
