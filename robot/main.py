#!/usr/bin/env pybricks-micropython
import sys

from pybricks.ev3devices import ColorSensor, Motor, TouchSensor  # type: ignore
from pybricks.hubs import EV3Brick  # type: ignore
from pybricks.media.ev3dev import ImageFile, SoundFile  # type: ignore
from pybricks.parameters import Button, Color, Direction, Port, Stop  # type: ignore
from pybricks.robotics import DriveBase  # type: ignore
from pybricks.tools import DataLog, StopWatch, wait  # type: ignore

sys.path.append("..")

import logic.mappings

ev3 = EV3Brick()

print(logic.mappings.UP_EDGES)

test_motor = Motor(Port.A)
test_button = TouchSensor(Port.S3)
test_light = ColorSensor(Port.S2)

if __name__ == "__main__":
    test_motor.reset_angle(0)

    test_motor.run_target(500, 90)

    while not test_button.pressed():
        print(test_light.color())
        wait(100)
