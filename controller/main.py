import socket
import sys

PORT = 65432

if __name__ == "__main__":
    ev3_ip = sys.argv[1] if len(sys.argv) > 1 else "ev3dev.local"
    calculated_moves = ["U", "R2", "F'", "D"]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print(f"Connecting to EV3 at {ev3_ip}:{PORT}...")
        s.connect((ev3_ip, PORT))
        print("Connected successfully!\n")
        for move in calculated_moves:
            print(f"Sending: {move}")
            s.sendall(move.encode("utf-8"))
            response = s.recv(1024)
            print(f"EV3 replies: {response.decode('utf-8').strip()}")
    print("\nAll moves completed successfully.")
