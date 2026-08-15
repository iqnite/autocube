import socket
import sys

PORT = 65432

if __name__ == "__main__":
    ev3_ip = sys.argv[1] if len(sys.argv) > 1 else "ev3dev.local"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print(f"Connecting to EV3 at {ev3_ip}:{PORT}...")
        s.connect((ev3_ip, PORT))
        print("Connected successfully!\n")
        while True:
            user_input = input("Enter command (or 'quit' to exit): ")
            if not user_input:
                continue
            if user_input == "quit":
                break
            s.sendall(user_input.encode("utf-8"))
            response = s.recv(1024)
            print(response.decode("utf-8").strip())
