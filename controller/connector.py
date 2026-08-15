import socket

from logic.cube import Algorithm


class Robot:
    def __init__(self, host="192.168.0.2", port=65432):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        print(f"Connecting to EV3 at {self.host}:{self.port}...")
        self.socket.connect((self.host, self.port))
        print("Connected successfully!\n")

    def __enter__(self):
        self.socket.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.socket.__exit__(exc_type, exc_val, exc_tb)

    def execute(self, command: str) -> str:
        self.socket.sendall(command.encode("utf-8"))
        response = self.socket.recv(1024)
        return response.decode("utf-8")

    def apply_motor_algorithm(self, algorithm: Algorithm):
        for move in algorithm.moves:
            motor_id = move[0].lower()
            modifier = 1 if "'" not in move else -1
            speed = 1000 * modifier
            angle = 90 * modifier
            if motor_id == "b":
                angle *= 3
            command = f"m {motor_id} {speed} {angle}"
            response = self.execute(command)
            if response.startswith("ERROR"):
                print(f"Error executing command '{command}': {response}")
                break
