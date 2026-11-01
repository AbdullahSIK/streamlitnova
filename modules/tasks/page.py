
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QLineEdit, QComboBox,
    QDateEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QHeaderView
)

from PySide6.QtCore import Qt, QDate


class TasksPage(QWidget):

    def __init__(self, database):

        super().__init__()

        self.database = database
        self.editing_task_id = None

        self.setStyleSheet("""
            QLineEdit, QComboBox, QDateEdit {
                background-color: #111A2A;
                border: 1px solid #293751;
                border-radius: 7px;
                padding: 10px;
                color: #FFFFFF;
            }

            QTableWidget {
                background-color: #111A2A;
                border: 1px solid #243149;
                border-radius: 10px;
                gridline-color: #243149;
                selection-background-color: #30254D;
            }

            QHeaderView::section {
                background-color: #192237;
                color: #AFA3D8;
                border: none;
                padding: 12px;
                font-weight: bold;
            }

            QPushButton {
                background-color: #202B42;
                color: #FFFFFF;
                border: 1px solid #354363;
                border-radius: 7px;
                padding: 10px 15px;
            }

            QPushButton:hover {
                background-color: #30254D;
                border-color: #9675FF;
            }
        """)

        self.build_ui()
        self.refresh_tasks()

    def build_ui(self):

        main = QVBoxLayout(self)
        main.setContentsMargins(35, 30, 35, 30)
        main.setSpacing(18)

        # Heading
        heading = QLabel("Task Manager")
        heading.setObjectName("PageTitle")

        subtitle = QLabel(
            "Organize your work. Manage your priorities. "
            "Stay productive."
        )
        subtitle.setObjectName("MutedText")

        main.addWidget(heading)
        main.addWidget(subtitle)

        # Task creation card
        form_card = QFrame()
        form_card.setObjectName("DashboardCard")

        form = QVBoxLayout(form_card)
        form.setContentsMargins(20, 20, 20, 20)
        form.setSpacing(12)

        form_title = QLabel("CREATE / EDIT TASK")
        form_title.setObjectName("CardTitle")

        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText(
            "Enter your task name..."
        )

        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText(
            "Description (optional)..."
        )

        controls = QHBoxLayout()

        self.priority_input = QComboBox()
        self.priority_input.addItems([
            "Low", "Medium", "High"
        ])

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("dd MMM yyyy")
        self.date_input.setDate(QDate.currentDate())

        controls.addWidget(self.priority_input)
        controls.addWidget(self.date_input)

        self.save_button = QPushButton("＋  Add Task")
        self.save_button.clicked.connect(self.save_task)

        self.cancel_button = QPushButton("Cancel Edit")
        self.cancel_button.clicked.connect(self.cancel_edit)
        self.cancel_button.hide()

        buttons = QHBoxLayout()
        buttons.addWidget(self.save_button)
        buttons.addWidget(self.cancel_button)

        form.addWidget(form_title)
        form.addWidget(self.task_input)
        form.addWidget(self.description_input)
        form.addLayout(controls)
        form.addLayout(buttons)

        main.addWidget(form_card)

        # Task count
        self.count_label = QLabel("YOUR TASKS")
        self.count_label.setObjectName("CardTitle")

        main.addWidget(self.count_label)

        # Task table
        self.table = QTableWidget()
        self.table.setColumnCount(4)

        self.table.setHorizontalHeaderLabels([
            "TASK",
            "PRIORITY",
            "DUE DATE",
            "STATUS"
        ])

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )

        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(False)

        main.addWidget(self.table, 1)

        # Action buttons
        actions = QHBoxLayout()

        complete_button = QPushButton("✓  Complete / Undo")
        edit_button = QPushButton("✎  Edit Task")
        delete_button = QPushButton("⌫  Delete Task")

        complete_button.clicked.connect(self.toggle_task)
        edit_button.clicked.connect(self.edit_task)
        delete_button.clicked.connect(self.delete_task)

        actions.addWidget(complete_button)
        actions.addWidget(edit_button)
        actions.addWidget(delete_button)

        main.addLayout(actions)

    def save_task(self):

        title = self.task_input.text().strip()
        description = self.description_input.text().strip()

        if not title:

            QMessageBox.warning(
                self,
                "Missing task",
                "Please enter a task name."
            )
            return

        priority = self.priority_input.currentText()

        due_date = self.date_input.date().toString(
            Qt.DateFormat.ISODate
        )

        if self.editing_task_id is None:

            self.database.add_task(
                title, description, priority, due_date
            )

        else:

            self.database.update_task(
                self.editing_task_id,
                title,
                description,
                priority,
                due_date
            )

        self.cancel_edit()
        self.refresh_tasks()

    def refresh_tasks(self):

        tasks = self.database.get_tasks()

        self.table.setRowCount(len(tasks))

        for row, task in enumerate(tasks):

            title_item = QTableWidgetItem(task["title"])

            title_item.setData(
                Qt.ItemDataRole.UserRole,
                task["id"]
            )

            if task["completed"]:
                title_item.setForeground(
                    Qt.GlobalColor.gray
                )

            self.table.setItem(row, 0, title_item)

            self.table.setItem(
                row, 1,
                QTableWidgetItem(task["priority"])
            )

            self.table.setItem(
                row, 2,
                QTableWidgetItem(task["due_date"])
            )

            status = (
                "Completed" if task["completed"]
                else "Pending"
            )

            self.table.setItem(
                row, 3,
                QTableWidgetItem(status)
            )

        completed = sum(
            1 for task in tasks if task["completed"]
        )

        self.count_label.setText(
            f"YOUR TASKS  •  {len(tasks)} TOTAL  •  "
            f"{completed} COMPLETED"
        )

    def selected_task_id(self):

        row = self.table.currentRow()

        if row < 0:
            return None

        item = self.table.item(row, 0)

        if item is None:
            return None

        return item.data(Qt.ItemDataRole.UserRole)

    def edit_task(self):

        task_id = self.selected_task_id()

        if task_id is None:
            QMessageBox.information(
                self, "Select task",
                "Please select a task first."
            )
            return

        task = next(
            (t for t in self.database.get_tasks()
             if t["id"] == task_id),
            None
        )

        if task is None:
            return

        self.editing_task_id = task_id

        self.task_input.setText(task["title"])
        self.description_input.setText(task["description"])

        self.priority_input.setCurrentText(task["priority"])

        self.date_input.setDate(
            QDate.fromString(
                task["due_date"],
                Qt.DateFormat.ISODate
            )
        )

        self.save_button.setText("Save Changes")
        self.cancel_button.show()

    def cancel_edit(self):

        self.editing_task_id = None

        self.task_input.clear()
        self.description_input.clear()

        self.priority_input.setCurrentIndex(1)
        self.date_input.setDate(QDate.currentDate())

        self.save_button.setText("＋  Add Task")
        self.cancel_button.hide()

    def toggle_task(self):

        task_id = self.selected_task_id()

        if task_id is None:
            QMessageBox.information(
                self, "Select task",
                "Please select a task first."
            )
            return

        task = next(
            (t for t in self.database.get_tasks()
             if t["id"] == task_id),
            None
        )

        if task is None:
            return

        self.database.set_completed(
            task_id,
            not bool(task["completed"])
        )

        self.refresh_tasks()

    def delete_task(self):

        task_id = self.selected_task_id()

        if task_id is None:
            QMessageBox.information(
                self, "Select task",
                "Please select a task first."
            )
            return

        answer = QMessageBox.question(
            self,
            "Delete task",
            "Are you sure you want to delete this task?",
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No
        )

        if answer == QMessageBox.StandardButton.Yes:

            self.database.delete_task(task_id)
            self.cancel_edit()
            self.refresh_tasks()
