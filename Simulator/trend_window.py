import os
from datetime import datetime
from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
import pyqtgraph as pg


class TrendWindow(QMainWindow):
    def __init__(self, x_data, y_data, time_labels=None):
        super().__init__()
        self.setWindowTitle("Full RMS History")
        self.resize(800, 500)

        self.x_data = x_data
        self.y_data = y_data
        self.time_labels = time_labels

        # Central layout
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        # Plot setup
        self.plot_widget = pg.PlotWidget(title="Complete RMS History")
        self.plot_widget.setLabel('left', 'RMS Trend (mm/s)')
        self.plot_widget.setLabel('bottom', 'Time (minutes)')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setYRange(0.0, 8.0)
        layout.addWidget(self.plot_widget)

        self.curve = self.plot_widget.plot(x_data, y_data, pen=pg.mkPen('cyan', width=1))

        if self.x_data:
            vb = self.plot_widget.getViewBox()
            vb.setXRange(0, self.x_data[-1], padding=0)
            vb.enableAutoRange(axis=vb.XAxis, enable=False)

        thresholds = [
            (0.28, '#90EE90', 'Good'),
            (1.12, '#FFFF99', 'Satisfactory'),
            (2.80, '#FFD580', 'Unsatisfactory'),
            (7.10, '#FF9999', 'Unacceptable'),
        ]

        for y_val, color, label in thresholds:
            line = pg.InfiniteLine(pos=y_val, angle=0, pen=pg.mkPen(color, width=1.5, style=Qt.DashLine))
            self.plot_widget.addItem(line)
            text = pg.TextItem(text=f"{label} ({y_val:.2f})", color=color, anchor=(1, 1))
            text.setPos(x_data[-1] if x_data else 0, y_val)
            self.plot_widget.addItem(text)

        scatter = pg.ScatterPlotItem()
        points = []
        last_zone = None

        for i, rms in enumerate(y_data):
            if rms < 0.28:
                zone = 'Good'
            elif rms < 1.12:
                zone = 'Satisfactory'
            elif rms < 2.80:
                zone = 'Unsatisfactory'
            else:
                zone = 'Unacceptable'

            if zone != last_zone:
                color = 'white' if zone != 'Unacceptable' else 'red'
                time_text = time_labels[i] if time_labels else f"{x_data[i]:.2f} min"
                points.append({
                    'pos': (x_data[i], rms),
                    'brush': pg.mkBrush(color),
                    'symbol': 'o',
                    'size': 8,
                    'pen': pg.mkPen('black', width=1)
                })
                label = pg.TextItem(text=f"{time_text}\n{rms:.2f} mm/s", anchor=(0.5, 1), color='white')
                label.setPos(x_data[i], rms)
                self.plot_widget.addItem(label)
                last_zone = zone

        scatter.addPoints(points)
        self.plot_widget.addItem(scatter)

        export_button = QPushButton("Export to TXT")
        export_button.clicked.connect(self.export_txt)
        layout.addWidget(export_button)

        self.setCentralWidget(central_widget)

    def export_txt(self):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        logs_folder = os.path.join(desktop, "RMS logs")
        os.makedirs(logs_folder, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_path = os.path.join(logs_folder, f"rms_log_{timestamp}.txt")

        try:
            with open(file_path, 'w') as file:
                file.write("Time\tIndex\tRMS (mm/s)\n")
                for i in range(len(self.x_data)):
                    time_str = self.time_labels[i] if self.time_labels else "N/A"
                    index = i + 1
                    rms = self.y_data[i]
                    file.write(f"{time_str}\t{index}\t{rms:.4f}\n")
            print(f"TXT exported to: {file_path}")
        except Exception as e:
            print(f"Failed to export TXT: {e}")

