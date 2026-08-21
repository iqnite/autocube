import sys

import cv2
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from controller.connector import CubeManipulator, CubeScanner, Robot
from controller import mappings
from logic.autofix import autofix_scan
from logic.solver import solve_cube

EV3_ADDRESS = "ev3dev.local"
PORT = 65432


class CameraThread(QThread):
    frame_ready = Signal(QImage, object)

    def __init__(self):
        super().__init__()
        self._is_running = True
        self.grid_size = 100
        self.rectangle_color = mappings.FACE_BGRS["U"]

    def run(self):
        cap = cv2.VideoCapture(0)
        while self._is_running:
            ret, frame = cap.read()
            if ret:
                h, w = frame.shape[:2]
                cx, cy = w // 2, h // 2
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

    @Slot("tuple[int, int, int]")
    def set_guide_color(self, color: tuple[int, int, int]):
        self.rectangle_color = color


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Autocube - Vision Scanner")
        self.scan_order = mappings.FACE_SCAN_ORDER
        self.current_face = 0
        self.scanned_data: dict[str, list[list[tuple[float, float, float]]]] = {}
        self.motor_algorithm = None
        self.latest_frame = None
        self.video_label = QLabel("Starting camera...")
        self.instruction_label = QLabel(
            f"Align the {self.scan_order[0]} face and click Scan."
        )
        self.instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instruction_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.scan_btn = QPushButton("Scan Face")
        self.scan_btn.clicked.connect(self.scan_current_face)
        layout = QVBoxLayout()
        layout.addWidget(self.instruction_label)
        layout.addWidget(self.video_label)
        layout.addWidget(self.scan_btn)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.camera_thread = CameraThread()
        self.camera_thread.frame_ready.connect(self.update_feed)
        self.camera_thread.start()

    @Slot(QImage, object)
    def update_feed(self, image: QImage, raw_frame):
        image.mirror(horizontally=True, vertically=False)
        self.video_label.setPixmap(QPixmap.fromImage(image))
        self.latest_frame = raw_frame

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
            for col in [-1, 0, 1]:
                x = cx + (col * grid_size)
                y = cy + (row * grid_size)
                r, g, b = map(int, self.latest_frame[y, x])
                row_colors.append((r, g, b))
            face_colors.append(row_colors)
        self.scanned_data[face_name] = face_colors
        self.current_face += 1
        if self.current_face < len(self.scan_order):
            next_face = self.scan_order[self.current_face]
            self.camera_thread.set_guide_color(mappings.FACE_BGRS[next_face])
            self.instruction_label.setText(
                f"Align the {next_face} face and click Scan."
            )
        else:
            self.calculate_solution()
            return

    def calculate_solution(self):
        position_instruction = (
            "Please position the cube in the robot"
            " with the yellow face facing up and the red face facing you."
        )
        self.instruction_label.setText(
            f"Scan complete, calculating solution...\n{position_instruction}"
        )
        self.scan_btn.setEnabled(False)
        scanner = CubeScanner()
        scanner.update_center_colors(self.scanned_data, (1, 1))
        cube = scanner.rgb_to_cube(self.scanned_data)
        cube.state = autofix_scan(cube.state)[0]
        print(cube.to_json())
        solution = solve_cube(cube)
        manipulator = CubeManipulator()
        self.motor_algorithm = manipulator.cube_to_motor_algorithm(solution)
        print(solution)
        print(self.motor_algorithm)
        self.instruction_label.setText(f"Solution found.\n{position_instruction}")
        self.scan_btn.setText("Execute Solution")
        self.scan_btn.setEnabled(True)

    def execute_solution(self):
        if self.motor_algorithm is None:
            return
        self.scan_btn.setEnabled(False)
        with Robot(EV3_ADDRESS, PORT) as robot:
            robot.connect()
            robot.apply_motor_algorithm(self.motor_algorithm)

    def closeEvent(self, event):
        self.camera_thread.stop()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
