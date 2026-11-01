
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QFrame,
    QMessageBox,
    QCheckBox,
)


class NotesPage(QWidget):

    def __init__(self):
        super().__init__()

        from core.notes_database import NotesDatabase

        self.database = NotesDatabase()
        self.current_note_id = None

        self.setObjectName("NotesPage")

        # Complete Notes theme
        self.setStyleSheet("""
            QWidget#NotesPage {
                background-color: #000000;
                color: #39FF14;
            }

            QFrame {
                background-color: #000000;
                border: 1px solid #176B24;
                border-radius: 10px;
            }

            QLabel {
                background: transparent;
                color: #39FF14;
                border: none;
            }

            QLineEdit {
                background-color: #000000;
                color: #39FF14;
                border: 1px solid #176B24;
                border-radius: 7px;
                padding: 10px;
                font-size: 12px;
                selection-background-color: #176B24;
                selection-color: #FFFFFF;
            }

            QLineEdit:focus {
                border: 1px solid #39FF14;
            }

            QTextEdit {
                background-color: #000000;
                color: #39FF14;
                border: 1px solid #176B24;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                selection-background-color: #176B24;
                selection-color: #FFFFFF;
            }

            QTextEdit:focus {
                border: 1px solid #39FF14;
            }

            QPushButton {
                background-color: #000000;
                color: #39FF14;
                border: 1px solid #39FF14;
                border-radius: 7px;
                padding: 10px 16px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #39FF14;
                color: #000000;
                border: 1px solid #39FF14;
            }

            QPushButton:pressed {
                background-color: #176B24;
                color: #FFFFFF;
            }

            QPushButton:disabled {
                color: #416B46;
                border-color: #244229;
                background-color: #080808;
            }

            QListWidget {
                background-color: #000000;
                color: #39FF14;
                border: 1px solid #176B24;
                border-radius: 7px;
                padding: 5px;
                outline: none;
            }

            QListWidget::item {
                background-color: #000000;
                color: #39FF14;
                border: 1px solid transparent;
                border-radius: 5px;
                padding: 10px;
                margin: 2px;
            }

            QListWidget::item:hover {
                background-color: #102010;
                border: 1px solid #176B24;
            }

            QListWidget::item:selected {
                background-color: #176B24;
                color: #FFFFFF;
                border: 1px solid #39FF14;
            }

            QCheckBox {
                color: #39FF14;
                spacing: 8px;
                background: transparent;
            }

            QCheckBox::indicator {
                width: 17px;
                height: 17px;
                background-color: #000000;
                border: 1px solid #39FF14;
                border-radius: 3px;
            }

            QCheckBox::indicator:checked {
                background-color: #39FF14;
                border: 1px solid #39FF14;
            }

            QScrollBar:vertical {
                background-color: #000000;
                width: 9px;
                margin: 0;
            }

            QScrollBar::handle:vertical {
                background-color: #176B24;
                border-radius: 4px;
                min-height: 25px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #39FF14;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)

        main = QVBoxLayout(self)
        main.setContentsMargins(28, 25, 28, 25)
        main.setSpacing(15)

        # Header
        title = QLabel("NOVA Notes")
        title.setStyleSheet("""
            color: #39FF14;
            font-size: 26px;
            font-weight: bold;
            background: transparent;
        """)

        subtitle = QLabel(
            "Capture ideas, organize thoughts, and keep important notes."
        )
        subtitle.setStyleSheet("""
            color: #83C98B;
            font-size: 12px;
            background: transparent;
        """)

        main.addWidget(title)
        main.addWidget(subtitle)

        # Main layout
        content = QHBoxLayout()
        content.setSpacing(15)

        # Left notes panel
        left = QFrame()
        left.setObjectName("NotesPanel")
        left.setMinimumWidth(230)
        left.setMaximumWidth(310)

        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(13, 15, 13, 15)
        left_layout.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search notes...")
        self.search_input.textChanged.connect(
            self.refresh_notes
        )

        self.new_button = QPushButton("+ New Note")
        self.new_button.clicked.connect(self.new_note)

        self.notes_count = QLabel("0 notes")

        self.notes_list = QListWidget()
        self.notes_list.currentItemChanged.connect(
            self.select_note
        )

        left_layout.addWidget(self.search_input)
        left_layout.addWidget(self.new_button)
        left_layout.addWidget(self.notes_count)
        left_layout.addWidget(self.notes_list)

        # Right editor panel
        right = QFrame()
        right.setObjectName("EditorPanel")

        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(18, 18, 18, 18)
        right_layout.setSpacing(12)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Note title")
        self.title_input.setStyleSheet("""
            QLineEdit {
                background-color: #000000;
                color: #39FF14;
                border: 1px solid #39FF14;
                border-radius: 8px;
                font-size: 20px;
                font-weight: bold;
                padding: 12px;
            }
        """)

        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText(
            "Start writing your note here..."
        )

        self.content_input.setStyleSheet("""
            QTextEdit {
                background-color: #000000;
                color: #39FF14;
                border: 1px solid #39FF14;
                border-radius: 8px;
                font-size: 14px;
                padding: 12px;
                selection-background-color: #176B24;
                selection-color: #FFFFFF;
            }
        """)

        palette = self.content_input.palette()
        palette.setColor(
            QPalette.ColorRole.Base,
            QColor("#000000")
        )
        palette.setColor(
            QPalette.ColorRole.Text,
            QColor("#39FF14")
        )
        self.content_input.setPalette(palette)

        self.pin_checkbox = QCheckBox("Pin this note")

        buttons = QHBoxLayout()

        self.save_button = QPushButton("Save Note")
        self.save_button.clicked.connect(self.save_note)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_note)

        buttons.addWidget(self.pin_checkbox)
        buttons.addStretch()
        buttons.addWidget(self.delete_button)
        buttons.addWidget(self.save_button)

        self.timestamp_label = QLabel(
            "Create a new note or select an existing one."
        )
        self.timestamp_label.setStyleSheet(
            "color: #83C98B; background: transparent;"
        )

        right_layout.addWidget(self.title_input)
        right_layout.addWidget(self.content_input, 1)
        right_layout.addLayout(buttons)
        right_layout.addWidget(self.timestamp_label)

        content.addWidget(left, 1)
        content.addWidget(right, 3)

        main.addLayout(content, 1)

        self.refresh_notes()
        self.new_note()

    def refresh_notes(self):

        search = self.search_input.text()
        notes = self.database.get_notes(search)

        self.notes_list.blockSignals(True)
        self.notes_list.clear()

        for note in notes:

            pin = "📌 " if note["pinned"] else ""

            item = QListWidgetItem(
                f"{pin}{note['title']}"
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                note["id"]
            )

            item.setToolTip(
                note["content"][:200]
            )

            self.notes_list.addItem(item)

        self.notes_list.blockSignals(False)

        count = len(notes)

        self.notes_count.setText(
            f"{count} note{'s' if count != 1 else ''}"
        )

    def new_note(self):

        self.notes_list.blockSignals(True)
        self.notes_list.clearSelection()
        self.notes_list.setCurrentItem(None)
        self.notes_list.blockSignals(False)

        self.current_note_id = None

        self.title_input.clear()
        self.content_input.clear()
        self.pin_checkbox.setChecked(False)

        self.timestamp_label.setText(
            "New note • Not saved yet"
        )

        self.delete_button.setEnabled(False)
        self.title_input.setFocus()

    def select_note(self, current, previous):

        if current is None:
            return

        note_id = current.data(
            Qt.ItemDataRole.UserRole
        )

        note = self.database.get_note(note_id)

        if not note:
            self.refresh_notes()
            return

        self.current_note_id = note["id"]

        self.title_input.setText(note["title"])
        self.content_input.setPlainText(
            note["content"]
        )

        self.pin_checkbox.setChecked(
            bool(note["pinned"])
        )

        self.timestamp_label.setText(
            f"Created: {note['created_at']}   •   "
            f"Updated: {note['updated_at']}"
        )

        self.delete_button.setEnabled(True)

    def save_note(self):

        title = self.title_input.text().strip()
        content = self.content_input.toPlainText()
        pinned = self.pin_checkbox.isChecked()

        if not title and not content.strip():

            QMessageBox.warning(
                self,
                "Empty note",
                "Please enter a title or some content."
            )
            return

        if not title:
            title = "Untitled Note"
            self.title_input.setText(title)

        if self.current_note_id is None:

            self.current_note_id = self.database.add_note(
                title,
                content,
                pinned
            )

        else:

            self.database.update_note(
                self.current_note_id,
                title,
                content,
                pinned
            )

        self.refresh_notes()
        self.select_saved_note()

        QMessageBox.information(
            self,
            "Saved",
            "Your note has been saved successfully."
        )

    def select_saved_note(self):

        for index in range(self.notes_list.count()):

            item = self.notes_list.item(index)

            if item.data(
                Qt.ItemDataRole.UserRole
            ) == self.current_note_id:

                self.notes_list.setCurrentItem(item)
                return

    def delete_note(self):

        if self.current_note_id is None:
            return

        answer = QMessageBox.question(
            self,
            "Delete note",
            "Are you sure you want to delete this note?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self.database.delete_note(
            self.current_note_id
        )

        self.refresh_notes()
        self.new_note()
