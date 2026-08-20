"""
Contains various mappings used for cube and motor translation.
"""

ROTATION_MAP = {
    "clockwise": {
        "F": "L",
        "L": "B",
        "B": "R",
        "R": "F",
        "U": "U",
        "D": "D",
    },
    "counterclockwise": {
        "F": "R",
        "R": "B",
        "B": "L",
        "L": "F",
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

FACE_SCAN_ORDER = "U", "F", "D", "R", "B", "L"
FACE_SCAN_POSITIONS = {
    "UFD": [
        [4, 5, 6],
        [3, 0, 7],
        [2, 1, 8],
    ],
    "R": [
        [8, 1, 2],
        [7, 0, 3],
        [6, 5, 4],
    ],
    "BL": [
        [6, 7, 8],
        [5, 0, 1],
        [4, 3, 2],
    ],
}

FACE_BGRS = {
    "U": (255, 255, 255),
    "F": (0, 255, 0),
    "D": (0, 255, 255),
    "B": (255, 0, 0),
    "L": (0, 0, 255),
    "R": (0, 165, 255),
}
