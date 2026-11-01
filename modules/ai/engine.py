
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import psutil

from core.database import Database
from core.notes_database import NotesDatabase
from core.calendar_database import CalendarDatabase


class NOVAEngine:

    def __init__(self):
        self.tasks_db = Database()
        self.notes_db = NotesDatabase()
        self.calendar_db = CalendarDatabase()

    # --------------------------------------------------
    # MAIN COMMAND PROCESSOR
    # --------------------------------------------------

    def process(self, message):
        message = message.strip()

        if not message:
            return "Please enter a command."

        command = message.lower().strip()
        command = re.sub(r"\s+", " ", command)

        if command in ("help", "commands", "what can you do?"):
            return self.help_message()

        if command in ("hello", "hi", "hey"):
            return (
                "Hello! I'm NOVA. Your local assistant engine "
                "is online. What can I help you with?"
            )

        # FLEXIBLE NATURAL-LANGUAGE TASK QUERIES

        task_query = self.resolve_task_query(command)

        if task_query == "today":
            return self.today_tasks()

        if task_query == "overdue":
            return self.overdue_tasks()

        if task_query == "next":
            return self.suggest_next_task()

        if task_query == "all":
            return self.list_tasks()

        # SMART DAILY PLANNER COMMANDS

        if command in (
            "today",
            "today's tasks",
            "todays tasks",
            "show today's tasks",
            "show todays tasks",
            "what do i need to do today",
            "what do i have to do today",
            "show my tasks for today",
            "my tasks for today",
            "today's plan",
            "todays plan",
            "daily plan",
        ):
            return self.today_tasks()

        if command in (
            "overdue",
            "overdue tasks",
            "show overdue tasks",
            "what tasks are overdue",
            "do i have overdue tasks",
            "show my overdue tasks",
        ):
            return self.overdue_tasks()

        if command in (
            "what should i work on next",
            "what should i do next",
            "what should i work on",
            "suggest a task",
            "recommend a task",
            "next task",
            "what is my next task",
        ):
            return self.suggest_next_task()

        if command in (
            "list tasks",
            "show tasks",
            "my tasks",
            "show my tasks",
            "what are my tasks",
            "what tasks do i have",
            "what's on my task list",
            "whats on my task list",
        ):
            return self.list_tasks()

        if command in (
            "upcoming events",
            "show events",
            "my events",
            "show my events",
            "what events are coming up",
            "what's on my calendar",
            "whats on my calendar",
            "show my calendar",
        ):
            return self.upcoming_events()

        if command in (
            "list notes",
            "show notes",
            "my notes",
            "show my notes",
            "what notes do i have",
        ):
            return self.list_notes()

        if (
            command.startswith("system status")
            or command == "pc status"
            or "how is my pc doing" in command
            or "how is my pc performing" in command
            or "check my pc" in command
            or "system performance" in command
        ):
            return self.system_status()

        # EXACT COMMANDS

        if command.startswith("search notes |"):
            parts = message.split("|", 1)

            if len(parts) != 2 or not parts[1].strip():
                return "Usage: search notes | keyword"

            return self.search_notes(parts[1].strip())

        if command.startswith("add task |"):
            return self.add_task(message)

        if command.startswith("complete task |"):
            return self.complete_task(message)

        if command.startswith("delete task |"):
            return self.delete_task(message)

        if command.startswith("add note |"):
            return self.add_note(message)

        if command.startswith("add event |"):
            return self.add_event(message)

        # NATURAL-LANGUAGE TASK MANAGEMENT

        management_response = self.handle_task_management(message)

        if management_response is not None:
            return management_response

        # NATURAL-LANGUAGE TASK CREATION

        natural_task = self.parse_natural_task(message)

        if natural_task is not None:
            title, due_date, priority = natural_task

            self.tasks_db.add_task(
                title,
                "",
                priority,
                due_date
            )

            return (
                "Task added successfully!\n\n"
                f"Task: {title}\n"
                f"Due date: {due_date}\n"
                f"Priority: {priority}"
            )

        return (
            "I don't recognise that request yet.\n\n"
            "Try asking me to show your tasks, notes, events, "
            "or PC status. You can also type 'help'."
        )

    # --------------------------------------------------
    # NATURAL-LANGUAGE TASK QUERY RESOLVER
    # --------------------------------------------------

    def resolve_task_query(self, command):
        text = command.lower().strip()
        text = re.sub(r"[?!.,]+$", "", text)
        text = re.sub(r"\s+", " ", text)

        # TODAY'S TASKS

        today_patterns = (
            r"\btoday\b",
            r"\bfor today\b",
            r"\bdue today\b",
            r"\bdue for today\b",
            r"\btoday's\b",
            r"\btodays\b",
        )

        asks_about_today = any(
            re.search(pattern, text)
            for pattern in today_patterns
        )

        today_action_patterns = (
            r"\bneed to (?:do|finish|complete|get done)\b",
            r"\bhave to (?:do|finish|complete|get done)\b",
            r"\bshould i (?:do|finish|complete)\b",
            r"\bshould i get done\b",
            r"\banything i need to do\b",
            r"\banything i have to do\b",
            r"\bwhat should i complete\b",
            r"\bwhat should i finish\b",
            r"\bwhat do i need to get done\b",
            r"\bwhat do i have to get done\b",
            r"\bwhat do i need to complete\b",
        )

        asks_about_daily_work = any(
            re.search(pattern, text)
            for pattern in today_action_patterns
        )

        if asks_about_today and asks_about_daily_work:
            return "today"

        # NEXT RECOMMENDED TASK
        # IMPORTANT: This check must happen BEFORE checking
        # whether the user explicitly said "task".

        next_patterns = (
            r"\bwhat should i work on next\b",
            r"\bwhat should i do next\b",
            r"\bwhat do i work on next\b",
            r"\bwhat should i focus on next\b",
            r"\bwhat should i do now\b",
            r"\bwhat do i do now\b",
            r"\bwhat should i work on\b",
            r"\bwhich task should i do next\b",
            r"\bwhich task should i work on\b",
            r"\bwhich task is next\b",
            r"\bwhat is my next task\b",
            r"\bwhat's my next task\b",
            r"\bwhats my next task\b",
            r"\bnext task\b",
            r"\brecommend a task\b",
            r"\bsuggest a task\b",
            r"\bpick my next task\b",
        )

        if any(
            re.search(pattern, text)
            for pattern in next_patterns
        ):
            return "next"

        # The remaining queries should explicitly mention tasks.

        task_words = (
            "task",
            "tasks",
            "todo",
            "to-do",
            "to do",
        )

        has_task_word = any(
            re.search(rf"\b{re.escape(word)}\b", text)
            for word in task_words
        )

        if not has_task_word:
            return None

        if asks_about_today:
            return "today"

        # OVERDUE TASKS

        overdue_patterns = (
            r"\boverdue\b",
            r"\bpast due\b",
            r"\blate tasks\b",
            r"\bmissed deadlines\b",
        )

        if any(
            re.search(pattern, text)
            for pattern in overdue_patterns
        ):
            return "overdue"

        # ALL TASKS

        all_patterns = (
            r"\bshow\b",
            r"\blist\b",
            r"\btell me\b",
            r"\bcan you tell me\b",
            r"\bwhat are\b",
            r"\bwhat tasks\b",
            r"\bwhich tasks\b",
            r"\bwhat do i have\b",
            r"\bdo i have\b",
            r"\bdisplay\b",
            r"\bfind\b",
            r"\bget\b",
        )

        if any(
            re.search(pattern, text)
            for pattern in all_patterns
        ):
            return "all"

        return None

    # --------------------------------------------------
    # SMART DAILY PLANNER
    # --------------------------------------------------

    def get_task_date(self, task):
        due_date = task.get("due_date")

        if not due_date:
            return None

        try:
            return datetime.strptime(
                str(due_date).strip(),
                "%Y-%m-%d"
            ).date()
        except (ValueError, TypeError):
            return None

    def get_pending_tasks(self):
        return [
            task for task in self.tasks_db.get_tasks()
            if not task["completed"]
        ]

    def priority_rank(self, priority):
        priorities = {
            "high": 0,
            "medium": 1,
            "low": 2,
        }

        return priorities.get(
            str(priority).lower(),
            3
        )

    def sort_planner_tasks(self, tasks):
        today = datetime.now().date()

        def sort_key(task):
            due_date = self.get_task_date(task)

            if due_date is None:
                date_rank = 2
                date_value = datetime.max.date()
            elif due_date < today:
                date_rank = 0
                date_value = due_date
            else:
                date_rank = 1
                date_value = due_date

            return (
                date_rank,
                date_value,
                self.priority_rank(task["priority"])
            )

        return sorted(tasks, key=sort_key)

    def today_tasks(self):
        today = datetime.now().date()
        tasks = self.tasks_db.get_tasks()

        today_list = [
            task for task in tasks
            if self.get_task_date(task) == today
        ]

        if not today_list:
            return (
                "YOUR PLAN FOR TODAY\n\n"
                "You have no tasks due today.\n\n"
                "You can relax or get ahead on upcoming tasks!"
            )

        pending = [
            task for task in today_list
            if not task["completed"]
        ]

        completed = [
            task for task in today_list
            if task["completed"]
        ]

        lines = [
            f"YOUR PLAN FOR TODAY — {today.strftime('%d %B %Y')}",
            "",
            f"Total tasks: {len(today_list)}",
            f"Pending: {len(pending)}",
            f"Completed: {len(completed)}",
            ""
        ]

        if pending:
            lines.append("PENDING TASKS")

            pending.sort(
                key=lambda task: self.priority_rank(
                    task["priority"]
                )
            )

            for task in pending:
                lines.append(
                    f"\n#{task['id']} - {task['title']}"
                    f"\n   Priority: {task['priority']}"
                )

        if completed:
            lines.extend(["", "COMPLETED TASKS"])

            for task in completed:
                lines.append(
                    f"\n#{task['id']} - {task['title']}"
                )

        if not pending:
            lines.extend([
                "",
                "Excellent! All your tasks for today are completed."
            ])

        return "\n".join(lines)

    def overdue_tasks(self):
        today = datetime.now().date()

        overdue = [
            task for task in self.get_pending_tasks()
            if (
                self.get_task_date(task) is not None
                and self.get_task_date(task) < today
            )
        ]

        if not overdue:
            return "You have no overdue tasks. Great work!"

        overdue = self.sort_planner_tasks(overdue)

        lines = [
            "OVERDUE TASKS",
            "",
            f"You have {len(overdue)} overdue task(s):",
            ""
        ]

        for task in overdue:
            due_date = self.get_task_date(task)
            days_late = (today - due_date).days

            lines.append(
                f"#{task['id']} - {task['title']}"
                f"\n   Due: {due_date.strftime('%d %B %Y')}"
                f"\n   Overdue by: {days_late} day(s)"
                f"\n   Priority: {task['priority']}"
            )

        lines.extend([
            "",
            "Suggestion: Start by reviewing your overdue tasks."
        ])

        return "\n\n".join(lines)

    def suggest_next_task(self):
        today = datetime.now().date()
        pending = self.get_pending_tasks()

        if not pending:
            return (
                "You have no pending tasks!\n\n"
                "Your task list is clear. Great work!"
            )

        ordered = self.sort_planner_tasks(pending)
        task = ordered[0]

        due_date = self.get_task_date(task)

        if due_date is None:
            reason = "This task has no deadline."
        elif due_date < today:
            days_late = (today - due_date).days
            reason = (
                f"This task is overdue by {days_late} day(s)."
            )
        elif due_date == today:
            reason = "This task is due today."
        else:
            reason = (
                f"This task is due on "
                f"{due_date.strftime('%d %B %Y')}."
            )

        return (
            "YOUR NEXT RECOMMENDED TASK\n\n"
            f"Task: {task['title']}\n"
            f"ID: #{task['id']}\n"
            f"Priority: {task['priority']}\n"
            f"Reason: {reason}\n\n"
            "Focus on this task first, then ask me again "
            "for your next recommendation."
        )

    # --------------------------------------------------
    # NATURAL-LANGUAGE TASK MANAGEMENT
    # --------------------------------------------------

    def handle_task_management(self, message):
        text = message.strip()

        match = re.fullmatch(
            r"(?:mark|set)\s+(?:my\s+)?(.+?)\s+"
            r"(?:as\s+)?(?:completed|complete|done)",
            text,
            flags=re.IGNORECASE
        )

        if match:
            return self.complete_task_by_name(match.group(1))

        match = re.fullmatch(
            r"complete\s+(?:my\s+)?(?:task\s+)?"
            r"(?:called\s+)?(.+)",
            text,
            flags=re.IGNORECASE
        )

        if match:
            return self.complete_task_by_name(match.group(1))

        match = re.fullmatch(
            r"(?:delete|remove)\s+(?:my\s+)?"
            r"(?:task\s+)?(?:called\s+)?(.+)",
            text,
            flags=re.IGNORECASE
        )

        if match:
            return self.delete_task_by_name(match.group(1))

        match = re.fullmatch(
            r"(?:make|set|change)\s+(?:my\s+)?"
            r"(.+?)\s+(?:task\s+)?(?:to\s+)?"
            r"(high|medium|low)(?:\s+priority)?",
            text,
            flags=re.IGNORECASE
        )

        if match:
            task_name = match.group(1)
            priority = match.group(2).capitalize()

            return self.change_task_priority(
                task_name,
                priority
            )

        match = re.fullmatch(
            r"(?:change|move|update|reschedule)\s+"
            r"(?:my\s+)?(.+?)\s+"
            r"(?:task\s+)?(?:deadline|due date)\s+to\s+(.+)",
            text,
            flags=re.IGNORECASE
        )

        if match:
            return self.change_task_deadline(
                match.group(1),
                match.group(2)
            )

        match = re.fullmatch(
            r"(?:move|reschedule)\s+(?:my\s+)?"
            r"(.+?)\s+to\s+(.+)",
            text,
            flags=re.IGNORECASE
        )

        if match:
            return self.change_task_deadline(
                match.group(1),
                match.group(2)
            )

        match = re.fullmatch(
            r"(?:rename|retitle)\s+(?:my\s+)?"
            r"(.+?)\s+to\s+(.+)",
            text,
            flags=re.IGNORECASE
        )

        if match:
            return self.rename_task(
                match.group(1),
                match.group(2)
            )

        return None

    def find_task_by_name(self, task_name):
        task_name = task_name.strip()

        task_name = re.sub(
            r"^(my|the)\s+",
            "",
            task_name,
            flags=re.IGNORECASE
        )

        task_name = re.sub(
            r"\s+task$",
            "",
            task_name,
            flags=re.IGNORECASE
        )

        query = task_name.casefold().strip()

        if not query:
            return None, "Please provide a task name."

        tasks = self.tasks_db.get_tasks()

        exact_matches = [
            task for task in tasks
            if task["title"].casefold().strip() == query
        ]

        if len(exact_matches) == 1:
            return exact_matches[0], None

        if len(exact_matches) > 1:
            return None, self.ambiguous_task_message(exact_matches)

        matches = [
            task for task in tasks
            if query in task["title"].casefold()
        ]

        if len(matches) == 1:
            return matches[0], None

        if len(matches) > 1:
            return None, self.ambiguous_task_message(matches)

        return None, (
            f"I couldn't find a task matching '{task_name}'.\n\n"
            "Try 'Show my tasks' to see your task names."
        )

    def ambiguous_task_message(self, tasks):
        lines = [
            "I found multiple matching tasks.",
            "Please use a more specific task name or its ID:",
            ""
        ]

        for task in tasks:
            lines.append(
                f"#{task['id']} - {task['title']}"
            )

        return "\n".join(lines)

    def complete_task_by_name(self, task_name):
        task, error = self.find_task_by_name(task_name)

        if error:
            return error

        if task["completed"]:
            return f"'{task['title']}' is already completed."

        self.tasks_db.set_completed(task["id"], True)

        return (
            "Task marked as completed!\n\n"
            f"Task: {task['title']}\n"
            f"ID: #{task['id']}"
        )

    def delete_task_by_name(self, task_name):
        task, error = self.find_task_by_name(task_name)

        if error:
            return error

        self.tasks_db.delete_task(task["id"])

        return (
            "Task deleted successfully.\n\n"
            f"Task: {task['title']}\n"
            f"ID: #{task['id']}"
        )

    def change_task_priority(self, task_name, priority):
        task, error = self.find_task_by_name(task_name)

        if error:
            return error

        self.tasks_db.update_task(
            task["id"],
            task["title"],
            task["description"],
            priority,
            task["due_date"]
        )

        return (
            "Task priority updated!\n\n"
            f"Task: {task['title']}\n"
            f"New priority: {priority}"
        )

    def change_task_deadline(self, task_name, date_text):
        task, error = self.find_task_by_name(task_name)

        if error:
            return error

        due_date = self.extract_due_date(
            date_text,
            allow_to=True
        )

        if due_date is None:
            return (
                "I couldn't understand that deadline.\n\n"
                "Try a date such as tomorrow, Friday, "
                "next Monday, or today."
            )

        formatted_date = due_date.strftime("%Y-%m-%d")

        self.tasks_db.update_task(
            task["id"],
            task["title"],
            task["description"],
            task["priority"],
            formatted_date
        )

        return (
            "Task deadline updated!\n\n"
            f"Task: {task['title']}\n"
            f"New deadline: {formatted_date}"
        )

    def rename_task(self, old_name, new_name):
        task, error = self.find_task_by_name(old_name)

        if error:
            return error

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

        return (
            "Task renamed successfully!\n\n"
            f"Old name: {task['title']}\n"
            f"New name: {new_name}"
        )

    # --------------------------------------------------
    # NATURAL-LANGUAGE TASK CREATION
    # --------------------------------------------------

    def parse_natural_task(self, message):
        text = message.strip()
        lowered = text.lower()

        prefixes = (
            "remind me to ",
            "remind me ",
            "i need to ",
            "i have to ",
            "i want to ",
            "i must ",
            "need to ",
            "have to ",
            "add a task to ",
            "add task to ",
            "create a task to ",
            "create task to ",
            "make a task to ",
        )

        task_text = None

        for prefix in prefixes:
            if lowered.startswith(prefix):
                task_text = text[len(prefix):].strip()
                break

        if task_text is None:
            direct_starts = (
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

            for prefix in direct_starts:
                if lowered.startswith(prefix):
                    task_text = text
                    break

        if not task_text:
            return None

        due_date = self.extract_due_date(task_text)

        if due_date is None:
            return None

        priority = self.extract_priority(task_text)

        task_text = re.sub(
            r"\b(high|medium|low)\s+priority\b",
            "",
            task_text,
            flags=re.IGNORECASE
        )

        task_text = re.sub(
            r"\bpriority\s+(high|medium|low)\b",
            "",
            task_text,
            flags=re.IGNORECASE
        )

        task_text = re.sub(
            r"\bby\s+(next\s+)?(monday|tuesday|wednesday|"
            r"thursday|friday|saturday|sunday)\b",
            "",
            task_text,
            flags=re.IGNORECASE
        )

        task_text = re.sub(
            r"\bon\s+(next\s+)?(monday|tuesday|wednesday|"
            r"thursday|friday|saturday|sunday)\b",
            "",
            task_text,
            flags=re.IGNORECASE
        )

        task_text = re.sub(
            r"\bnext\s+(monday|tuesday|wednesday|"
            r"thursday|friday|saturday|sunday)\b",
            "",
            task_text,
            flags=re.IGNORECASE
        )

        task_text = re.sub(
            r"\b(monday|tuesday|wednesday|thursday|"
            r"friday|saturday|sunday)\b",
            "",
            task_text,
            flags=re.IGNORECASE
        )

        task_text = re.sub(
            r"\b(today|tomorrow)\b",
            "",
            task_text,
            flags=re.IGNORECASE
        )

        task_text = re.sub(
            r"\bby\b|\bon\b",
            "",
            task_text,
            flags=re.IGNORECASE
        )

        task_text = re.sub(r"\s+", " ", task_text)
        task_text = task_text.strip(" .,!?:;-")

        if not task_text:
            return None

        removable_starts = (
            "finish ",
            "complete ",
            "do my ",
        )

        for prefix in removable_starts:
            if task_text.lower().startswith(prefix):
                task_text = task_text[len(prefix):].strip()
                break

        if not task_text:
            return None

        return (
            task_text,
            due_date.strftime("%Y-%m-%d"),
            priority
        )

    def extract_due_date(self, text, allow_to=False):
        lowered = text.lower()
        today = datetime.now().date()

        if re.search(r"\btomorrow\b", lowered):
            return today + timedelta(days=1)

        if re.search(r"\btoday\b", lowered):
            return today

        weekdays = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }

        next_match = re.search(
            r"\bnext\s+(monday|tuesday|wednesday|"
            r"thursday|friday|saturday|sunday)\b",
            lowered
        )

        if next_match:
            weekday = weekdays[next_match.group(1)]
            days_ahead = (weekday - today.weekday()) % 7

            if days_ahead == 0:
                days_ahead = 7

            return today + timedelta(days=days_ahead)

        weekday_prepositions = ["by", "on"]

        if allow_to:
            weekday_prepositions.append("to")

        preposition_pattern = "|".join(weekday_prepositions)

        weekday_match = re.search(
            rf"\b(?:{preposition_pattern})\s+"
            r"(monday|tuesday|wednesday|thursday|"
            r"friday|saturday|sunday)\b",
            lowered
        )

        if weekday_match:
            weekday = weekdays[weekday_match.group(1)]
            days_ahead = (weekday - today.weekday()) % 7

            if days_ahead == 0:
                days_ahead = 7

            return today + timedelta(days=days_ahead)

        ending_match = re.search(
            r"\b(monday|tuesday|wednesday|thursday|"
            r"friday|saturday|sunday)[.!?]*$",
            lowered
        )

        if ending_match:
            weekday = weekdays[ending_match.group(1)]
            days_ahead = (weekday - today.weekday()) % 7

            if days_ahead == 0:
                days_ahead = 7

            return today + timedelta(days=days_ahead)

        return None

    def extract_priority(self, text):
        lowered = text.lower()

        if re.search(
            r"\b(high priority|priority high|urgent|"
            r"very important)\b",
            lowered
        ):
            return "High"

        if re.search(
            r"\b(low priority|priority low|not urgent)\b",
            lowered
        ):
            return "Low"

        return "Medium"

    # --------------------------------------------------
    # HELP
    # --------------------------------------------------

    def help_message(self):
        return """
NOVA LOCAL ASSISTANT

SMART DAILY PLANNER
  Show today's tasks
  Show overdue tasks
  What should I work on next?
  Show my daily plan

TASKS
  Show my tasks
  Remind me to study tomorrow
  Finish English homework by Friday
  Study Chemistry tomorrow, high priority
  Prepare for my CS exam next Monday

TASK MANAGEMENT
  Change my English homework deadline to Monday
  Make my Chemistry task high priority
  Rename my project task to Science project
  Delete my Maths homework task
  Mark English homework as completed

EXACT TASK COMMANDS
  add task | title | YYYY-MM-DD | priority | description
  complete task | ID
  delete task | ID

NOTES
  Show my notes
  search notes | keyword
  add note | title | content

CALENDAR
  Show my calendar
  add event | title | YYYY-MM-DD | HH:MM | description | reminder_minutes

PC MONITOR
  How is my PC doing?
  system status

GENERAL
  hello
  help

You can use natural language for supported requests.
"""

    # --------------------------------------------------
    # TASKS
    # --------------------------------------------------

    def list_tasks(self):
        tasks = self.tasks_db.get_tasks()

        if not tasks:
            return "You don't have any tasks yet."

        lines = ["YOUR TASKS", ""]

        for task in tasks:
            status = "Completed" if task["completed"] else "Pending"

            lines.append(
                f"#{task['id']} - {task['title']}\n"
                f"   Priority: {task['priority']}\n"
                f"   Due: {task['due_date']}\n"
                f"   Status: {status}"
            )

        return "\n\n".join(lines)

    def add_task(self, message):
        parts = message.split("|")

        if len(parts) != 5:
            return (
                "Incorrect format.\n\n"
                "add task | title | YYYY-MM-DD | priority | description"
            )

        _, title, due_date, priority, description = parts

        title = title.strip()
        due_date = due_date.strip()
        priority = priority.strip().capitalize()
        description = description.strip()

        if not title:
            return "Task title cannot be empty."

        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            return "Please use the date format YYYY-MM-DD."

        if priority not in ("Low", "Medium", "High"):
            return "Priority must be Low, Medium or High."

        self.tasks_db.add_task(
            title,
            description,
            priority,
            due_date
        )

        return f"Task added successfully: {title}"

    def complete_task(self, message):
        parts = message.split("|", 1)

        if len(parts) != 2:
            return "Usage: complete task | ID"

        try:
            task_id = int(parts[1].strip())
        except ValueError:
            return "Please provide a valid task ID."

        task = next(
            (
                item for item in self.tasks_db.get_tasks()
                if item["id"] == task_id
            ),
            None
        )

        if not task:
            return f"I couldn't find task #{task_id}."

        if task["completed"]:
            return f"Task #{task_id} is already completed."

        self.tasks_db.set_completed(task_id, True)

        return f"Task completed: {task['title']}"

    def delete_task(self, message):
        parts = message.split("|", 1)

        if len(parts) != 2:
            return "Usage: delete task | ID"

        try:
            task_id = int(parts[1].strip())
        except ValueError:
            return "Please provide a valid task ID."

        task = next(
            (
                item for item in self.tasks_db.get_tasks()
                if item["id"] == task_id
            ),
            None
        )

        if not task:
            return f"I couldn't find task #{task_id}."

        self.tasks_db.delete_task(task_id)

        return f"Task deleted: {task['title']}"

    # --------------------------------------------------
    # NOTES
    # --------------------------------------------------

    def list_notes(self):
        notes = self.notes_db.get_notes()

        if not notes:
            return "You don't have any notes yet."

        lines = ["YOUR NOTES", ""]

        for note in notes:
            pinned = " [PINNED]" if note["pinned"] else ""

            lines.append(
                f"#{note['id']} - {note['title']}{pinned}\n"
                f"   {note['content'][:150]}"
            )

        return "\n\n".join(lines)

    def search_notes(self, keyword):
        notes = self.notes_db.get_notes(keyword)

        if not notes:
            return f"No notes found for '{keyword}'."

        lines = [f"SEARCH RESULTS: {keyword}", ""]

        for note in notes:
            lines.append(
                f"#{note['id']} - {note['title']}\n"
                f"   {note['content'][:200]}"
            )

        return "\n\n".join(lines)

    def add_note(self, message):
        parts = message.split("|", 2)

        if len(parts) != 3:
            return "Usage: add note | title | content"

        title = parts[1].strip()
        content = parts[2].strip()

        if not title:
            return "Note title cannot be empty."

        note_id = self.notes_db.add_note(title, content)

        return f"Note saved successfully: {title} (ID: {note_id})"

    # --------------------------------------------------
    # CALENDAR
    # --------------------------------------------------

    def upcoming_events(self):
        events = self.calendar_db.get_upcoming_events(10)

        if not events:
            return "You don't have any upcoming events."

        lines = ["UPCOMING EVENTS", ""]

        for event in events:
            event_time = event["event_time"] or "No time set"

            lines.append(
                f"#{event['id']} - {event['title']}\n"
                f"   Date: {event['event_date']}\n"
                f"   Time: {event_time}"
            )

        return "\n\n".join(lines)

    def add_event(self, message):
        parts = message.split("|", 5)

        if len(parts) != 6:
            return (
                "Incorrect format.\n\n"
                "add event | title | YYYY-MM-DD | HH:MM | "
                "description | reminder_minutes"
            )

        _, title, event_date, event_time, description, reminder = parts

        title = title.strip()
        event_date = event_date.strip()
        event_time = event_time.strip()
        description = description.strip()

        if not title:
            return "Event title cannot be empty."

        try:
            datetime.strptime(event_date, "%Y-%m-%d")
        except ValueError:
            return "Please use the date format YYYY-MM-DD."

        try:
            datetime.strptime(event_time, "%H:%M")
        except ValueError:
            return "Please use the 24-hour time format HH:MM."

        try:
            reminder = int(reminder.strip())
        except ValueError:
            return "Reminder must be a number of minutes."

        if reminder not in (0, 5, 10, 15, 30, 60):
            return "Reminder must be 0, 5, 10, 15, 30 or 60."

        self.calendar_db.add_event(
            title,
            description,
            event_date,
            event_time,
            reminder
        )

        return f"Calendar event added successfully: {title}"

    # --------------------------------------------------
    # PC MONITOR
    # --------------------------------------------------

    def system_status(self):
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage(str(Path.home()))

        result = [
            "NOVA SYSTEM REPORT",
            "",
            f"CPU Usage: {cpu}%",
            f"RAM Usage: {ram.percent}%",
            f"RAM Used: {ram.used / (1024 ** 3):.1f} GB",
            f"RAM Total: {ram.total / (1024 ** 3):.1f} GB",
            f"Disk Usage: {disk.percent}%",
        ]

        try:
            gpu_result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,utilization.gpu,memory.used,memory.total",
                    "--format=csv,noheader,nounits"
                ],
                capture_output=True,
                text=True,
                timeout=3,
                check=True
            )

            gpu_parts = [
                part.strip()
                for part in gpu_result.stdout.strip().split(",")
            ]

            if len(gpu_parts) == 4:
                result.extend([
                    "",
                    f"GPU: {gpu_parts[0]}",
                    f"GPU Usage: {gpu_parts[1]}%",
                    f"VRAM: {gpu_parts[2]} / {gpu_parts[3]} MB"
                ])

        except (
            FileNotFoundError,
            subprocess.SubprocessError,
            OSError
        ):
            result.extend([
                "",
                "GPU information is currently unavailable."
            ])

        return "\n".join(result)
