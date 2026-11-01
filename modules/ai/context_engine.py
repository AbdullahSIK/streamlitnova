
import re

from modules.ai.engine import NOVAEngine
from modules.ai.context_manager import ConversationContext


class ContextAwareNOVAEngine(NOVAEngine):

    def __init__(self):
        super().__init__()
        self.context = ConversationContext()

    # --------------------------------------------------
    # MAIN PROCESSOR
    # --------------------------------------------------

    def process(self, message):
        message = message.strip()

        if not message:
            return super().process(message)

        entity = self.context.resolve_reference(message)

        if entity and entity.get("type") == "task":
            response = self.handle_task_followup(message, entity)

            if response is not None:
                return response

        old_task_ids = {
            task["id"] for task in self.tasks_db.get_tasks()
        }

        self.remember_named_task(message)

        response = super().process(message)

        self.remember_new_task(old_task_ids)
        self.remember_recommended_task(message, response)

        return response

    # --------------------------------------------------
    # FOLLOW-UP UNDERSTANDING
    # --------------------------------------------------

    def handle_task_followup(self, message, entity):
        task_id = entity.get("id")

        if task_id is None:
            return None

        task = self.get_task_by_id(task_id)

        if task is None:
            self.context.clear()
            return (
                "The task we were discussing no longer exists.\n\n"
                "Please show your tasks and choose another one."
            )

        text = message.strip()
        lowered = text.lower()
        task_name = task["title"]

        # TASK STATUS

        status_patterns = [
            r"have i completed (?:it|that|this)\??",
            r"is (?:it|that|this)(?: task)? (?:done|completed)\??",
            r"is (?:it|that|this)(?: task)? (?:still )?pending\??",
            r"did i (?:finish|complete) (?:it|that|this)\??",
            r"what is the status of (?:it|that|this)\??",
            r"what's the status of (?:it|that|this)\??",
            r"whats the status of (?:it|that|this)\??",
            r"has (?:it|that|this) been completed\??",
            r"is (?:it|that|this) finished\??",
            r"have i done (?:it|that|this)\??",
        ]

        if any(
            re.fullmatch(pattern, lowered)
            for pattern in status_patterns
        ):
            return self.get_task_status(task)

        # CHANGE PRIORITY

        match = re.search(
            r"\b(high|medium|low)\s+priority\b",
            lowered
        )

        if match and re.search(
            r"\b(make|set|change|mark|actually)\b",
            lowered
        ):
            return self.change_task_priority(
                task_name,
                match.group(1).capitalize()
            )

        match = re.fullmatch(
            r"(?:make|set|change)\s+"
            r"(?:it|that|this)\s+(?:to\s+)?"
            r"(high|medium|low)",
            text,
            flags=re.IGNORECASE
        )

        if match:
            return self.change_task_priority(
                task_name,
                match.group(1).capitalize()
            )

        # CHANGE DEADLINE

        match = re.fullmatch(
            r"(?:move|reschedule|shift)\s+"
            r"(?:it|that|this)\s+to\s+(.+)",
            text,
            flags=re.IGNORECASE
        )

        if match:
            return self.change_task_deadline(
                task_name,
                match.group(1)
            )

        match = re.fullmatch(
            r"(?:change|update|move|reschedule)\s+"
            r"(?:its|the)\s+"
            r"(?:deadline|due date)\s+to\s+(.+)",
            text,
            flags=re.IGNORECASE
        )

        if match:
            return self.change_task_deadline(
                task_name,
                match.group(1)
            )

        # COMPLETE TASK

        if re.fullmatch(
            r"(?:complete|finish)\s+"
            r"(?:it|that|this)(?:\s+task)?",
            text,
            flags=re.IGNORECASE
        ):
            return self.complete_task_by_id(task)

        if re.fullmatch(
            r"mark\s+(?:it|that|this)\s+"
            r"(?:as\s+)?(?:done|complete|completed)",
            text,
            flags=re.IGNORECASE
        ):
            return self.complete_task_by_id(task)

        # DELETE TASK

        if re.fullmatch(
            r"(?:delete|remove)\s+"
            r"(?:it|that|this)(?:\s+task)?",
            text,
            flags=re.IGNORECASE
        ):
            return self.delete_task_by_id(task)

        # RENAME TASK

        match = re.fullmatch(
            r"(?:rename|retitle)\s+"
            r"(?:it|that|this)\s+to\s+(.+)",
            text,
            flags=re.IGNORECASE
        )

        if match:
            return self.rename_task_by_id(
                task,
                match.group(1)
            )

        return None

    # --------------------------------------------------
    # TASK STATUS
    # --------------------------------------------------

    def get_task_status(self, task):
        if task["completed"]:
            status = "COMPLETED"
            explanation = "You've already finished this task. Great work!"
        else:
            status = "PENDING"
            explanation = "You haven't marked this task as completed yet."

        return (
            "TASK STATUS\n\n"
            f"Task: {task['title']}\n"
            f"ID: #{task['id']}\n"
            f"Status: {status}\n"
            f"Priority: {task['priority']}\n"
            f"Due date: {task['due_date']}\n\n"
            f"{explanation}"
        )

    # --------------------------------------------------
    # TASK ID OPERATIONS
    # --------------------------------------------------

    def get_task_by_id(self, task_id):
        for task in self.tasks_db.get_tasks():
            if task["id"] == task_id:
                return task
        return None

    def complete_task_by_id(self, task):
        if task["completed"]:
            return f"'{task['title']}' is already completed."

        self.tasks_db.set_completed(task["id"], True)

        return (
            "Task marked as completed!\n\n"
            f"Task: {task['title']}\n"
            f"ID: #{task['id']}"
        )

    def delete_task_by_id(self, task):
        self.tasks_db.delete_task(task["id"])
        self.context.clear()

        return (
            "Task deleted successfully.\n\n"
            f"Task: {task['title']}\n"
            f"ID: #{task['id']}"
        )

    def rename_task_by_id(self, task, new_name):
        new_name = new_name.strip().strip(" .,!?:;-")

        if not new_name:
            return "The new task name cannot be empty."

        if len(new_name) > 200:
            return "Please use a shorter task name."

        self.tasks_db.update_task(
            task["id"],
            new_name,
            task["description"],
            task["priority"],
            task["due_date"]
        )

        self.context.remember(
            "task",
            task["id"],
            new_name,
            intent="rename_task"
        )

        return (
            "Task renamed successfully!\n\n"
            f"Old name: {task['title']}\n"
            f"New name: {new_name}"
        )

    # --------------------------------------------------
    # CONTEXT TRACKING
    # --------------------------------------------------

    def remember_named_task(self, message):
        patterns = [
            r"(?:make|set|change)\s+(?:my\s+)?(.+?)\s+"
            r"(?:task\s+)?(?:to\s+)?(?:high|medium|low)",
            r"(?:delete|remove)\s+(?:my\s+)?"
            r"(?:task\s+)?(?:called\s+)?(.+)",
            r"(?:rename|retitle)\s+(?:my\s+)?"
            r"(.+?)\s+to\s+(.+)",
            r"(?:complete|finish)\s+(?:my\s+)?"
            r"(?:task\s+)?(?:called\s+)?(.+)",
            r"(?:mark|set)\s+(?:my\s+)?(.+?)\s+"
            r"(?:as\s+)?(?:completed|complete|done)",
            r"(?:move|reschedule)\s+(?:my\s+)?"
            r"(.+?)\s+to\s+(.+)",
        ]

        for pattern in patterns:
            match = re.fullmatch(
                pattern,
                message.strip(),
                flags=re.IGNORECASE
            )

            if not match:
                continue

            task_name = match.group(1).strip()
            task, error = self.find_task_by_name(task_name)

            if task and not error:
                self.context.remember(
                    "task",
                    task["id"],
                    task["title"],
                    intent="task_management"
                )
            return

    def remember_new_task(self, old_task_ids):
        tasks = self.tasks_db.get_tasks()

        new_tasks = [
            task for task in tasks
            if task["id"] not in old_task_ids
        ]

        if len(new_tasks) == 1:
            task = new_tasks[0]

            self.context.remember(
                "task",
                task["id"],
                task["title"],
                intent="add_task"
            )

    def remember_recommended_task(self, message, response):
        lowered = message.lower()

        phrases = (
            "what should i work on next",
            "what should i do next",
            "suggest a task",
            "recommend a task",
            "next task",
        )

        if not any(phrase in lowered for phrase in phrases):
            return

        match = re.search(r"\bID:\s*#(\d+)", response)

        if not match:
            return

        task = self.get_task_by_id(int(match.group(1)))

        if task:
            self.context.remember(
                "task",
                task["id"],
                task["title"],
                intent="recommended_task"
            )
