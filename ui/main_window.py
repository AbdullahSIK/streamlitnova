
from datetime import date

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QPushButton,
    QStackedWidget,
)
from PySide6.QtCore import QTimer, QDateTime

from ui.sidebar import Sidebar
from ui.theme import APP_STYLE
from core.database import Database

from modules.tasks.page import TasksPage
from modules.monitor.page import PCMonitorPage
from modules.notes.page import NotesPage
from modules.calendar.page import CalendarPage
from modules.ai.page import AIPage


class Dashboard(QWidget):

    def __init__(self, database, navigate):
        super().__init__()

        self.database = database
        self.navigate = navigate

        self.setObjectName("ContentArea")

        main = QVBoxLayout(self)
        main.setContentsMargins(35, 30, 35, 25)
        main.setSpacing(18)

        self.clock = QLabel()
        self.clock.setStyleSheet("""
            color: #A58BFF;
            font-size: 13px;
            font-weight: bold;
        """)

        title = QLabel("Welcome to NOVA.")
        title.setObjectName("PageTitle")

        subtitle = QLabel(
            "Your personal digital command center."
        )
        subtitle.setObjectName("MutedText")

        main.addWidget(self.clock)
        main.addWidget(title)
        main.addWidget(subtitle)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)
        self.update_clock()

        grid = QGridLayout()
        grid.setSpacing(14)

        self.total_value = self.create_stat_card(
            grid, 0, 0, "TOTAL TASKS"
        )

        self.completed_value = self.create_stat_card(
            grid, 0, 1, "COMPLETED"
        )

        self.pending_value = self.create_stat_card(
            grid, 0, 2, "PENDING"
        )

        self.overdue_value = self.create_stat_card(
            grid, 1, 0, "OVERDUE"
        )

        self.rate_value = self.create_stat_card(
            grid, 1, 1, "COMPLETION RATE"
        )

        grid.setColumnStretch(2, 1)
        main.addLayout(grid)

        recent_header = QHBoxLayout()

        recent_title = QLabel("RECENT TASKS")
        recent_title.setObjectName("CardTitle")

        view_all = QPushButton("View All →")
        view_all.setObjectName("QuickButton")
        view_all.clicked.connect(
            lambda: self.navigate("Tasks")
        )

        recent_header.addWidget(recent_title)
        recent_header.addStretch()
        recent_header.addWidget(view_all)

        main.addLayout(recent_header)

        self.recent_container = QFrame()
        self.recent_container.setObjectName(
            "DashboardCard"
        )

        self.recent_layout = QVBoxLayout(
            self.recent_container
        )

        self.recent_layout.setContentsMargins(
            18, 15, 18, 15
        )
        self.recent_layout.setSpacing(10)

        main.addWidget(self.recent_container)
        main.addStretch()

        self.refresh_stats()

    def create_stat_card(self, grid, row, column, heading):

        card = QFrame()
        card.setObjectName("DashboardCard")
        card.setMinimumHeight(105)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(17, 14, 17, 14)
        layout.setSpacing(8)

        title = QLabel(heading)
        title.setObjectName("CardTitle")

        value = QLabel("0")
        value.setObjectName("CardValue")

        layout.addWidget(title)
        layout.addWidget(value)
        layout.addStretch()

        grid.addWidget(card, row, column)

        return value

    def update_clock(self):

        now = QDateTime.currentDateTime()

        self.clock.setText(
            now.toString(
                "dddd, dd MMMM yyyy   •   hh:mm:ss AP"
            )
        )

    def refresh_stats(self):

        tasks = self.database.get_tasks()
        today = date.today()

        total = len(tasks)

        completed = sum(
            1 for task in tasks
            if task["completed"]
        )

        pending = total - completed

        overdue = sum(
            1 for task in tasks
            if not task["completed"]
            and task["due_date"] < today.isoformat()
        )

        completion_rate = (
            round((completed / total) * 100)
            if total > 0 else 0
        )

        self.total_value.setText(str(total))
        self.completed_value.setText(str(completed))
        self.pending_value.setText(str(pending))
        self.overdue_value.setText(str(overdue))
        self.rate_value.setText(
            f"{completion_rate}%"
        )

        self.refresh_recent_tasks(tasks)

    def refresh_recent_tasks(self, tasks):

        while self.recent_layout.count():

            item = self.recent_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        recent = sorted(
            tasks,
            key=lambda task: task.get("created_at") or "",
            reverse=True
        )[:5]

        if not recent:

            empty = QLabel(
                "No tasks yet. Create your first task!"
            )
            empty.setObjectName("MutedText")

            self.recent_layout.addWidget(empty)
            return

        for task in recent:

            row = QHBoxLayout()

            task_title = QLabel(task["title"])
            task_title.setStyleSheet(
                "color: #E8ECF5; font-size: 12px;"
            )

            status_text = (
                "Completed"
                if task["completed"]
                else task["priority"]
            )

            status = QLabel(status_text)
            status.setStyleSheet(
                "color: #A58BFF; font-size: 11px;"
            )

            row.addWidget(task_title)
            row.addStretch()
            row.addWidget(status)

            self.recent_layout.addLayout(row)

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_stats()


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "NOVA | Digital Command Center"
        )

        self.resize(1250, 780)
        self.setMinimumSize(950, 600)

        self.setStyleSheet(APP_STYLE)

        self.database = Database()

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = Sidebar()

        self.sidebar.page_changed.connect(
            self.change_page
        )

        main_layout.addWidget(self.sidebar)

        content = QFrame()
        content.setObjectName("ContentArea")

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()

        content_layout.addWidget(self.stack)
        main_layout.addWidget(content, 1)

        self.pages = {}

        # Dashboard
        self.dashboard = Dashboard(
            self.database,
            self.change_page
        )

        self.add_page(
            "Dashboard",
            self.dashboard
        )

        # Tasks
        self.tasks_page = TasksPage(
            self.database
        )

        self.add_page(
            "Tasks",
            self.tasks_page
        )

        # Calendar
        self.calendar_page = CalendarPage()

        self.add_page(
            "Calendar",
            self.calendar_page
        )

        # Notes
        self.notes_page = NotesPage()

        self.add_page(
            "Notes",
            self.notes_page
        )

        # PC Monitor
        self.monitor_page = PCMonitorPage()

        self.add_page(
            "PC Monitor",
            self.monitor_page
        )

        # NOVA AI - REAL MODULE
        self.ai_page = AIPage()

        self.add_page(
            "NOVA AI",
            self.ai_page
        )

        # Settings
        self.add_page(
            "Settings",
            self.create_placeholder("Settings")
        )

        self.change_page("Dashboard")

    def add_page(self, name, widget):

        self.pages[name] = widget
        self.stack.addWidget(widget)

    def create_placeholder(self, name):

        page = QWidget()

        layout = QVBoxLayout(page)
        layout.setContentsMargins(
            40, 40, 40, 40
        )
        layout.setSpacing(15)

        status = QLabel("MODULE INITIALIZED")

        status.setStyleSheet("""
            color: #A58BFF;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 2px;
        """)

        title = QLabel(name)
        title.setObjectName("PageTitle")

        subtitle = QLabel(
            f"The {name} module will be developed "
            "in an upcoming NOVA update."
        )

        subtitle.setObjectName("MutedText")

        layout.addWidget(status)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch()

        return page

    def change_page(self, page_name):

        if page_name not in self.pages:
            return

        self.stack.setCurrentWidget(
            self.pages[page_name]
        )

        self.sidebar.set_active(page_name)

        if page_name == "Dashboard":
            self.dashboard.refresh_stats()
