import json
from groq import Groq
from config import (
    GROQ_API_KEY,
    COMPOUND_MODEL,
    LOCAL_AGENT_MODEL,
    SYSTEM_PROMPT,
    MAX_HISTORY,
)
from memory import get_memory_context, remember
from tools import LOCAL_TOOLS


# -------------------------------------------------------------------
# NOVA — Groq agent with request-size protection
# -------------------------------------------------------------------

# Keep API payloads comfortably below request-size limits.
# These limits are character-based, intentionally conservative.
MAX_SYSTEM_PROMPT_CHARS = 12000
MAX_MEMORY_CHARS = 4000
MAX_HISTORY_MESSAGE_CHARS = 3500
MAX_USER_CHARS = 8000
MAX_TOOL_RESULT_CHARS = 6000
MAX_COMPOUND_PROMPT_CHARS = 6000
RESEARCH_API_MODEL = "openai/gpt-oss-120b"


def _trim(text, limit):
    """Trim text safely while preserving the beginning and end."""
    text = str(text or "")
    if len(text) <= limit:
        return text

    if limit < 100:
        return text[:limit]

    head = int(limit * 0.72)
    tail = limit - head
    return (
        text[:head]
        + "\n\n[content truncated to keep the Groq request small]\n\n"
        + text[-tail:]
    )


def _clean_history(history):
    """Keep history compact enough for the next Groq request."""
    cleaned = []

    for message in history[-MAX_HISTORY:]:
        if not isinstance(message, dict):
            continue

        item = dict(message)

        if "content" in item and item["content"] is not None:
            item["content"] = _trim(
                item["content"],
                MAX_HISTORY_MESSAGE_CHARS,
            )

        # Tool-call payloads can also become large.
        if "tool_calls" in item:
            calls = []
            for call in item.get("tool_calls") or []:
                call = dict(call)
                function = dict(call.get("function") or {})

                if "arguments" in function:
                    function["arguments"] = _trim(
                        function["arguments"],
                        2500,
                    )

                call["function"] = function
                calls.append(call)

            item["tool_calls"] = calls

        cleaned.append(item)

    return cleaned


def _compact_memory():
    try:
        return _trim(get_memory_context(), MAX_MEMORY_CHARS)
    except Exception:
        return ""


def _system_prompt():
    return _trim(SYSTEM_PROMPT, MAX_SYSTEM_PROMPT_CHARS)


def _is_request_too_large(error):
    """Detect Groq/HTTP 413 responses without relying on one exact message."""
    text = str(error).lower()
    return (
        "413" in text
        or "request entity too large" in text
        or "request too large" in text
        or "payload too large" in text
    )


def _safe_error_message(error):
    text = str(error).strip()
    if _is_request_too_large(error):
        return (
            "The request was too large for the AI service. "
            "I reduced the request size automatically. Please try again."
        )
    return text


class NovaAgent:
    def __init__(self, status_callback=None):
        if not GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is missing. Add it to .env"
            )

        self.client = Groq(api_key=GROQ_API_KEY)
        self.status = status_callback or (lambda x: None)
        self.history = []

    def schemas(self):
        """Build compact tool schemas for local tool calls."""
        schemas = []

        for name, tool in LOCAL_TOOLS.items():
            description = _trim(
                tool.get("description", ""),
                900,
            )

            schema = tool.get("schema") or {
                "type": "object",
                "properties": {},
            }

            schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": description,
                        "parameters": schema,
                    },
                }
            )

        return schemas

    def _local_messages(self, text):
        return [
            {
                "role": "system",
                "content": _system_prompt(),
            },
            {
                "role": "system",
                "content": "Saved memory:\n" + _compact_memory(),
            },
            *_clean_history(self.history),
            {
                "role": "user",
                "content": _trim(text, MAX_USER_CHARS),
            },
        ]

    def local(self, text):
        messages = self._local_messages(text)

        for _ in range(6):
            try:
                response = self.client.chat.completions.create(
                    model=LOCAL_AGENT_MODEL,
                    messages=messages,
                    tools=self.schemas(),
                    tool_choice="auto",
                    temperature=0.2,
                )

                message = response.choices[0].message
                calls = getattr(message, "tool_calls", None)

                if not calls:
                    answer = message.content or "Done."

                    self.history.extend(
                        [
                            {
                                "role": "user",
                                "content": _trim(
                                    text,
                                    MAX_HISTORY_MESSAGE_CHARS,
                                ),
                            },
                            {
                                "role": "assistant",
                                "content": _trim(
                                    answer,
                                    MAX_HISTORY_MESSAGE_CHARS,
                                ),
                            },
                        ]
                    )

                    self.history = _clean_history(self.history)
                    return answer

                # Preserve the assistant tool-call message exactly as needed
                # by Groq, but keep argument strings bounded.
                assistant_message = message.model_dump(
                    exclude_none=True
                )

                if "content" in assistant_message:
                    assistant_message["content"] = _trim(
                        assistant_message["content"] or "",
                        MAX_HISTORY_MESSAGE_CHARS,
                    )

                messages.append(assistant_message)

                for call in calls:
                    name = call.function.name

                    try:
                        args = json.loads(
                            call.function.arguments or "{}"
                        )
                    except Exception:
                        args = {}

                    self.status("EXECUTING: " + name)

                    try:
                        if name in LOCAL_TOOLS:
                            result = LOCAL_TOOLS[name]["function"](**args)
                        else:
                            result = "Unknown tool."
                    except Exception as error:
                        result = f"Tool error: {error}"

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call.id,
                            "content": _trim(
                                str(result),
                                MAX_TOOL_RESULT_CHARS,
                            ),
                        }
                    )

            except Exception as error:
                # One compact retry is useful when a long tool result or
                # accumulated message causes an oversized local request.
                if _is_request_too_large(error):
                    messages = [
                        {
                            "role": "system",
                            "content": _trim(
                                _system_prompt(),
                                5000,
                            ),
                        },
                        {
                            "role": "user",
                            "content": _trim(
                                text,
                                4000,
                            ),
                        },
                    ]

                    try:
                        response = self.client.chat.completions.create(
                            model=LOCAL_AGENT_MODEL,
                            messages=messages,
                            temperature=0.2,
                        )

                        answer = (
                            response.choices[0].message.content
                            or "Done."
                        )

                        self.history.extend(
                            [
                                {
                                    "role": "user",
                                    "content": _trim(
                                        text,
                                        MAX_HISTORY_MESSAGE_CHARS,
                                    ),
                                },
                                {
                                    "role": "assistant",
                                    "content": _trim(
                                        answer,
                                        MAX_HISTORY_MESSAGE_CHARS,
                                    ),
                                },
                            ]
                        )
                        self.history = _clean_history(self.history)
                        return answer

                    except Exception as retry_error:
                        return (
                            "The AI request is still too large. "
                            "Please try a shorter request."
                        )

                return f"Tool/agent error: {_safe_error_message(error)}"

        return "I reached the local action limit for this request."

    def compound(self, text):
        """
        Research mode without Groq Compound.

        Groq's Compound endpoint is returning HTTP 413 even for a minimal
        one-message request on this setup. Use GPT-OSS 120B with Groq's
        built-in browser_search tool instead. This keeps research requests
        small while still providing current web information.
        """
        self.status("ONLINE WEB/RESEARCH MODE")

        user_request = _trim(text, 6000)

        try:
            response = self.client.chat.completions.create(
                model=RESEARCH_API_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are NOVA, a helpful desktop assistant. "
                            "For questions about current events, news, "
                            "prices, weather, or other time-sensitive facts, "
                            "use the browser search tool. "
                            "Give a concise answer and include source "
                            "references/citations when available."
                        ),
                    },
                    {
                        "role": "user",
                        "content": user_request,
                    },
                ],
                tools=[
                    {
                        "type": "browser_search",
                    }
                ],
                tool_choice="auto",
                reasoning_effort="low",
            )

            answer = response.choices[0].message.content
            return answer or "I couldn't produce a response."

        except Exception as error:
            if _is_request_too_large(error):
                return (
                    "Groq is rejecting the web-search request itself with "
                    "HTTP 413. The request is already compact and NOVA is "
                    "using GPT-OSS 120B with browser search instead of "
                    "Compound. Please check the Groq API service/account "
                    "configuration or try the same request with a newly "
                    "generated API key."
                )

            return f"I ran into a research error: {_safe_error_message(error)}"

    def run(self, text):
        text = str(text or "").strip()
        low = text.lower()

        if not text:
            return "Please give me a task."

        if low.startswith("remember that "):
            return remember(text[14:].strip())

        markers = (
            "search the web",
            "search online",
            "latest",
            "today's news",
            "todays news",
            "current news",
            "look up",
            "recent",
            "browse the web",
            "find online",
            "current price",
            "current weather",
            "what happened",
            "news today",
            "news right now",
        )

        return (
            self.compound(text)
            if any(marker in low for marker in markers)
            else self.local(text)
        )
