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
MOTOR_POSITIONS_PATH = "motor_positions.txt"


class Robot:
    def __init__(self):
        self.ev3 = EV3Brick()
        self.color_sensor = ColorSensor(Port.S2)
        self.motors = {
            "a": Motor(Port.A),
            "b": Motor(Port.B),
            "c": Motor(Port.C),
        }
        motor_positions_file = None
        try:
            motor_positions_file = open(MOTOR_POSITIONS_PATH, "r")
        except:
            motor_positions_file = open(MOTOR_POSITIONS_PATH, "w")
        else:
            for line in motor_positions_file.readlines():
                motor_id, angle = line.strip().split(":")
                if not angle.isdigit():
                    continue
                self.motors[motor_id].reset_angle(int(angle))
        finally:
            if motor_positions_file is not None:
                motor_positions_file.close()
        self.reset_motor_positions()

    def save_motor_positions(self):
        motor_positions_file = None
        try:
            motor_positions_file = open(MOTOR_POSITIONS_PATH, "w")
            for motor_id, motor in self.motors.items():
                motor_positions_file.write(motor_id + ":" + str(motor.angle() % 360) + "\n")
        finally:
            if motor_positions_file is not None:
                motor_positions_file.flush()
                motor_positions_file.close()

    def reset_motor_positions(self):
        for motor in self.motors.values():
            motor.run_target(500, 0)

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
                    repetitions = 1
                    repetitions_str = args[0][-1]
                    if repetitions_str.isdigit():
                        repetitions = int(repetitions_str)
                    speed = 400
                    angle = 90 * modifier * repetitions
                    if motor_id == "b":
                        angle *= 3
                        speed = 1000
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
                        r, g, b = self.color_sensor.rgb()
                        output.append(str(r) + "," + str(g) + "," + str(b))
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
                    robot.save_motor_positions()
                    conn.send(response.encode("utf-8") if response else b"OK")
            except Exception as e:
                print("Error during communication:", e)
            finally:
                conn.close()
    except Exception as e:
        print("Error setting up server:", e)
    finally:
        robot.save_motor_positions()
        s.close()
