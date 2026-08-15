#!/usr/bin/env pybricks-micropython

import socket

from pybricks.ev3devices import ColorSensor, Motor, TouchSensor  # type: ignore
from pybricks.hubs import EV3Brick  # type: ignore
from pybricks.media.ev3dev import ImageFile, SoundFile  # type: ignore
from pybricks.parameters import Button, Color, Direction, Port, Stop  # type: ignore
from pybricks.robotics import DriveBase  # type: ignore
from pybricks.tools import DataLog, StopWatch, wait  # type: ignore

HOST = "0.0.0.0"
PORT = 65432


class Robot:
    def __init__(self):
        self.ev3 = EV3Brick()
        self.motor_yaw = Motor(Port.A)
        self.motor_roll = Motor(Port.B)
        self.motor_scanner = Motor(Port.C)

    def reset_motor_positions(self):
        self.motor_yaw.run_until_stalled(-100)
        self.motor_scanner.run_until_stalled(500)

    def execute_move(self, move):
        print("Received command for motors:", move)


if __name__ == "__main__":
    robot = Robot()
    robot.reset_motor_positions()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # This setting prevents "Address already in use" errors if you restart the script quickly
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind((HOST, PORT))
        s.listen(1)

        print("Listening for connection on port", PORT)
        conn, addr = s.accept()
        try:
            print("Connected by laptop at", addr)
            while True:
                data = conn.recv(1024)
                if not data:
                    break  # Laptop disconnected
                command = data.decode("utf-8").strip()
                robot.execute_move(command)
                wait(1000)
                conn.send(b"DONE\n")
        finally:
            conn.close()
    finally:
        s.close()
