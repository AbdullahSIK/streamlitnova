
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QPushButton, QWidget
)
from PySide6.QtCore import Signal


class Sidebar(QFrame):

    page_changed = Signal(str)

    def __init__(self):
        super().__init__()

        self.setObjectName("Sidebar")
        self.setFixedWidth(225)

        self.buttons = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 25, 15, 15)
        layout.setSpacing(8)

        # Brand
        brand = QLabel("NOVA")
        brand.setObjectName("Brand")

        subtitle = QLabel("DIGITAL COMMAND CENTER")
        subtitle.setObjectName("BrandSubtitle")

        layout.addWidget(brand)
        layout.addWidget(subtitle)
        layout.addSpacing(35)

        section = QLabel("WORKSPACE")
        section.setObjectName("MutedText")
        layout.addWidget(section)

        pages = [
            ("Dashboard", "⌂"),
            ("Tasks", "✓"),
            ("Calendar", "▦"),
            ("Notes", "▤"),
            ("PC Monitor", "◈"),
            ("NOVA AI", "✧"),
        ]

        for name, symbol in pages:
            button = QPushButton(f"   {symbol}     {name}")
            button.setObjectName("NavButton")
            button.setCursor(__import__(
                "PySide6.QtCore", fromlist=["Qt"]
            ).Qt.CursorShape.PointingHandCursor)

            button.setCheckable(True)
            button.clicked.connect(
                lambda checked=False, page=name:
                self.page_changed.emit(page)
            )

            self.buttons[name] = button
            layout.addWidget(button)

        layout.addStretch()

        settings = QPushButton("   ⚙     Settings")
        settings.setObjectName("NavButton")
        settings.setCursor(
            __import__("PySide6.QtCore", fromlist=["Qt"])
            .Qt.CursorShape.PointingHandCursor
        )
        settings.clicked.connect(
            lambda: self.page_changed.emit("Settings")
        )

        self.buttons["Settings"] = settings
        layout.addWidget(settings)

        self.set_active("Dashboard")

    def set_active(self, page_name):

        for name, button in self.buttons.items():
            active = name == page_name

            button.setProperty("active", active)

            button.style().unpolish(button)
            button.style().polish(button)
            button.update()
