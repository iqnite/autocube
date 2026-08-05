# Autocube

Autocube is a work-in-progress 3x3x3 Rubik's cube solver. Right now, it takes a file path from the command line and outputs the solution moves. Code for auto-solving with LEGO Mindstorms EV3 robots will be added soon.

## Script

[Demo video](https://youtu.be/HdCdrFA-3j8)

### Installation

To use the script, download it from the [Releases](https://github.com/iqnite/autocube/releases/latest/) page...

...or clone it from the repository (requires Python and Git):

```bash
git clone https://github.com/iqnite/autocube
cd autocube
pip install -r requirements.txt
```

### Usage

The autocube script can be used to solve and manipulate Rubik's cubes, represented as JSON files. Run `autocube -h` in the terminal to get an overview of the available options. Run `autocube --live` for a demo.

#### Solving cubes

A Rubik's cube is represented by a JSON file. The `faces` attribute contains the cube's state, consisting of a 3x3 array for each of the 6 faces. An example with a fully solved cube can be found at [examples/solved.json](examples/solved.json).

To solve a cube, pass the path to its JSON file to the `--file` (or `-f`) option of the script:

```bash
autocube --file examples/unsolved.json
```

This will print the solution steps to the terminal, along with other useful info. If only the solution steps are needed, the `--quiet` option can be used. This is especially useful if the solution algorithm needs to be piped into another program.

#### Performing algorithms

Colors and rotations are mapped to the letters used in standard notation:

- `U`: Yellow
- `D`: White
- `F`: Green
- `B`: Blue
- `L`: Left
- `R`: Right

In algorithms, each rotation is separated by a space. Prime (counterclockwise) rotations are followed by an apostrophe (`'`), double rotations by a `2`.

To apply an algorithm to a cube, use the `--moves` option. Make sure the algorithm is put in double quotes (`"`):

```bash
autocube --moves "U R U' R'"
```

This can also be used in combination with the `--file` option to perform moves starting from a custom cube state:

```bash
autocube --moves "U R U' R'" --file examples/unsolved.json
```

By default, the `--moves` prints the same output as the one printed with the `--file` option, plus the final cube state in JSON format. If the `--quiet` option is passed too, only the state will be printed.

If `--moves` is used without arguments, the cube will be visualized in its original state.

#### Live mode

The `--live` option shows every move in real time on a flattened representation of the cube. If used with the `--quiet` option, the window will be closed as soon as the algorithms finishes, otherwise it will stay open and block the script until it is closed manually.

Note that the live view will drastically increase solution times, since performance is limited by the screen's framerate.

## Hardware

Coming soon!

## Credits

Huge thanks to the maintainer(s) of the [Solve the Cube](https://solvethecube.com/) website for the solution algorithms and tutorials.

LLMs were used for help with structuring the representation of the cube, as well as with mappings. Solutions and docs were entirely written by hand.
