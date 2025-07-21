import sys
import random
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QInputDialog, QComboBox
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QColor
import pyqtgraph as pg
from trend_window import TrendWindow


class RMSMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulated RMS Monitor")
        self.resize(1000, 550)
        

        # Core variables
        self.x_data = []
        self.y_data = []
        self.full_x_data = []
        self.full_y_data = []
        self.full_time_labels = []
        self.base_value = 1.0000
        self.target_trend = 0
        self.max_length = 20000
        self.running = False
        self.current_rms = self.base_value
        self.start_time = None
        self.elapsed_str = "00:00:00"
        self.speed = 1  # Default simulation speed multiplier

        # Main layout
        self.layout = QVBoxLayout(self)

        # Graph
        self.plot_widget = pg.PlotWidget(title="RMS Trend Line")
        self.plot_widget.setLabel('left', 'RMS Trend (mm/s)')
        self.plot_widget.setLabel('bottom', 'Time (minutes)')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setYRange(0.0, 5.0)
        self.curve = self.plot_widget.plot(pen=pg.mkPen('lime', width=1))
        self.layout.addWidget(self.plot_widget)

        self.add_class_I_thresholds()

        # Top display
        self.top_info_layout = QHBoxLayout()
        self.bottom_display = QLabel("Time: 00:00:00 | RMS: 1.0000")
        self.bottom_display.setStyleSheet("font-family: monospace; font-size: 14px;")
        self.toggle_controls_btn = QPushButton("  ")
        self.toggle_controls_btn.setFixedWidth(60)
        self.toggle_controls_btn.clicked.connect(self.toggle_controls)
        self.top_info_layout.addWidget(self.bottom_display)
        self.top_info_layout.addWidget(self.toggle_controls_btn)
        self.layout.addLayout(self.top_info_layout)

        # Controls
        self.control_widget = QWidget()
        self.control_layout = QHBoxLayout(self.control_widget)

        self.start_btn = QPushButton("Start")
        self.incline_btn = QPushButton("Incline")
        self.decline_btn = QPushButton("Decline")
        self.stabilize_btn = QPushButton("Stabilize")
        self.pause_btn = QPushButton("Pause")
        self.edit_time_btn = QPushButton("Edit Time")
        self.reset_time_btn = QPushButton("Reset Time")
        self.show_history_btn = QPushButton("Show Trend")

        self.rms_label = QLabel("Current RMS: 1.0000 ➖")
        self.rms_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.rms_edit = QLineEdit()
        self.rms_edit.setFixedWidth(80)
        self.rms_edit.setPlaceholderText("Edit RMS")
        self.rms_edit.returnPressed.connect(self.manual_edit_rms)

        self.elapsed_label = QLabel("Elapsed: 00:00:00")
        self.elapsed_label.setStyleSheet("font-family: monospace; font-weight: bold;")
        self.pause_time = None

        # Add controls
        self.control_layout.addWidget(self.start_btn)
        self.control_layout.addWidget(self.incline_btn)
        self.control_layout.addWidget(self.decline_btn)
        self.control_layout.addWidget(self.stabilize_btn)
        self.control_layout.addWidget(self.pause_btn)
        self.control_layout.addWidget(self.edit_time_btn)
        self.control_layout.addWidget(self.reset_time_btn)
        self.control_layout.addWidget(self.show_history_btn)
        self.control_layout.addWidget(self.rms_label)
        self.control_layout.addWidget(self.rms_edit)
        self.control_layout.addWidget(self.elapsed_label)

        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["1x", "2x", "4x", "6x", "8x", "10x", "20x", "30x"])
        self.speed_combo.setCurrentIndex(0)
        self.speed_combo.currentIndexChanged.connect(self.change_speed)
        self.control_layout.addWidget(QLabel("Speed:"))
        self.control_layout.addWidget(self.speed_combo)

        self.layout.addWidget(self.control_widget)

        # Connections
        self.start_btn.clicked.connect(self.start_simulation)
        self.incline_btn.clicked.connect(lambda: self.set_trend(1))
        self.decline_btn.clicked.connect(lambda: self.set_trend(-1))
        self.stabilize_btn.clicked.connect(lambda: self.set_trend(0))
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.edit_time_btn.clicked.connect(self.edit_time)
        self.reset_time_btn.clicked.connect(self.reset_time)
        self.show_history_btn.clicked.connect(self.show_trend_history)

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_logic)
        self.timer.start(1)

        self.update_button_styles()

    def change_speed(self):
        self.speed = int(self.speed_combo.currentText().replace('x', ''))

    def start_simulation(self):
        self.running = True
        self.start_btn.setEnabled(False)
        self.start_time = datetime.now()
        
        # Update RMS label on start
        arrow = "⬆️" if self.target_trend == 1 else "⬇️" if self.target_trend == -1 else "➖"
        self.rms_label.setText(f"Current RMS: {self.current_rms:.4f} {arrow}")

    def toggle_pause(self):
        if self.running:
            # Pause the simulation
            self.pause_time = datetime.now()
            self.running = False
            self.pause_btn.setText("Resume")
        else:
            # Resume and adjust start_time
            if self.pause_time:
                paused_duration = datetime.now() - self.pause_time
                self.start_time += paused_duration
            self.running = True
            self.pause_btn.setText("Pause")

    def toggle_controls(self):
        visible = not self.control_widget.isVisible()
        self.control_widget.setVisible(visible)
        self.toggle_controls_btn.setText("   " if not visible else "   ")

    def set_trend(self, trend):
        self.target_trend = trend
        self.update_button_styles()

    def update_button_styles(self):
        def style(btn, active):
            btn.setStyleSheet("background-color: lightblue; font-weight: bold;" if active else "")
        style(self.incline_btn, self.target_trend == 1)
        style(self.decline_btn, self.target_trend == -1)
        style(self.stabilize_btn, self.target_trend == 0)



        def toggle_pause(self):
            if self.running:
                # Pause the simulation
                self.pause_time = datetime.now()
                self.running = False
                self.pause_btn.setText("Resume")
            else:
                # Resume the simulation and adjust start_time to keep elapsed time consistent
                if self.pause_time:
                    paused_duration = datetime.now() - self.pause_time
                    self.start_time += paused_duration
                self.running = True
                self.pause_btn.setText("Pause")

    def manual_edit_rms(self):
        try:
            val = float(self.rms_edit.text())
            self.current_rms = val
            arrow = "⬆️" if self.target_trend == 1 else "⬇️" if self.target_trend == -1 else "➖"
            self.rms_label.setText(f"Current RMS: {self.current_rms:.4f} {arrow}")
        except ValueError:
            pass
        finally:
            self.rms_edit.clearFocus()

    def edit_time(self):
        input_time, ok = QInputDialog.getText(self, "Edit Time", "Enter time (HH:MM:SS):")
        if ok:
            try:
                h, m, s = map(int, input_time.strip().split(":"))
                self.start_time = datetime.now() - timedelta(hours=h, minutes=m, seconds=s)
            except:
                pass

    def reset_time(self):
        self.start_time = datetime.now()

    def update_logic(self):
        if not self.running or not self.start_time:
            return

        # Simulated fast-forward time
        real_elapsed = datetime.now() - self.start_time
        simulated_seconds = real_elapsed.total_seconds() * self.speed
        time_in_min = simulated_seconds / 60.0
        self.elapsed_str = str(timedelta(seconds=int(simulated_seconds)))
        self.elapsed_label.setText(f"Elapsed: {self.elapsed_str}")

        # Simulated RMS update
        noise = random.uniform(-0.0002, 0.0002) * self.speed
        drift = self.target_trend * 0.00001 * self.speed
        self.current_rms += noise + drift
        self.current_rms = max(0, self.current_rms)

        arrow = "⬆️" if self.target_trend == 1 else "⬇️" if self.target_trend == -1 else "➖"
        self.rms_label.setText(f"Current RMS: {self.current_rms:.4f} {arrow}")

        self.x_data.append(time_in_min)
        self.y_data.append(self.current_rms)
        self.full_x_data.append(time_in_min)
        self.full_y_data.append(self.current_rms)
        simulated_datetime = self.start_time + timedelta(seconds=simulated_seconds)
        self.full_time_labels.append(simulated_datetime.strftime("%H:%M:%S"))

        if len(self.x_data) > self.max_length:
            self.x_data = self.x_data[-self.max_length:]
            self.y_data = self.y_data[-self.max_length:]

        self.curve.setData(self.x_data, self.y_data)
        self.plot_widget.setXRange(max(0, time_in_min - 0.5), time_in_min)

        simulated_datetime = self.start_time + timedelta(seconds=simulated_seconds)
        self.bottom_display.setText(
            f"Time: {simulated_datetime.strftime('%H:%M:%S')} | RMS: {self.current_rms:.4f}"
)

    def show_trend_history(self):
        self.trend_window = TrendWindow(self.full_x_data, self.full_y_data, self.full_time_labels)
        self.trend_window.show()

    def add_class_I_thresholds(self):
        thresholds = [
            (1.12, "Good", QColor(0, 255, 0, 100)),
            (2.8, "Satisfactory", QColor(255, 255, 0, 100)),
            (4.50, "Unsatisfactory", QColor(255, 165, 0, 100)),
            (7.10, "Unacceptable", QColor(255, 0, 0, 100))
        ]
        for value, label, color in thresholds:
            line = pg.InfiniteLine(pos=value, angle=0, pen=pg.mkPen(color=color, width=2, style=Qt.DashLine))
            text = pg.TextItem(label, anchor=(0, 0), color=color)
            self.plot_widget.addItem(line)
            self.plot_widget.addItem(text)
            text.setPos(0.01, value - 0.02)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = RMSMonitor()
    win.show()
    sys.exit(app.exec_())
