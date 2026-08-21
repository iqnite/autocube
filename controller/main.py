import random
import sys

import cv2
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from controller import mappings
from controller.connector import CubeManipulator, CubeScanner, Robot
from logic.autofix import autofix_cube_state
from logic.cube import Algorithm, Cube
from logic.solver import solve_cube

EV3_ADDRESS = "ev3dev.local"
PORT = 65432


class CameraThread(QThread):
    frame_ready = Signal(QImage, object)

    def __init__(self):
        super().__init__()
        self._is_running = True
        self.grid_size = 100
        self.rectangle_color = None
        self.adjacent_colors = None

    def run(self):
        cap = cv2.VideoCapture(0)
        while self._is_running:
            ret, frame = cap.read()
            if ret:
                h, w = frame.shape[:2]
                cx, cy = w // 2, h // 2
                if self.rectangle_color is not None:
                    for row in [-1, 0, 1]:
                        for col in [-1, 0, 1]:
                            x = cx + (col * self.grid_size)
                            y = cy + (row * self.grid_size)
                            cv2.rectangle(
                                frame,
                                (x - 5, y - 5),
                                (x + 5, y + 5),
                                self.rectangle_color,
                                2,
                            )
                if self.adjacent_colors is not None:
                    for idx, (row, col, xd, yd) in enumerate(
                        [
                            (-1.5, -1, 2, 0),
                            (-1, -1.5, 0, 2),
                            (1.5, -1, 2, 0),
                            (-1, 1.5, 0, 2),
                        ]
                    ):
                        x = int(cx + (col * self.grid_size))
                        y = int(cy + (row * self.grid_size))
                        d = self.grid_size
                        cv2.rectangle(
                            frame,
                            (x, y),
                            (x + d * xd, y + d * yd),
                            self.adjacent_colors[idx],
                            2,
                        )
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                bytes_per_line = 3 * w
                qt_image = QImage(
                    rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888
                )
                self.frame_ready.emit(qt_image, rgb_frame)
        cap.release()

    def stop(self):
        self._is_running = False
        self.wait()

    @Slot(str)
    def set_guide_face(self, face: str):
        self.rectangle_color = mappings.FACE_BGRS[face]
        self.adjacent_colors = [
            mappings.FACE_BGRS[adj_face] for adj_face in mappings.ADJ_FACES[face]
        ]


class MainMenuWidget(QWidget):
    go_to_solve = Signal()
    go_to_scramble = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Autocube")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        solve_btn = QPushButton("Solve Cube")
        solve_btn.setMinimumHeight(50)
        solve_btn.clicked.connect(self.go_to_solve.emit)

        scramble_btn = QPushButton("Scramble Cube")
        scramble_btn.setMinimumHeight(50)
        scramble_btn.clicked.connect(self.go_to_scramble.emit)

        layout.addWidget(title)
        layout.addWidget(solve_btn)
        layout.addWidget(scramble_btn)
        self.setLayout(layout)


class ScramblerWidget(QWidget):
    go_back = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.instruction_label = QLabel(
            "Place the cube in the robot\n(Yellow Up, Red Forward)"
        )
        self.instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instruction_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.scramble_btn = QPushButton("Generate and Execute Scramble")
        self.scramble_btn.setMinimumHeight(50)
        self.scramble_btn.clicked.connect(self.execute_scramble)

        self.back_btn = QPushButton("Back to Menu")
        self.back_btn.clicked.connect(self.go_back.emit)

        layout.addWidget(self.instruction_label)
        layout.addWidget(self.scramble_btn)
        layout.addWidget(self.back_btn)
        self.setLayout(layout)

    def execute_scramble(self):
        self.scramble_btn.setEnabled(False)
        self.instruction_label.setText("Generating scramble and moving robot...")
        QApplication.processEvents()  # Force GUI update before blocking thread

        # Generate a random 20-move scramble
        faces = ["U", "D", "F", "B", "R", "L"]
        modifiers = ["", "'", "2"]
        scramble_sequence = [
            random.choice(faces) + random.choice(modifiers) for _ in range(20)
        ]

        print(f"Scramble Generated: {' '.join(scramble_sequence)}")

        manipulator = CubeManipulator()
        motor_algorithm = manipulator.cube_to_motor_algorithm(
            Algorithm(scramble_sequence)
        )

        try:
            with Robot(EV3_ADDRESS, PORT) as robot:
                robot.connect()
                robot.apply_motor_algorithm(motor_algorithm)
            self.instruction_label.setText("Scramble complete!")
        except Exception as e:
            self.instruction_label.setText(f"Robot Error: {e}")

        solution = solve_cube(Cube(scramble_sequence))
        print(f"Solution to Scramble: {' '.join(solution)}")
        self.scramble_btn.setEnabled(True)


class ScannerWidget(QWidget):
    go_back = Signal()

    def __init__(self):
        super().__init__()
        self.scan_order = mappings.FACE_SCAN_ORDER
        self.current_face = 0
        self.scanned_data: dict[str, list[list[tuple[float, float, float]]]] = {}
        self.motor_algorithm = None
        self.latest_frame = None

        self.video_label = QLabel("Starting camera...")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.instruction_label = QLabel(
            f"Align the {self.scan_order[0]} face and click Scan."
        )
        self.instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instruction_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.scan_btn = QPushButton("Scan Face")
        self.scan_btn.setEnabled(False)
        self.scan_btn.clicked.connect(self.scan_current_face)

        self.back_btn = QPushButton("Back to Menu")
        self.back_btn.clicked.connect(self.go_back.emit)

        layout = QVBoxLayout()
        layout.addWidget(self.instruction_label)
        layout.addWidget(self.video_label)
        layout.addWidget(self.scan_btn)
        layout.addWidget(self.back_btn)
        self.setLayout(layout)

        self.camera_thread = CameraThread()
        self.camera_thread.set_guide_face(self.scan_order[0])
        self.camera_thread.frame_ready.connect(self.update_feed)
        self.camera_thread.start()

    @Slot(QImage, object)
    def update_feed(self, image: QImage, raw_frame):
        self.scan_btn.setEnabled(True)
        image.mirror(horizontally=True, vertically=False)
        self.video_label.setPixmap(QPixmap.fromImage(image))
        self.latest_frame = cv2.flip(raw_frame, 1)

    def scan_current_face(self):
        if self.latest_frame is None:
            return
        if (
            self.current_face >= len(self.scan_order)
            and self.motor_algorithm is not None
        ):
            self.execute_solution()
            return
        face_name = self.scan_order[self.current_face]
        h, w = self.latest_frame.shape[:2]
        cx, cy = w // 2, h // 2
        grid_size = self.camera_thread.grid_size
        face_colors = []
        for row in [-1, 0, 1]:
            row_colors = []
            for col in [1, 0, -1]:
                x = cx + (col * grid_size)
                y = cy + (row * grid_size)
                r, g, b = map(int, self.latest_frame[y, x])
                row_colors.append((r, g, b))
            face_colors.append(row_colors)
        self.scanned_data[face_name] = face_colors
        self.current_face += 1

        if self.current_face < len(self.scan_order):
            next_face = self.scan_order[self.current_face]
            self.camera_thread.set_guide_face(next_face)
            self.instruction_label.setText(
                f"Align the {next_face} face and click Scan."
            )
        else:
            self.calculate_solution()
            return

    def calculate_solution(self):
        position_instruction = (
            "Please position the cube in the robot\n"
            "with the yellow face facing up and the red face facing you."
        )
        self.scan_btn.setEnabled(False)
        self.instruction_label.setText("Scan complete, calculating solution...")
        self.video_label.setText(position_instruction)

        scanner = CubeScanner()
        scanner.update_center_colors(self.scanned_data, (1, 1))
        cube = scanner.rgb_to_cube(self.scanned_data)
        cube.state, error = autofix_cube_state(cube.state)

        print(cube.to_json())
        if error:
            print(error)

        solution = solve_cube(cube)
        manipulator = CubeManipulator()
        self.motor_algorithm = manipulator.cube_to_motor_algorithm(solution)

        print("Human solution steps:")
        print(solution)
        print("Motor steps:")
        print(self.motor_algorithm)

        self.instruction_label.setText("Solution found!")
        self.scan_btn.setText("Execute Solution")
        self.scan_btn.setEnabled(True)

    def execute_solution(self):
        if self.motor_algorithm is None:
            return
        self.scan_btn.setEnabled(False)
        try:
            with Robot(EV3_ADDRESS, PORT) as robot:
                robot.connect()
                robot.apply_motor_algorithm(self.motor_algorithm)
            self.instruction_label.setText("Solution executed. Cube should be solved.")
        except Exception as e:
            self.instruction_label.setText(f"Robot Error: {e}")
            self.scan_btn.setEnabled(True)

    def stop_camera(self):
        self.camera_thread.stop()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Autocube")
        self.resize(800, 600)

        self.stacked_widget = QStackedWidget()

        self.menu_widget = MainMenuWidget()
        self.scanner_widget = ScannerWidget()
        self.scrambler_widget = ScramblerWidget()

        self.stacked_widget.addWidget(self.menu_widget)
        self.stacked_widget.addWidget(self.scanner_widget)
        self.stacked_widget.addWidget(self.scrambler_widget)

        self.setCentralWidget(self.stacked_widget)

        self.menu_widget.go_to_solve.connect(
            lambda: self.stacked_widget.setCurrentWidget(self.scanner_widget)
        )
        self.menu_widget.go_to_scramble.connect(
            lambda: self.stacked_widget.setCurrentWidget(self.scrambler_widget)
        )

        self.scanner_widget.go_back.connect(
            lambda: self.stacked_widget.setCurrentWidget(self.menu_widget)
        )
        self.scrambler_widget.go_back.connect(
            lambda: self.stacked_widget.setCurrentWidget(self.menu_widget)
        )

    def closeEvent(self, event):
        self.scanner_widget.stop_camera()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
