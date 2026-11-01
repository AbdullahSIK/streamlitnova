
import os
import subprocess
from collections import deque

import psutil

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QPainterPath
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
)


class LiveGraph(QWidget):
    """A lightweight scrolling graph for the last 60 readings."""

    def __init__(self, title, parent=None):
        super().__init__(parent)

        self.title = title
        self.values = deque(maxlen=60)
        self.line_color = QColor("#A58BFF")
        self.setMinimumHeight(155)

    def add_value(self, value):
        self.values.append(value)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        area = self.rect().adjusted(12, 12, -12, -12)

        painter.setPen(QColor("#AAB5C8"))
        painter.drawText(
            area.left(),
            area.top() + 10,
            self.title
        )

        graph = area.adjusted(0, 22, 0, -8)

        # Grid lines
        painter.setPen(QPen(QColor("#26344A"), 1))

        for i in range(5):
            y = graph.top() + (graph.height() * i / 4)
            painter.drawLine(
                int(graph.left()),
                int(y),
                int(graph.right()),
                int(y)
            )

        for label, percentage in [
            ("100%", 0),
            ("50%", 0.5),
            ("0%", 1),
        ]:
            y = graph.top() + graph.height() * percentage
            painter.setPen(QColor("#718096"))
            painter.drawText(
                int(graph.right() - 35),
                int(y - 3),
                label
            )

        if len(self.values) < 2:
            painter.setPen(QColor("#718096"))
            painter.drawText(
                graph,
                Qt.AlignmentFlag.AlignCenter,
                "Collecting readings..."
            )
            return

        path = QPainterPath()

        for index, value in enumerate(self.values):
            x = graph.left() + (
                index / (len(self.values) - 1)
            ) * graph.width()

            y = graph.bottom() - (
                max(0, min(100, value)) / 100
            ) * graph.height()

            if index == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)

        painter.setPen(
            QPen(
                self.line_color,
                2.5,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin
            )
        )

        painter.drawPath(path)


class MetricCard(QFrame):

    def __init__(self, title, parent=None):
        super().__init__(parent)

        self.setObjectName("MonitorCard")
        self.setMinimumHeight(112)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(17, 13, 17, 13)
        layout.setSpacing(7)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("""
            color: #94A3B8;
            font-size: 10px;
            font-weight: bold;
        """)

        self.value_label = QLabel("--")
        self.value_label.setStyleSheet("""
            color: #E8ECF5;
            font-size: 25px;
            font-weight: bold;
        """)

        self.detail_label = QLabel("Waiting for readings")
        self.detail_label.setStyleSheet("""
            color: #A58BFF;
            font-size: 11px;
        """)

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.detail_label)
        layout.addStretch()

    def set_values(self, value, detail):
        self.value_label.setText(value)
        self.detail_label.setText(detail)


class PCMonitorPage(QWidget):

    def __init__(self):
        super().__init__()

        self.setObjectName("ContentArea")

        self.cpu_history = deque(maxlen=60)
        self.ram_history = deque(maxlen=60)
        self.gpu_history = deque(maxlen=60)

        self.gpu_available = False
        self.gpu_name = "NVIDIA GPU"

        self.last_cpu_reading = psutil.cpu_percent(
            interval=None
        )

        main = QVBoxLayout(self)
        main.setContentsMargins(30, 25, 30, 25)
        main.setSpacing(17)

        # Header
        title = QLabel("PC Monitor")
        title.setObjectName("PageTitle")

        subtitle = QLabel(
            "Real-time performance monitoring • Refreshes every second"
        )
        subtitle.setObjectName("MutedText")

        self.status_label = QLabel("INITIALIZING MONITOR")
        self.status_label.setStyleSheet("""
            color: #A58BFF;
            font-size: 10px;
            font-weight: bold;
        """)

        main.addWidget(self.status_label)
        main.addWidget(title)
        main.addWidget(subtitle)

        # Metric cards
        grid = QGridLayout()
        grid.setSpacing(12)

        self.cpu_card = MetricCard("CPU USAGE")
        self.ram_card = MetricCard("RAM USAGE")
        self.gpu_card = MetricCard("GPU USAGE")
        self.disk_card = MetricCard("SYSTEM DRIVE")

        grid.addWidget(self.cpu_card, 0, 0)
        grid.addWidget(self.ram_card, 0, 1)
        grid.addWidget(self.gpu_card, 1, 0)
        grid.addWidget(self.disk_card, 1, 1)

        main.addLayout(grid)

        # Graphs
        graph_title = QLabel("LIVE PERFORMANCE")
        graph_title.setObjectName("CardTitle")
        main.addWidget(graph_title)

        self.cpu_graph = LiveGraph("CPU")
        self.ram_graph = LiveGraph("RAM")
        self.gpu_graph = LiveGraph("GPU")

        self.cpu_graph.line_color = QColor("#A58BFF")
        self.ram_graph.line_color = QColor("#36C8E8")
        self.gpu_graph.line_color = QColor("#61DDAA")

        for graph in [
            self.cpu_graph,
            self.ram_graph,
            self.gpu_graph
        ]:
            graph.setObjectName("MonitorCard")

        graphs = QGridLayout()
        graphs.setSpacing(12)

        graphs.addWidget(self.cpu_graph, 0, 0)
        graphs.addWidget(self.ram_graph, 0, 1)
        graphs.addWidget(self.gpu_graph, 1, 0, 1, 2)

        main.addLayout(graphs)
        main.addStretch()

        # One-second update timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_metrics)
        self.timer.start(1000)

        self.update_metrics()

    def read_gpu(self):
        """Read NVIDIA GPU information if nvidia-smi is available."""

        command = [
            "nvidia-smi",
            "--query-gpu=name,utilization.gpu,memory.used,"
            "memory.total,temperature.gpu",
            "--format=csv,noheader,nounits"
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=2,
                creationflags=getattr(
                    subprocess,
                    "CREATE_NO_WINDOW",
                    0
                )
            )

            if result.returncode != 0:
                return None

            parts = [
                item.strip()
                for item in result.stdout.strip().split(",")
            ]

            if len(parts) < 5:
                return None

            return {
                "name": parts[0],
                "usage": float(parts[1]),
                "memory_used": float(parts[2]),
                "memory_total": float(parts[3]),
                "temperature": float(parts[4]),
            }

        except (
            FileNotFoundError,
            subprocess.TimeoutExpired,
            ValueError,
            OSError
        ):
            return None

    def update_metrics(self):

        # CPU
        cpu = psutil.cpu_percent(interval=None)

        # RAM
        memory = psutil.virtual_memory()
        ram = memory.percent

        # System drive
        drive = os.environ.get("SystemDrive", "C:") + "\\"

        try:
            disk = psutil.disk_usage(drive)
            disk_percent = disk.percent
            disk_detail = (
                f"{disk.free / (1024 ** 3):.1f} GB free"
            )
        except OSError:
            disk_percent = 0
            disk_detail = "Drive information unavailable"

        # GPU
        gpu = self.read_gpu()

        if gpu:
            self.gpu_available = True
            self.gpu_name = gpu["name"]

            gpu_usage = gpu["usage"]
            gpu_memory = (
                f'{gpu["memory_used"]:.0f} / '
                f'{gpu["memory_total"]:.0f} MB VRAM'
            )
            gpu_temperature = (
                f'{gpu["temperature"]:.0f} °C'
            )

            self.gpu_card.set_values(
                f"{gpu_usage:.0f}%",
                f"{gpu_memory} • {gpu_temperature}"
            )

            self.gpu_graph.add_value(gpu_usage)

        else:
            self.gpu_available = False
            self.gpu_card.set_values(
                "N/A",
                "NVIDIA monitoring unavailable"
            )

        # Update cards
        self.cpu_card.set_values(
            f"{cpu:.0f}%",
            f"{psutil.cpu_count(logical=True)} logical processors"
        )

        self.ram_card.set_values(
            f"{ram:.0f}%",
            f"{memory.used / (1024 ** 3):.1f} / "
            f"{memory.total / (1024 ** 3):.1f} GB used"
        )

        self.disk_card.set_values(
            f"{disk_percent:.0f}%",
            disk_detail
        )

        # Update graphs
        self.cpu_graph.add_value(cpu)
        self.ram_graph.add_value(ram)

        # Status
        self.status_label.setText(
            "LIVE • UPDATING EVERY SECOND"
        )

    def showEvent(self, event):
        super().showEvent(event)
        self.timer.start(1000)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.timer.stop()
    