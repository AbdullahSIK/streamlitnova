
import re


class IntentRouter:
    """
    Central natural-language intent detector for NOVA.
    Identifies the user's intended feature and action.
    """

    def __init__(self):
        self.patterns = {
            "tasks.today": [
                r"\b(today|today's|todays)\b.*\b(task|tasks|work|todo|to-do|plan|schedule)\b",
                r"\b(task|tasks|work|todo|to-do|plan|schedule)\b.*\b(today|today's|todays)\b",
                r"\bwhat\s+(?:do|should)\s+i\s+(?:need\s+to\s+)?(?:do|finish|complete)\s+today\b",
                r"\bwhat\s+do\s+i\s+have\s+to\s+do\b",
                r"\bam\s+i\s+free\s+today\b",
                r"\banything\s+(?:due|planned|scheduled)\s+today\b",
            ],

            "tasks.overdue": [
                r"\boverdue\b",
                r"\blate\s+tasks?\b",
                r"\bmissed\s+(?:my\s+)?deadlines?\b",
                r"\bpassed\s+deadlines?\b",
                r"\btasks?\s+(?:past|after)\s+(?:their\s+)?deadline\b",
            ],

            "tasks.next": [
                r"\bwhat\s+should\s+i\s+(?:do|work\s+on)\s+next\b",
                r"\bwhat\s+do\s+i\s+do\s+next\b",
                r"\bwhich\s+task\s+should\s+i\s+(?:do|start|finish)\b",
                r"\bsuggest\s+(?:a\s+)?(?:task|work)\b",
                r"\brecommend\s+(?:a\s+)?task\b",
            ],

            "tasks.complete": [
                r"\bmark\b.+\b(?:completed|complete|done)\b",
                r"\bset\b.+\b(?:completed|complete|done)\b",
                r"\bcomplete\s+(?:my\s+)?task\b.+",
                r"\bfinish\s+(?:my\s+)?task\b.+",
            ],

            "tasks.delete": [
                r"\b(delete|remove)\b.+\b(task|homework|reminder)\b",
                r"\b(delete|remove)\s+(?:my\s+)?task\b",
            ],

            "tasks.update": [
                r"\b(rename|retitle|reschedule|change|update|move)\b.+\b(task|deadline|due|priority)\b",
                r"\b(make|set)\b.+\b(high|medium|low)\s+priority\b",
            ],

            "tasks.create": [
                r"\b(remind\s+me|i\s+need\s+to|i\s+have\s+to|"
                r"i\s+must|add\s+(?:a\s+)?task|create\s+(?:a\s+)?task|"
                r"make\s+(?:a\s+)?task)\b",
                r"\b(add|create|make)\s+(?:a\s+)?(?:new\s+)?task\b",
            ],

            "tasks.list": [
                r"\b(show|list|display|view)\b.*\b(my\s+)?tasks?\b",
                r"\bwhat\s+(?:are|is)\s+(?:my\s+)?tasks?\b",
                r"\bwhat\s+tasks?\s+do\s+i\s+have\b",
                r"\bmy\s+task\s+list\b",
                r"\bwhat\s+do\s+i\s+need\s+to\s+do\b",
            ],

            "notes.search": [
                r"\b(find|search|look\s+for|locate)\b.+\b(notes?|notebook)\b",
                r"\bnotes?\s+(?:about|on|containing)\b",
                r"\bwhat\s+did\s+i\s+write\s+about\b",
            ],

            "notes.list": [
                r"\b(show|list|display|view)\b.+\b(my\s+)?notes?\b",
                r"\bwhat\s+notes?\s+do\s+i\s+have\b",
                r"\bmy\s+saved\s+notes?\b",
            ],

            "notes.create": [
                r"\b(save|store|write|create|add)\b.+\b(note|notes)\b",
                r"\bremember\s+this\s+as\s+a\s+note\b",
            ],

            "calendar.today": [
                r"\b(calendar|schedule|events?|appointments?)\b.*\btoday\b",
                r"\btoday\b.*\b(calendar|schedule|events?|appointments?)\b",
            ],

            "calendar.create": [
                r"\b(add|create|schedule|book|put)\b.+\b(event|meeting|appointment)\b",
                r"\b(schedule|plan)\s+(?:a\s+)?meeting\b",
            ],

            "calendar.upcoming": [
                r"\b(upcoming|future)\s+events?\b",
                r"\b(events?|appointments?)\b.+\b(coming\s+up|upcoming)\b",
                r"\bwhat'?s\s+coming\s+up\b",
                r"\bwhat\s+is\s+coming\s+up\b",
                r"\bwhat'?s\s+happening\b.+\b(calendar|schedule)\b",
                r"\bwhat\s+is\s+happening\b.+\b(calendar|schedule)\b",
                r"\bwhat'?s\s+on\s+my\s+calendar\b",
                r"\bshow\s+(?:me\s+)?(?:my\s+)?calendar\b",
            ],

            "calendar.list": [
                r"\b(show|list|display|view)\b.+\b(calendar|events?|appointments?)\b",
                r"\bwhat\s+(?:events?|appointments?)\s+do\s+i\s+have\b",
                r"\bwhat'?s\s+on\s+my\s+calendar\b",
                r"\bwhats\s+on\s+my\s+calendar\b",
            ],

            "pc.cpu": [
                r"\b(cpu|processor)\b.+\b(usage|performance|temperature|load)\b",
                r"\b(usage|performance|temperature|load)\b.+\b(cpu|processor)\b",
                r"\bhow\s+much\s+cpu\b",
            ],

            "pc.ram": [
                r"\b(ram|memory)\b.+\b(usage|used|available|free|performance)\b",
                r"\b(how\s+much|check)\b.+\b(ram|memory)\b",
            ],

            "pc.gpu": [
                r"\b(gpu|graphics\s+card|graphics\s+processor)\b",
                r"\b(vram|video\s+memory)\b",
            ],

            "pc.status": [
                r"\b(system|pc|computer)\s+(status|report|performance|health)\b",
                r"\bhow\s+is\s+my\s+(pc|computer)\b",
                r"\bcheck\s+my\s+(pc|computer|system)\b",
                r"\bcomplete\s+system\s+report\b",
                r"\bcomplete\s+(?:pc|computer)\s+report\b",
            ],
        }

    def normalize(self, message):
        message = message.lower().strip()
        message = re.sub(r"\s+", " ", message)
        return message

    def classify(self, message):
        text = self.normalize(message)

        if not text:
            return None

        priority_order = [
            "pc.status",
            "pc.cpu",
            "pc.ram",
            "pc.gpu",

            "tasks.today",
            "tasks.overdue",
            "tasks.next",
            "tasks.complete",
            "tasks.delete",
            "tasks.update",
            "tasks.create",
            "tasks.list",

            "notes.search",
            "notes.create",
            "notes.list",

            "calendar.today",
            "calendar.create",
            "calendar.upcoming",
            "calendar.list",
        ]

        for intent in priority_order:
            for pattern in self.patterns[intent]:
                if re.search(pattern, text, re.IGNORECASE):
                    return intent

        return None

    def is_local_intent(self, message):
        return self.classify(message) is not None
