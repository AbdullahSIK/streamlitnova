
import re
from datetime import datetime, timedelta

from modules.ai.engine import NOVAEngine
from modules.ai.intent_router import IntentRouter


class UniversalNOVAEngine(NOVAEngine):

    def __init__(self):
        super().__init__()

        self.router = IntentRouter()

        # Extend calendar understanding without changing
        # the original intent router.
        self.router.patterns["calendar.today"].extend([
            r"\bwhat'?s\s+happening\s+today\b",
            r"\bwhat\s+is\s+happening\s+today\b",
            r"\banything\s+planned\s+for\s+today\b",
        ])

        self.router.patterns["calendar.upcoming"].extend([
            r"\bwhat'?s\s+happening\s+tomorrow\b",
            r"\bwhat\s+is\s+happening\s+tomorrow\b",
            r"\banything\s+planned\s+for\s+tomorrow\b",
            r"\bwhat\s+do\s+i\s+have\s+tomorrow\b",
            r"\bwhat'?s\s+planned\s+for\s+tomorrow\b",
        ])

        self.router.patterns["tasks.list"].extend([
            r"\bcan\s+you\s+tell\s+me\s+my\s+tasks\b",
            r"\bshow\s+me\s+everything\s+i\s+need\s+to\s+do\b",
        ])

    # --------------------------------------------------
    # MAIN UNIVERSAL PROCESSOR
    # --------------------------------------------------

    def process(self, message):

        message = message.strip()

        if not message:
            return "Please enter a message."

        command = re.sub(
            r"\s+",
            " ",
            message.lower().strip()
        )

        # Keep greetings and help local.
        if command in (
            "hello",
            "hi",
            "hey",
            "help",
            "commands",
            "what can you do?"
        ):
            return super().process(message)

        # Keep exact pipe commands compatible.
        exact_prefixes = (
            "search notes |",
            "add task |",
            "complete task |",
            "delete task |",
            "add note |",
            "add event |",
        )

        if command.startswith(exact_prefixes):
            return super().process(message)

        # Identify the user's intention.
        intent = self.router.classify(message)

        # If we don't understand the request, try the
        # existing engine before sending it to Ollama.
        if intent is None:
            return self.process_legacy(message)

        # --------------------------------------------------
        # TASKS
        # --------------------------------------------------

        if intent == "tasks.today":
            return self.today_tasks()

        if intent == "tasks.overdue":
            return self.overdue_tasks()

        if intent == "tasks.next":
            return self.suggest_next_task()

        if intent == "tasks.list":
            return self.list_tasks()

        if intent in (
            "tasks.complete",
            "tasks.delete",
            "tasks.update",
            "tasks.create"
        ):
            return self.process_legacy(message)

        # --------------------------------------------------
        # NOTES
        # --------------------------------------------------

        if intent == "notes.list":
            return self.list_notes()

        if intent == "notes.search":
            keyword = self.extract_note_keyword(message)

            if not keyword:
                return (
                    "What would you like me to search for "
                    "in your notes?"
                )

            return self.search_notes(keyword)

        if intent == "notes.create":
            return self.process_legacy(message)

        # --------------------------------------------------
        # CALENDAR
        # --------------------------------------------------

        if intent == "calendar.today":
            return self.events_for_date(
                datetime.now().date()
            )

        if intent == "calendar.upcoming":
            if re.search(r"\btomorrow\b", command):
                target_date = (
                    datetime.now().date()
                    + timedelta(days=1)
                )

                return self.events_for_date(target_date)

            return self.upcoming_events()

        if intent == "calendar.list":
            return self.upcoming_events()

        if intent == "calendar.create":
            return self.process_legacy(message)

        # --------------------------------------------------
        # PC MONITOR
        # --------------------------------------------------

        if intent in (
            "pc.cpu",
            "pc.ram",
            "pc.gpu",
            "pc.status"
        ):
            return self.system_status()

        return None

    # --------------------------------------------------
    # LEGACY ENGINE COMPATIBILITY
    # --------------------------------------------------

    def process_legacy(self, message):

        response = super().process(message)

        if response is None:
            return None

        # The original engine returns this message for
        # unsupported commands. Convert it to None so
        # the chat page can use Ollama.
        if str(response).startswith(
            "I don't recognise that request yet."
        ):
            return None

        return response

    # --------------------------------------------------
    # NOTE SEARCH
    # --------------------------------------------------

    def extract_note_keyword(self, message):

        text = message.strip()

        patterns = [
            r"\b(?:find|search|look\s+for|locate)"
            r"\s+(?:my\s+)?(?:notes?\s+)?"
            r"(?:about|on|containing)\s+(.+)",

            r"\bwhat\s+did\s+i\s+write\s+about\s+(.+)",

            r"\b(?:find|search|look\s+for|locate)"
            r"\s+(?:my\s+)?(.+?)\s+notes?\b",
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE
            )

            if match:
                keyword = match.group(1).strip()
                return keyword.strip(" .,!?:;")

        return None

    # --------------------------------------------------
    # CALENDAR DATE FILTER
    # --------------------------------------------------

    def events_for_date(self, target_date):

        events = self.calendar_db.get_upcoming_events(100)

        matching_events = []

        for event in events:
            try:
                event_date = datetime.strptime(
                    str(event["event_date"]),
                    "%Y-%m-%d"
                ).date()
            except (ValueError, TypeError, KeyError):
                continue

            if event_date == target_date:
                matching_events.append(event)

        if not matching_events:
            return (
                f"CALENDAR — {target_date.strftime('%d %B %Y')}\n\n"
                "You don't have any events scheduled for this date."
            )

        lines = [
            f"CALENDAR — {target_date.strftime('%d %B %Y')}",
            "",
            f"Events: {len(matching_events)}",
            ""
        ]

        for event in matching_events:
            event_time = event.get("event_time") or "No time set"

            lines.append(
                f"#{event['id']} - {event['title']}\n"
                f"   Time: {event_time}"
            )

            description = event.get("description", "")

            if description:
                lines.append(
                    f"   Description: {description}"
                )

            lines.append("")

        return "\n".join(lines).strip()
