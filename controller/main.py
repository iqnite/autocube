import sys

from controller.connector import Robot

PORT = 65432

if __name__ == "__main__":
    ev3_ip = sys.argv[1] if len(sys.argv) > 1 else "ev3dev.local"
    with Robot(ev3_ip, PORT) as robot:
        robot.connect()
        while True:
            user_input = input("Enter command (or 'q' to exit): ")
            if not user_input:
                continue
            if user_input == "q":
                break
            response = robot.execute(user_input)
            print(response.strip())
