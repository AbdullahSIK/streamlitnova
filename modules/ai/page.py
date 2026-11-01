
import re
import threading

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QScrollArea,
    QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont

from modules.ai.context_engine import ContextAwareNOVAEngine
from modules.ai.ollama_client import OllamaClient
from core.chat_database import ChatDatabase


SYSTEM_PROMPT = (
    "You are NOVA, a helpful personal desktop AI assistant. "
    "You run locally on the user's Windows PC. "
    "Be friendly, intelligent, clear, and concise. "
    "Help with programming, gaming, studies, productivity, "
    "technology, and everyday questions. "
    "Use simple explanations when appropriate. "
    "Never claim to have performed an action unless it "
    "was actually performed. "
    "You are chatting directly with the user. "
    "Do not invent messages from the user. "
    "Never write fake User messages or continue the conversation "
    "transcript. "
    "Do not prefix your replies with NOVA:, Assistant:, or other "
    "speaker labels. "
    "Respond only to the latest user message while using previous "
    "messages as context."
)


class OllamaWorker(QThread):
    token_received = Signal(str)

    def __init__(self, messages):
        super().__init__()

        self.messages = messages
        self.client = OllamaClient()
        self.stop_event = threading.Event()

    def request_stop(self):
        self.stop_event.set()

    def run(self):
        try:
            for token in self.client.stream_chat(
                self.messages,
                system_prompt=SYSTEM_PROMPT,
                stop_event=self.stop_event
            ):
                if self.stop_event.is_set():
                    break

                self.token_received.emit(token)

        except Exception as error:
            self.token_received.emit(
                f"\nSorry, something went wrong with the AI connection.\n"
                f"Details: {error}"
            )


class AIPage(QWidget):

    def __init__(self):
        super().__init__()

        # NOVA v1.4: Context-aware local engine
        self.engine = ContextAwareNOVAEngine()
        self.database = ChatDatabase()

        self.current_conversation_id = None
        self.current_conversation = []

        self.ai_worker = None
        self.current_response = ""
        self.streaming_message_label = None
        self.generation_stopped = False

        self.thinking_row = None
        self.thinking_label = None

        self.thinking_timer = QTimer(self)
        self.thinking_timer.timeout.connect(self.update_thinking)
        self.thinking_step = 0

        self.thinking_messages = [
            "Understanding your message",
            "Thinking through the answer",
            "Generating response",
            "Almost there",
            "Putting everything together",
        ]

        self.setup_ui()
        self.load_history()

    # --------------------------------------------------
    # CONTEXT MANAGEMENT
    # --------------------------------------------------

    def reset_context(self):
        """Clear remembered task context for a different conversation."""
        if hasattr(self.engine, "context"):
            self.engine.context.clear()

    def is_context_task_followup(self, message):
        """
        Route supported follow-up commands to the local context engine.
        Avoid routing ordinary AI messages containing words like 'it'
        or 'that' to the task manager.
        """
        command = " ".join(message.lower().strip().split())

        if not hasattr(self.engine, "context"):
            return False

        context = self.engine.context

        if not context.resolve_reference(command):
            return False

        patterns = (
            # Priority follow-ups
            r"^(?:make|set|change)\s+(?:it|that|this)"
            r"\s+(?:to\s+)?(?:high|medium|low)(?:\s+priority)?$",

            # Deadline follow-ups
            r"^(?:move|reschedule|change|update)\s+"
            r"(?:it|that|this)(?:\s+task)?\s+"
            r"(?:to|deadline\s+to|due\s+date\s+to)\s+.+$",

            # Complete or delete
            r"^(?:complete|finish|delete|remove)\s+"
            r"(?:it|that|this)(?:\s+task)?$",

            r"^mark\s+(?:it|that|this)(?:\s+task)?\s+"
            r"(?:as\s+)?(?:complete|completed|done)$",

            # Rename
            r"^(?:rename|retitle)\s+(?:it|that|this)"
            r"(?:\s+task)?\s+to\s+.+$",

            # Task status questions
            r"^(?:have\s+i\s+completed|have\s+i\s+finished)\s+"
            r"(?:it|that|this)(?:\s+task)?\??$",

            r"^(?:is|was)\s+(?:it|that|this)"
            r"(?:\s+task)?\s+(?:still\s+)?"
            r"(?:done|complete|completed|pending)\??$",

            r"^did\s+i\s+(?:finish|complete)"
            r"\s+(?:it|that|this)(?:\s+task)?\??$",

            r"^(?:what(?:'s| is)|tell me)\s+"
            r"(?:the\s+)?(?:status|priority|deadline|due date)"
            r"(?:\s+of)?\s+(?:it|that|this)\??$",
        )

        return any(
            re.fullmatch(pattern, command, re.IGNORECASE)
            for pattern in patterns
        )

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #090b14;
                color: #e8eaff;
                font-family: Segoe UI;
            }

            QLabel {
                background: transparent;
            }

            QPushButton {
                background-color: #171b2c;
                color: #dce0ff;
                border: 1px solid #292f49;
                border-radius: 8px;
                padding: 10px;
            }

            QPushButton:hover {
                background-color: #252b45;
                border: 1px solid #8065ff;
            }

            QLineEdit {
                background-color: #111525;
                color: white;
                border: 1px solid #303653;
                border-radius: 10px;
                padding: 13px;
            }

            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.history_panel = QFrame()
        self.history_panel.setFixedWidth(235)
        self.history_panel.setStyleSheet("""
            QFrame {
                background-color: #0d101c;
                border-right: 1px solid #20253a;
            }
        """)

        history_layout = QVBoxLayout(self.history_panel)
        history_layout.setContentsMargins(15, 20, 15, 15)
        history_layout.setSpacing(15)

        history_title = QLabel("NOVA AI")
        history_title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        history_title.setStyleSheet("color: #a58aff;")

        history_subtitle = QLabel("YOUR PERSONAL ASSISTANT")
        history_subtitle.setStyleSheet(
            "color: #69718f; font-size: 9px; letter-spacing: 2px;"
        )

        self.new_chat_button = QPushButton("+  New Chat")
        self.new_chat_button.clicked.connect(self.new_chat)

        history_label = QLabel("RECENT CHATS")
        history_label.setStyleSheet(
            "color: #737c9e; font-size: 10px; font-weight: bold;"
        )

        self.history_list = QVBoxLayout()
        self.history_list.setSpacing(7)

        history_layout.addWidget(history_title)
        history_layout.addWidget(history_subtitle)
        history_layout.addSpacing(15)
        history_layout.addWidget(self.new_chat_button)
        history_layout.addSpacing(15)
        history_layout.addWidget(history_label)
        history_layout.addLayout(self.history_list)
        history_layout.addStretch()

        version_label = QLabel("NOVA AI  •  v1.4.2")
        version_label.setStyleSheet("color: #555d78; font-size: 10px;")
        history_layout.addWidget(version_label)

        chat_area = QWidget()
        chat_layout = QVBoxLayout(chat_area)
        chat_layout.setContentsMargins(25, 20, 25, 20)
        chat_layout.setSpacing(15)

        header = QHBoxLayout()
        heading_layout = QVBoxLayout()

        self.chat_title = QLabel("NOVA Assistant")
        self.chat_title.setFont(QFont("Segoe UI", 20, QFont.Bold))

        self.status_label = QLabel("Local AI ready • Qwen 2.5")
        self.status_label.setStyleSheet(
            "color: #75dba5; font-size: 11px;"
        )

        heading_layout.addWidget(self.chat_title)
        heading_layout.addWidget(self.status_label)

        self.clear_button = QPushButton("Clear Chat")
        self.clear_button.clicked.connect(self.clear_chat)

        header.addLayout(heading_layout)
        header.addStretch()
        header.addWidget(self.clear_button)

        chat_layout.addLayout(header)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.message_container = QWidget()
        self.message_layout = QVBoxLayout(self.message_container)
        self.message_layout.setContentsMargins(10, 10, 10, 10)
        self.message_layout.setSpacing(15)
        self.message_layout.addStretch()

        self.scroll_area.setWidget(self.message_container)
        chat_layout.addWidget(self.scroll_area, 1)

        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background-color: #111525;
                border: 1px solid #292f49;
                border-radius: 12px;
            }
        """)

        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(10, 8, 10, 8)
        input_layout.setSpacing(8)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Ask NOVA anything...")
        self.message_input.returnPressed.connect(self.send_message)

        self.send_button = QPushButton("Send  ➤")
        self.send_button.setFixedWidth(100)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #7657e8;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 12px;
            }

            QPushButton:hover {
                background-color: #9278ff;
            }
        """)
        self.send_button.clicked.connect(self.send_message)

        self.stop_button = QPushButton("Stop  ■")
        self.stop_button.setFixedWidth(100)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #a33c55;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 12px;
            }

            QPushButton:hover {
                background-color: #c54b68;
            }
        """)
        self.stop_button.clicked.connect(self.stop_generation)
        self.stop_button.hide()

        input_layout.addWidget(self.message_input, 1)
        input_layout.addWidget(self.send_button)
        input_layout.addWidget(self.stop_button)

        chat_layout.addWidget(input_frame)

        main_layout.addWidget(self.history_panel)
        main_layout.addWidget(chat_area, 1)

        self.show_welcome_message()

    # --------------------------------------------------
    # WELCOME
    # --------------------------------------------------

    def show_welcome_message(self):
        self.chat_title.setText("NOVA Assistant")

        self.add_message(
            "AI",
            "Hello! I'm NOVA.\n\n"
            "My local AI model is connected and ready!\n\n"
            "I can have conversations, explain topics, help with "
            "coding, and manage your tasks, notes, calendar and "
            "PC information.\n\n"
            "I can also understand follow-up requests, such as:\n"
            "• Remind me to study Chemistry tomorrow\n"
            "• Make it high priority\n"
            "• Move that to Friday\n"
            "• Have I completed it?\n"
            "• Rename it to Chemistry Revision\n\n"
            "Type 'help' to see what I can do."
        )

    # --------------------------------------------------
    # MESSAGE DISPLAY
    # --------------------------------------------------

    def scroll_to_bottom(self):
        QTimer.singleShot(
            50,
            lambda: self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().maximum()
            )
        )

    def add_message(self, sender, message):
        bubble = QFrame()
        bubble.setMaximumWidth(650)

        if sender == "You":
            bubble.setStyleSheet("""
                QFrame {
                    background-color: #292044;
                    border: 1px solid #59449a;
                    border-radius: 12px;
                }
            """)
        else:
            bubble.setStyleSheet("""
                QFrame {
                    background-color: #151b2c;
                    border: 1px solid #29344d;
                    border-radius: 12px;
                }
            """)

        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(15, 10, 15, 10)
        bubble_layout.setSpacing(6)

        sender_label = QLabel(sender)
        sender_label.setStyleSheet(
            "color: #a58aff; font-size: 10px; font-weight: bold;"
        )

        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setTextFormat(Qt.TextFormat.PlainText)
        message_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        message_label.setStyleSheet(
            "color: #e8eaff; font-size: 13px;"
        )

        bubble_layout.addWidget(sender_label)
        bubble_layout.addWidget(message_label)

        row = QHBoxLayout()

        if sender == "You":
            row.addStretch()
            row.addWidget(bubble)
        else:
            row.addWidget(bubble)
            row.addStretch()

        self.message_layout.insertLayout(
            self.message_layout.count() - 1, row
        )

        self.scroll_to_bottom()

    # --------------------------------------------------
    # STREAMING
    # --------------------------------------------------

    def create_streaming_message(self):
        bubble = QFrame()
        bubble.setMaximumWidth(650)
        bubble.setStyleSheet("""
            QFrame {
                background-color: #151b2c;
                border: 1px solid #59449a;
                border-radius: 12px;
            }
        """)

        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(15, 10, 15, 10)
        bubble_layout.setSpacing(6)

        sender_label = QLabel("NOVA")
        sender_label.setStyleSheet(
            "color: #a58aff; font-size: 10px; font-weight: bold;"
        )

        self.streaming_message_label = QLabel("")
        self.streaming_message_label.setWordWrap(True)
        self.streaming_message_label.setTextFormat(
            Qt.TextFormat.PlainText
        )
        self.streaming_message_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.streaming_message_label.setStyleSheet(
            "color: #e8eaff; font-size: 13px;"
        )

        bubble_layout.addWidget(sender_label)
        bubble_layout.addWidget(self.streaming_message_label)

        row = QHBoxLayout()
        row.addWidget(bubble)
        row.addStretch()

        self.message_layout.insertLayout(
            self.message_layout.count() - 1, row
        )

    def handle_stream_token(self, token):
        if self.streaming_message_label is None:
            self.remove_thinking()
            self.create_streaming_message()

        self.current_response += token
        self.streaming_message_label.setText(self.current_response)

        self.scroll_to_bottom()

    # --------------------------------------------------
    # THINKING INDICATOR
    # --------------------------------------------------

    def show_thinking(self):
        self.thinking_step = 0
        self.thinking_row = QHBoxLayout()

        bubble = QFrame()
        bubble.setMaximumWidth(650)
        bubble.setStyleSheet("""
            QFrame {
                background-color: #151b2c;
                border: 1px solid #59449a;
                border-radius: 12px;
            }
        """)

        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(15, 12, 15, 12)
        bubble_layout.setSpacing(8)

        sender_label = QLabel("NOVA")
        sender_label.setStyleSheet(
            "color: #a58aff; font-size: 10px; font-weight: bold;"
        )

        self.thinking_label = QLabel("Understanding your message...")
        self.thinking_label.setStyleSheet(
            "color: #c5c8e0; font-size: 13px;"
        )
        self.thinking_label.setWordWrap(True)

        bubble_layout.addWidget(sender_label)
        bubble_layout.addWidget(self.thinking_label)

        self.thinking_row.addWidget(bubble)
        self.thinking_row.addStretch()

        self.message_layout.insertLayout(
            self.message_layout.count() - 1,
            self.thinking_row
        )

        self.thinking_timer.start(1400)
        self.scroll_to_bottom()

    def update_thinking(self):
        if self.thinking_label is None:
            return

        message = self.thinking_messages[
            self.thinking_step % len(self.thinking_messages)
        ]

        dots = "." * ((self.thinking_step % 3) + 1)
        self.thinking_label.setText(message + dots)

        self.thinking_step += 1

    def remove_thinking(self):
        self.thinking_timer.stop()

        if self.thinking_row is not None:
            while self.thinking_row.count():
                item = self.thinking_row.takeAt(0)

                widget = item.widget()
                if widget:
                    widget.deleteLater()

            self.message_layout.removeItem(self.thinking_row)
            self.thinking_row = None

        self.thinking_label = None

    # --------------------------------------------------
    # DATABASE AND HISTORY
    # --------------------------------------------------

    def ensure_conversation(self, first_message):
        if self.current_conversation_id is not None:
            return

        title = first_message.strip().replace("\n", " ")

        if len(title) > 30:
            title = title[:30].rstrip() + "..."

        self.current_conversation_id = (
            self.database.create_conversation(title)
        )

        self.chat_title.setText(title)

    def save_message(self, sender, content):
        if self.current_conversation_id is None:
            return

        self.database.save_message(
            self.current_conversation_id,
            sender,
            content
        )

    def load_history(self):
        while self.history_list.count():
            item = self.history_list.takeAt(0)

            if item.widget():
                item.widget().deleteLater()

            if item.layout():
                self.clear_layout(item.layout())

        conversations = self.database.get_conversations()

        for chat_id, title, created_at, updated_at in conversations:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(4)

            open_button = QPushButton(title)
            open_button.setToolTip(title)
            open_button.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    background-color: #171b2c;
                    color: #dce0ff;
                    border: 1px solid #292f49;
                    border-radius: 7px;
                    padding: 9px;
                }

                QPushButton:hover {
                    background-color: #252b45;
                    border: 1px solid #8065ff;
                }
            """)

            open_button.clicked.connect(
                lambda checked=False, cid=chat_id:
                self.open_conversation(cid)
            )

            delete_button = QPushButton("×")
            delete_button.setFixedWidth(32)
            delete_button.setToolTip("Delete this conversation")
            delete_button.setStyleSheet("""
                QPushButton {
                    background-color: #211522;
                    color: #e58a9c;
                    border: 1px solid #462536;
                    border-radius: 7px;
                    padding: 7px;
                    font-weight: bold;
                }

                QPushButton:hover {
                    background-color: #542538;
                }
            """)

            delete_button.clicked.connect(
                lambda checked=False, cid=chat_id:
                self.delete_conversation(cid)
            )

            row_layout.addWidget(open_button, 1)
            row_layout.addWidget(delete_button)

            self.history_list.addWidget(row_widget)

    def open_conversation(self, conversation_id):
        if self.ai_worker is not None:
            return

        # Context is isolated between conversations.
        self.reset_context()

        messages = self.database.get_messages(conversation_id)

        self.current_conversation_id = conversation_id
        self.current_conversation = list(messages)

        self.clear_messages()

        conversations = self.database.get_conversations()
        title = "NOVA Assistant"

        for chat_id, chat_title, created_at, updated_at in conversations:
            if chat_id == conversation_id:
                title = chat_title
                break

        self.chat_title.setText(title)

        for sender, content in messages:
            self.add_message(sender, content)

        self.status_label.setText(
            "Conversation loaded • Local storage"
        )
        self.status_label.setStyleSheet(
            "color: #75dba5; font-size: 11px;"
        )

        self.message_input.setFocus()

    def delete_conversation(self, conversation_id):
        answer = QMessageBox.question(
            self,
            "Delete Conversation",
            "Are you sure you want to permanently delete this conversation?",
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self.database.delete_conversation(conversation_id)

        if self.current_conversation_id == conversation_id:
            self.current_conversation_id = None
            self.current_conversation.clear()
            self.reset_context()
            self.clear_messages()
            self.show_welcome_message()

        self.load_history()

    # --------------------------------------------------
    # LOCAL COMMAND DETECTION
    # --------------------------------------------------

    def is_local_task_management(self, command):
        patterns = (
            r"^(?:mark\s+.+\s+(?:as\s+)?(?:completed|complete|done)|"
            r"complete\s+(?:my\s+)?(?:task\s+)?(?:called\s+)?\S.*)$",

            r"^(?:delete|remove)\s+(?:my\s+)?(?:task\s+)?\S.*$",

            r"^(?:make|set|change)\s+.+\s+(?:task\s+)?"
            r"(?:to\s+)?(?:high|medium|low)(?:\s+priority)?$",

            r"^(?:change|move|update|reschedule)\s+.+\s+"
            r"(?:task\s+)?(?:deadline|due date)\s+to\s+.+$",

            r"^(?:move|reschedule)\s+.+\s+to\s+.+$",

            r"^(?:rename|retitle)\s+.+\s+to\s+.+$",
        )

        return any(
            re.fullmatch(pattern, command, re.IGNORECASE)
            for pattern in patterns
        )

    def is_universal_local_query(self, command):
        """
        Detect natural-language requests for NOVA's local data.
        This allows different phrasings to reach the local engine.
        """

        task_terms = (
            "task", "tasks", "to-do", "todo"
        )

        task_intents = (
            "show", "list", "what", "which", "tell",
            "find", "search", "today", "tomorrow",
            "overdue", "pending", "completed", "complete",
            "unfinished", "priority", "deadline", "due",
            "work on", "next", "remaining", "have i",
            "did i", "is it", "are my"
        )

        if (
            any(term in command for term in task_terms)
            and any(intent in command for intent in task_intents)
        ):
            return True

        if (
            "what should i work on next" in command
            or "what should i do next" in command
            or "what do i need to finish" in command
        ):
            return True

        note_terms = ("note", "notes")
        note_intents = (
            "show", "list", "find", "search", "look",
            "what", "which", "tell", "read", "open"
        )

        if (
            any(term in command for term in note_terms)
            and any(intent in command for intent in note_intents)
        ):
            return True

        calendar_terms = (
            "calendar", "event", "events", "appointment",
            "appointments"
        )

        calendar_intents = (
            "show", "list", "what", "which", "tell",
            "upcoming", "tomorrow", "today", "next",
            "coming", "scheduled", "have i"
        )

        if (
            any(term in command for term in calendar_terms)
            and any(intent in command for intent in calendar_intents)
        ):
            return True

        pc_terms = (
            "pc", "computer", "system", "cpu", "gpu",
            "graphics card", "processor", "ram",
            "memory usage", "disk usage", "performance"
        )

        pc_intents = (
            "status", "check", "show", "tell", "how",
            "usage", "temperature", "performance",
            "doing", "performing", "report"
        )

        if (
            any(term in command for term in pc_terms)
            and any(intent in command for intent in pc_intents)
        ):
            return True

        return False

    def is_local_command(self, message):
        command = " ".join(message.lower().strip().split())

        exact_commands = {
            "help",
            "commands",
            "what can you do?",
            "hello",
            "hi",
            "hey",

            "list tasks",
            "show tasks",
            "my tasks",
            "show my tasks",
            "what are my tasks",
            "what tasks do i have",
            "what do i have to do",
            "what do i have to do today",
            "what's on my task list",
            "whats on my task list",

            "upcoming events",
            "show events",
            "my events",
            "show my events",
            "what events are coming up",
            "what's on my calendar",
            "whats on my calendar",
            "show my calendar",

            "list notes",
            "show notes",
            "my notes",
            "show my notes",
            "what notes do i have",

            "system status",
            "pc status",
            "how is my pc doing",
            "how is my pc performing",
            "check my pc",
            "system performance",
        }

        if command in exact_commands:
            return True

        if self.is_context_task_followup(command):
            return True

        if self.is_universal_local_query(command):
            return True

        if self.is_local_task_management(command):
            return True

        command_prefixes = (
            "search notes |",
            "add task |",
            "complete task |",
            "delete task |",
            "add note |",
            "add event |",

            "remind me to ",
            "remind me ",
            "add a task to ",
            "add task to ",
            "create a task to ",
            "create task to ",
            "make a task to ",

            "i need to ",
            "i have to ",
            "i want to ",
            "i must ",
            "need to ",
            "have to ",
            "finish ",
            "complete ",
            "study ",
            "prepare for ",
            "revise ",
            "submit ",
            "do my ",
            "clean ",
            "organise ",
            "organize ",
        )

        if command.startswith(command_prefixes):
            return True

        return False

    # --------------------------------------------------
    # AI CONVERSATION CONTEXT
    # --------------------------------------------------

    def build_ai_prompt(self):
        messages = []

        for sender, content in self.current_conversation[-12:]:
            if sender == "You":
                role = "user"
            elif sender == "AI":
                role = "assistant"
            else:
                continue

            messages.append({
                "role": role,
                "content": content
            })

        return messages

    # --------------------------------------------------
    # SEND MESSAGE
    # --------------------------------------------------

    def send_message(self):
        message = self.message_input.text().strip()

        if not message or self.ai_worker is not None:
            return

        self.message_input.clear()
        self.send_button.setEnabled(False)

        self.add_message("You", message)
        self.current_conversation.append(("You", message))

        self.ensure_conversation(message)
        self.save_message("You", message)
        self.load_history()

        if self.is_local_command(message):
            self.status_label.setText("Running NOVA local intelligence...")
            self.status_label.setStyleSheet(
                "color: #75dba5; font-size: 11px;"
            )

            try:
                response = self.engine.process(message)
            except Exception as error:
                response = (
                    "Something went wrong while processing your command.\n"
                    f"Error: {error}"
                )

            response = str(response)

            self.add_message("AI", response)
            self.current_conversation.append(("AI", response))
            self.save_message("AI", response)

            self.status_label.setText("Local AI ready • Qwen 2.5")
            self.send_button.setEnabled(True)
            self.message_input.setFocus()
            self.load_history()
            return

        self.current_response = ""
        self.streaming_message_label = None
        self.generation_stopped = False

        self.status_label.setText("NOVA is thinking...")
        self.status_label.setStyleSheet(
            "color: #a58aff; font-size: 11px;"
        )

        self.show_thinking()
        self.stop_button.show()

        messages = self.build_ai_prompt()

        self.ai_worker = OllamaWorker(messages)

        self.ai_worker.token_received.connect(
            self.handle_stream_token
        )

        self.ai_worker.finished.connect(
            self.ai_worker_finished
        )

        self.ai_worker.start()

    # --------------------------------------------------
    # STOP GENERATION
    # --------------------------------------------------

    def stop_generation(self):
        if self.ai_worker is None:
            return

        self.generation_stopped = True
        self.ai_worker.request_stop()

        self.status_label.setText(
            "Stopping after the current response chunk..."
        )
        self.status_label.setStyleSheet(
            "color: #e9a45c; font-size: 11px;"
        )

        self.stop_button.setEnabled(False)

    # --------------------------------------------------
    # GENERATION FINISHED
    # --------------------------------------------------

    def ai_worker_finished(self):
        self.remove_thinking()

        if self.current_response:
            if self.generation_stopped:
                self.current_response += "\n\n[Generation stopped]"

                if self.streaming_message_label is not None:
                    self.streaming_message_label.setText(
                        self.current_response
                    )

            self.current_conversation.append(
                ("AI", self.current_response)
            )

            self.save_message("AI", self.current_response)

        elif self.generation_stopped:
            stopped_message = "Generation stopped."

            self.add_message("AI", stopped_message)
            self.current_conversation.append(
                ("AI", stopped_message)
            )
            self.save_message("AI", stopped_message)

        self.ai_worker = None
        self.streaming_message_label = None

        self.stop_button.hide()
        self.stop_button.setEnabled(True)

        self.status_label.setText("Local AI ready • Qwen 2.5")
        self.status_label.setStyleSheet(
            "color: #75dba5; font-size: 11px;"
        )

        self.send_button.setEnabled(True)
        self.message_input.setFocus()

        self.load_history()

    # --------------------------------------------------
    # CHAT MANAGEMENT
    # --------------------------------------------------

    def new_chat(self):
        if self.ai_worker is not None:
            return

        self.current_conversation_id = None
        self.current_conversation.clear()
        self.reset_context()

        self.clear_messages()
        self.show_welcome_message()

        self.status_label.setText(
            "New conversation • Local AI ready"
        )
        self.status_label.setStyleSheet(
            "color: #75dba5; font-size: 11px;"
        )

    def clear_chat(self):
        if self.ai_worker is not None:
            return

        if self.current_conversation_id is not None:
            answer = QMessageBox.question(
                self,
                "Clear Chat",
                "This will permanently delete the current conversation. Continue?",
                QMessageBox.StandardButton.Yes |
                QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if answer != QMessageBox.StandardButton.Yes:
                return

            self.database.delete_conversation(
                self.current_conversation_id
            )

        self.current_conversation_id = None
        self.current_conversation.clear()
        self.reset_context()

        self.clear_messages()
        self.show_welcome_message()
        self.load_history()

    def clear_messages(self):
        self.remove_thinking()
        self.streaming_message_label = None

        while self.message_layout.count() > 0:
            item = self.message_layout.takeAt(0)

            if item.layout():
                self.clear_layout(item.layout())

            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.message_layout.addStretch()

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)

            if item.layout():
                self.clear_layout(item.layout())

            widget = item.widget()
            if widget:
                widget.deleteLater()
