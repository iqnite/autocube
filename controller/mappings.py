"""
Contains various mappings used for cube and motor translation.
"""

ROTATION_MAP = {
    "clockwise": {
        "F": "R",
        "R": "B",
        "B": "L",
        "L": "F",
        "U": "U",
        "D": "D",
    },
    "counterclockwise": {
        "F": "L",
        "L": "B",
        "B": "R",
        "R": "F",
        "U": "U",
        "D": "D",
    },
}

TILT_MAP = {
    "U": "B",
    "B": "D",
    "D": "F",
    "F": "U",
    "L": "L",
    "R": "R",
}
