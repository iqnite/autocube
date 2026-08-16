#!/usr/bin/env pybricks-micropython

"""
Main entry point for the EV3 robot.
"""

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
        self.color_sensor = ColorSensor(Port.S2)
        self.motors = {
            "a": Motor(Port.A),
            "b": Motor(Port.B),
            "c": Motor(Port.C),
        }

    def reset_motor_positions(self):
        self.motors["a"].run_until_stalled(-100)
        self.motors["c"].run_until_stalled(500)

    def execute_command(self, commands):
        print(commands)
        output = []
        for command in commands.split(";"):
            try:
                if not command.strip():
                    continue
                cmd_type, *args = command.split()
                if cmd_type == "m":
                    motor_id = args[0][0]
                    is_prime = "'" in args[0]
                    modifier = -1 if is_prime else 1
                    speed = 1000
                    angle = 90 * modifier
                    if motor_id == "b":
                        angle *= 3
                    self.motors[motor_id].run_angle(int(speed), int(angle), wait=True)
                    continue
                if cmd_type == "a":
                    motor_id, speed, angle = args
                    self.motors[motor_id].run_angle(int(speed), int(angle), wait=True)
                    continue
                if cmd_type == "t":
                    motor_id, speed, angle = args
                    self.motors[motor_id].run_target(int(speed), int(angle), wait=True)
                    continue
                if cmd_type == "s":
                    sensor_id = args[0]
                    if sensor_id == "rgb":
                        output.append(str(self.color_sensor.rgb()))
                        continue
            except Exception as e:
                output.append("ERROR: " + str(e))
        return ";".join(output)


if __name__ == "__main__":
    robot = Robot()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # This setting prevents "Address already in use" errors if you restart the script quickly
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind((HOST, PORT))
        s.listen(1)

        print("Listening for connection on port", PORT)
        while True:
            conn, addr = s.accept()
            try:
                print("Connected by laptop at", addr)
                while True:
                    data = conn.recv(2048)
                    if not data:
                        break  # Laptop disconnected
                    command = data.decode("utf-8").strip()
                    response = robot.execute_command(command)
                    conn.send(response.encode("utf-8") if response else b"OK")
            finally:
                try:
                    conn.close()
                except OSError as e:
                    print("Error occurred while closing connection:", e)
    finally:
        try:
            s.close()
        except OSError as e:
            print("Error occurred while closing socket:", e)
