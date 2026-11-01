
import re


class ConversationContext:
    """
    Stores useful context from the current NOVA conversation.

    This allows NOVA to understand references such as:
    'it', 'that task', 'the same one', and 'that note'.
    """

    def __init__(self):
        self.last_entity = None
        self.last_intent = None
        self.last_result = None

    def remember(self, entity_type, entity_id=None, entity_name=None,
                 intent=None, result=None):
        self.last_entity = {
            "type": entity_type,
            "id": entity_id,
            "name": entity_name
        }

        self.last_intent = intent
        self.last_result = result

    def remember_result(self, intent, result):
        self.last_intent = intent
        self.last_result = result

    def get_entity(self):
        return self.last_entity

    def get_entity_name(self):
        if not self.last_entity:
            return None

        return self.last_entity.get("name")

    def get_entity_id(self):
        if not self.last_entity:
            return None

        return self.last_entity.get("id")

    def get_entity_type(self):
        if not self.last_entity:
            return None

        return self.last_entity.get("type")

    def get_last_intent(self):
        return self.last_intent

    def get_last_result(self):
        return self.last_result

    def has_entity(self):
        return self.last_entity is not None

    def refers_to_previous(self, message):
        """
        Checks whether a message probably refers to the
        previously discussed item.
        """

        if not self.has_entity():
            return False

        text = message.lower().strip()

        references = [
            r"\bit\b",
            r"\bthat\b",
            r"\bthis\b",
            r"\bthat task\b",
            r"\bthis task\b",
            r"\bthe same one\b",
            r"\bthat note\b",
            r"\bthis note\b",
            r"\bthe previous one\b",
            r"\bthe last one\b"
        ]

        return any(re.search(pattern, text) for pattern in references)

    def resolve_reference(self, message):
        """
        Returns the previous entity if the message refers to it.
        Otherwise returns None.
        """

        if self.refers_to_previous(message):
            return self.last_entity

        return None

    def clear(self):
        self.last_entity = None
        self.last_intent = None
        self.last_result = None
