
from datetime import datetime

from PySide6.QtCore import Qt, QDate, QTime, QTimer
from PySide6.QtGui import QColor, QBrush, QTextCharFormat
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QCalendarWidget,
    QListWidget,
    QListWidgetItem,
    QDialog,
    QLineEdit,
    QTextEdit,
    QDateEdit,
    QTimeEdit,
    QComboBox,
    QFormLayout,
    QMessageBox,
    QFrame,
    QSplitter,
    QAbstractItemView
)

from core.calendar_database import CalendarDatabase


class EventDialog(QDialog):

    def __init__(self, parent=None, event=None, selected_date=None):
        super().__init__(parent)

        self.setWindowTitle(
            "Edit Event" if event else "Create Event"
        )
        self.setMinimumWidth(420)

        self.setStyleSheet("""
            QDialog {
                background-color: #090b12;
                color: #e8eaff;
            }

            QLabel {
                color: #bfc5df;
                font-size: 13px;
            }

            QLineEdit, QTextEdit, QDateEdit, QTimeEdit,
            QComboBox {
                background-color: #151a29;
                color: white;
                border: 1px solid #343c55;
                border-radius: 7px;
                padding: 9px;
                selection-background-color: #7857ff;
            }

            QPushButton {
                background-color: #7857ff;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 10px 18px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #9278ff;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        heading = QLabel(
            "EDIT EVENT" if event else "NEW EVENT"
        )
        heading.setStyleSheet("""
            font-size: 19px;
            font-weight: bold;
            color: #a58bff;
        """)
        layout.addWidget(heading)

        form = QFormLayout()
        form.setSpacing(12)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter event title")

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText(
            "Add event details..."
        )
        self.description_input.setMaximumHeight(90)

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("dd MMM yyyy")
        self.date_input.setDate(
            selected_date or QDate.currentDate()
        )

        self.time_input = QTimeEdit()
        self.time_input.setDisplayFormat("HH:mm")
        self.time_input.setTime(QTime.currentTime())

        self.reminder_input = QComboBox()
        self.reminder_input.addItem("No reminder", 0)
        self.reminder_input.addItem("5 minutes before", 5)
        self.reminder_input.addItem("10 minutes before", 10)
        self.reminder_input.addItem("15 minutes before", 15)
        self.reminder_input.addItem("30 minutes before", 30)
        self.reminder_input.addItem("60 minutes before", 60)

        form.addRow("Event title", self.title_input)
        form.addRow("Description", self.description_input)
        form.addRow("Date", self.date_input)
        form.addRow("Time", self.time_input)
        form.addRow("Reminder", self.reminder_input)

        layout.addLayout(form)

        buttons = QHBoxLayout()

        self.cancel_button = QPushButton("Cancel")
        self.save_button = QPushButton(
            "Update Event" if event else "Create Event"
        )

        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #252b3b;
            }
        """)

        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self.validate_and_accept)

        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.save_button)

        layout.addLayout(buttons)

        if event:
            self.title_input.setText(event["title"])
            self.description_input.setPlainText(
                event["description"]
            )

            self.date_input.setDate(
                QDate.fromString(
                    event["event_date"],
                    "yyyy-MM-dd"
                )
            )

            if event["event_time"]:
                self.time_input.setTime(
                    QTime.fromString(
                        event["event_time"],
                        "HH:mm"
                    )
                )

            index = self.reminder_input.findData(
                event["reminder_minutes"]
            )

            if index >= 0:
                self.reminder_input.setCurrentIndex(index)

    def validate_and_accept(self):

        if not self.title_input.text().strip():
            QMessageBox.warning(
                self,
                "Missing Title",
                "Please enter an event title."
            )
            return

        self.accept()

    def get_data(self):

        return {
            "title": self.title_input.text().strip(),
            "description": self.description_input.toPlainText().strip(),
            "event_date": self.date_input.date().toString(
                "yyyy-MM-dd"
            ),
            "event_time": self.time_input.time().toString(
                "HH:mm"
            ),
            "reminder_minutes": self.reminder_input.currentData()
        }


class CalendarPage(QWidget):

    def __init__(self):
        super().__init__()

        self.db = CalendarDatabase()

        self.setStyleSheet("""
            QWidget {
                background-color: #090b12;
                color: #e8eaff;
                font-family: Segoe UI;
            }

            QLabel {
                color: #e8eaff;
            }

            QPushButton {
                background-color: #7857ff;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 10px 15px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #9278ff;
            }

            QListWidget {
                background-color: #111625;
                border: 1px solid #293149;
                border-radius: 9px;
                padding: 7px;
                outline: none;
            }

            QListWidget::item {
                padding: 10px;
                border-radius: 5px;
            }

            QListWidget::item:selected {
                background-color: #493b83;
                color: white;
            }
        """)

        self.setup_ui()
        self.refresh_calendar()
        self.refresh_events()
        self.refresh_upcoming()

        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(
            self.check_reminders
        )
        self.reminder_timer.start(15000)

        self.check_reminders()

    def setup_ui(self):

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 22, 25, 22)
        main_layout.setSpacing(18)

        # Header

        header = QHBoxLayout()

        title_box = QVBoxLayout()

        title = QLabel("CALENDAR")
        title.setStyleSheet("""
            font-size: 25px;
            font-weight: bold;
            color: #a58bff;
        """)

        subtitle = QLabel(
            "Manage your schedule and upcoming events"
        )
        subtitle.setStyleSheet(
            "color: #858da8; font-size: 12px;"
        )

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        header.addLayout(title_box)
        header.addStretch()

        self.add_button = QPushButton("+ Add Event")
        self.add_button.clicked.connect(self.add_event)

        header.addWidget(self.add_button)

        main_layout.addLayout(header)

        # Main content

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Calendar section

        calendar_frame = QFrame()
        calendar_frame.setStyleSheet("""
            QFrame {
                background-color: #101523;
                border: 1px solid #293149;
                border-radius: 12px;
            }
        """)

        calendar_layout = QVBoxLayout(calendar_frame)
        calendar_layout.setContentsMargins(15, 15, 15, 15)

        calendar_heading = QLabel("MONTH VIEW")
        calendar_heading.setStyleSheet("""
            color: #a58bff;
            font-size: 13px;
            font-weight: bold;
        """)

        calendar_layout.addWidget(calendar_heading)

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setNavigationBarVisible(True)
        self.calendar.setFirstDayOfWeek(
            Qt.DayOfWeek.Monday
        )
        self.calendar.setMinimumHeight(370)

        self.calendar.setStyleSheet("""
            QCalendarWidget QWidget {
                background-color: #101523;
                color: #e8eaff;
            }

            QCalendarWidget QToolButton {
                color: #a58bff;
                background-color: #1b2235;
                border-radius: 5px;
                padding: 6px;
                margin: 3px;
            }

            QCalendarWidget QToolButton:hover {
                background-color: #343052;
            }

            QCalendarWidget QSpinBox {
                background-color: #1b2235;
                color: white;
                border: none;
            }

            QCalendarWidget QAbstractItemView {
                background-color: #101523;
                color: #e8eaff;
                selection-background-color: #7857ff;
                selection-color: white;
                outline: none;
            }
        """)

        self.calendar.selectionChanged.connect(
            self.refresh_events
        )

        self.calendar.currentPageChanged.connect(
            self.refresh_calendar
        )

        calendar_layout.addWidget(self.calendar)

        splitter.addWidget(calendar_frame)

        # Right panel

        right_frame = QFrame()
        right_frame.setStyleSheet("""
            QFrame {
                background-color: #101523;
                border: 1px solid #293149;
                border-radius: 12px;
            }
        """)

        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.setSpacing(10)

        selected_heading = QLabel("SELECTED DATE EVENTS")
        selected_heading.setStyleSheet("""
            color: #a58bff;
            font-size: 13px;
            font-weight: bold;
        """)

        self.selected_date_label = QLabel()
        self.selected_date_label.setStyleSheet(
            "color: #858da8; font-size: 12px;"
        )

        self.event_list = QListWidget()
        self.event_list.setSelectionMode(
            QAbstractItemView.SingleSelection
        )
        self.event_list.itemDoubleClicked.connect(
            self.edit_selected_event
        )

        right_layout.addWidget(selected_heading)
        right_layout.addWidget(self.selected_date_label)
        right_layout.addWidget(self.event_list, 3)

        # Event action buttons

        action_layout = QHBoxLayout()

        self.edit_button = QPushButton("Edit")
        self.delete_button = QPushButton("Delete")

        self.edit_button.setStyleSheet("""
            QPushButton {
                background-color: #293149;
            }
        """)

        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: #a43c53;
            }
        """)

        self.edit_button.clicked.connect(
            self.edit_selected_event
        )

        self.delete_button.clicked.connect(
            self.delete_selected_event
        )

        action_layout.addWidget(self.edit_button)
        action_layout.addWidget(self.delete_button)

        right_layout.addLayout(action_layout)

        # Upcoming events

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(
            "background-color: #293149; max-height: 1px;"
        )

        upcoming_heading = QLabel("UPCOMING EVENTS")
        upcoming_heading.setStyleSheet("""
            color: #a58bff;
            font-size: 13px;
            font-weight: bold;
        """)

        self.upcoming_list = QListWidget()
        self.upcoming_list.setMaximumHeight(190)
        self.upcoming_list.itemClicked.connect(
            self.open_upcoming_event
        )

        right_layout.addWidget(divider)
        right_layout.addWidget(upcoming_heading)
        right_layout.addWidget(self.upcoming_list, 2)

        splitter.addWidget(right_frame)

        splitter.setSizes([600, 400])

        main_layout.addWidget(splitter)

        self.edit_button.setEnabled(False)
        self.delete_button.setEnabled(False)

        self.event_list.itemSelectionChanged.connect(
            self.update_action_buttons
        )

    def update_action_buttons(self):

        selected = bool(self.event_list.selectedItems())

        self.edit_button.setEnabled(selected)
        self.delete_button.setEnabled(selected)

    def selected_date_string(self):

        return self.calendar.selectedDate().toString(
            "yyyy-MM-dd"
        )

    def refresh_calendar(self, *args):

        self.calendar.setDateTextFormat(
            QDate(),
            QTextCharFormat()
        )

        today_format = QTextCharFormat()
        today_format.setForeground(
            QBrush(QColor("#ffffff"))
        )
        today_format.setBackground(
            QBrush(QColor("#493b83"))
        )
        today_format.setFontWeight(700)

        self.calendar.setDateTextFormat(
            QDate.currentDate(),
            today_format
        )

        event_format = QTextCharFormat()
        event_format.setForeground(
            QBrush(QColor("#73f0c0"))
        )
        event_format.setFontWeight(700)

        for event in self.db.get_events():

            event_date = QDate.fromString(
                event["event_date"],
                "yyyy-MM-dd"
            )

            if event_date.isValid():
                self.calendar.setDateTextFormat(
                    event_date,
                    event_format
                )

        self.calendar.update()

    def refresh_events(self):

        selected_date = self.calendar.selectedDate()

        self.selected_date_label.setText(
            selected_date.toString("dddd, dd MMMM yyyy")
        )

        self.event_list.clear()

        events = self.db.get_events(
            self.selected_date_string()
        )

        for event in events:

            time_text = event["event_time"] or "No time"

            item = QListWidgetItem(
                f"{time_text}   |   {event['title']}"
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                event["id"]
            )

            if event["description"]:
                item.setToolTip(event["description"])

            self.event_list.addItem(item)

        if not events:

            item = QListWidgetItem(
                "No events scheduled for this date."
            )
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.event_list.addItem(item)

        self.update_action_buttons()

    def refresh_upcoming(self):

        self.upcoming_list.clear()

        events = self.db.get_upcoming_events(10)

        for event in events:

            date = QDate.fromString(
                event["event_date"],
                "yyyy-MM-dd"
            )

            date_text = date.toString("dd MMM")

            time_text = event["event_time"] or "--:--"

            item = QListWidgetItem(
                f"{date_text}  {time_text}  |  {event['title']}"
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                event["id"]
            )

            self.upcoming_list.addItem(item)

        if not events:

            item = QListWidgetItem(
                "No upcoming events."
            )
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.upcoming_list.addItem(item)

    def add_event(self):

        dialog = EventDialog(
            self,
            selected_date=self.calendar.selectedDate()
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:

            data = dialog.get_data()

            self.db.add_event(
                data["title"],
                data["description"],
                data["event_date"],
                data["event_time"],
                data["reminder_minutes"]
            )

            self.after_event_change(
                data["event_date"]
            )

    def edit_selected_event(self):

        item = self.event_list.currentItem()

        if not item:
            return

        event_id = item.data(
            Qt.ItemDataRole.UserRole
        )

        if event_id is None:
            return

        event = self.db.get_event(event_id)

        if not event:
            return

        dialog = EventDialog(
            self,
            event=event
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:

            data = dialog.get_data()

            self.db.update_event(
                event_id,
                data["title"],
                data["description"],
                data["event_date"],
                data["event_time"],
                data["reminder_minutes"]
            )

            self.after_event_change(
                data["event_date"]
            )

    def delete_selected_event(self):

        item = self.event_list.currentItem()

        if not item:
            return

        event_id = item.data(
            Qt.ItemDataRole.UserRole
        )

        if event_id is None:
            return

        answer = QMessageBox.question(
            self,
            "Delete Event",
            "Are you sure you want to delete this event?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
        )

        if answer == QMessageBox.StandardButton.Yes:

            self.db.delete_event(event_id)

            self.after_event_change(
                self.selected_date_string()
            )

    def open_upcoming_event(self, item):

        event_id = item.data(
            Qt.ItemDataRole.UserRole
        )

        if event_id is None:
            return

        event = self.db.get_event(event_id)

        if not event:
            return

        date = QDate.fromString(
            event["event_date"],
            "yyyy-MM-dd"
        )

        self.calendar.setSelectedDate(date)

        self.calendar.setCurrentPage(
            date.year(),
            date.month()
        )

        self.refresh_events()

    def after_event_change(self, event_date):

        date = QDate.fromString(
            event_date,
            "yyyy-MM-dd"
        )

        if date.isValid():

            self.calendar.setCurrentPage(
                date.year(),
                date.month()
            )

            self.calendar.setSelectedDate(date)

        self.refresh_calendar()
        self.refresh_events()
        self.refresh_upcoming()

    def check_reminders(self):

        try:

            events = self.db.get_pending_reminders()

            for event in events:

                # Mark first to prevent duplicate notifications.
                self.db.mark_reminder_sent(event["id"])

                QMessageBox.information(
                    self,
                    "NOVA Reminder",
                    (
                        f"Upcoming event:\n\n"
                        f"{event['title']}\n\n"
                        f"Date: {event['event_date']}\n"
                        f"Time: {event['event_time']}"
                    )
                )

        except Exception as error:

            print("NOVA reminder error:", error)
