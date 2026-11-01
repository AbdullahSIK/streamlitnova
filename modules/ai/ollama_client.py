
import json
import threading
import urllib.request
import urllib.error


class OllamaClient:

    def __init__(
        self,
        model="qwen2.5:1.5b",
        base_url="http://localhost:11434"
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def is_available(self):
        try:
            request = urllib.request.Request(
                f"{self.base_url}/api/tags",
                method="GET"
            )

            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status == 200

        except (urllib.error.URLError, TimeoutError, OSError):
            return False

    def _build_messages(self, message, system_prompt=None):
        messages = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        # Accept structured conversation history.
        if isinstance(message, list):
            for item in message:
                if not isinstance(item, dict):
                    continue

                role = item.get("role")
                content = item.get("content")

                if role not in ("user", "assistant"):
                    continue

                if not isinstance(content, str) or not content.strip():
                    continue

                messages.append({
                    "role": role,
                    "content": content
                })

        # Keep compatibility with ordinary string messages.
        elif isinstance(message, str) and message.strip():
            messages.append({
                "role": "user",
                "content": message
            })

        return messages

    def chat(self, message, system_prompt=None):
        """Generate a complete response."""

        messages = self._build_messages(message, system_prompt)

        if not messages:
            return "Please enter a message."

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }

        data = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=180
            ) as response:
                result = json.loads(
                    response.read().decode("utf-8")
                )

            return result.get("message", {}).get(
                "content",
                "NOVA couldn't generate a response."
            ).strip()

        except urllib.error.HTTPError as error:
            details = error.read().decode(
                "utf-8",
                errors="replace"
            )
            return f"Ollama error ({error.code}): {details}"

        except urllib.error.URLError:
            return (
                "Cannot connect to Ollama. "
                "Make sure the Ollama application is running."
            )

        except TimeoutError:
            return "NOVA took too long to respond. Please try again."

        except (ValueError, OSError) as error:
            return f"Unexpected error: {error}"

    def stream_chat(
        self,
        message,
        system_prompt=None,
        stop_event=None
    ):
        """Generate a response piece by piece."""

        messages = self._build_messages(message, system_prompt)

        if not messages:
            yield "Please enter a message."
            return

        if stop_event is None:
            stop_event = threading.Event()

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True
        }

        data = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=180
            ) as response:

                for line in response:
                    if stop_event.is_set():
                        break

                    if not line.strip():
                        continue

                    try:
                        result = json.loads(
                            line.decode("utf-8")
                        )
                    except (ValueError, UnicodeDecodeError):
                        continue

                    if "error" in result:
                        yield f"\nOllama error: {result['error']}"
                        return

                    fragment = result.get(
                        "message", {}
                    ).get("content", "")

                    if fragment:
                        yield fragment

                    if result.get("done", False):
                        break

        except urllib.error.HTTPError as error:
            details = error.read().decode(
                "utf-8",
                errors="replace"
            )
            yield f"Ollama error ({error.code}): {details}"

        except urllib.error.URLError:
            yield (
                "Cannot connect to Ollama. "
                "Make sure the Ollama application is running."
            )

        except TimeoutError:
            yield "\nNOVA took too long to respond."

        except (ValueError, OSError) as error:
            yield f"\nUnexpected error: {error}"
