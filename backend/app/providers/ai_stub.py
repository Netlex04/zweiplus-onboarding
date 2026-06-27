"""Deterministic offline chat model for tests and local smoke runs.

``StubChatModel`` is a minimal LangChain ``BaseChatModel`` that performs **no**
network calls. It inspects the incoming messages and returns a deterministic
response:

- If the prompt asks for JSON (it contains the marker the provider injects for
  ``structured`` calls), it returns a valid JSON object that satisfies the AI
  suggestion / validation schemas used by the endpoints.
- Otherwise it echoes a short, deterministic chat reply.

Tests inject this via ``get_ai_provider(chat_model=StubChatModel())`` or the
``AI_USE_STUB`` settings flag. It is intentionally not wired into the product
provider selection except behind that explicit flag.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any, Optional

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

# Marker the provider injects into structured prompts (German instruction text).
_JSON_MARKER = "JSON-Objekt"


class StubChatModel(BaseChatModel):
    """Deterministic, offline chat model. No server, no key required."""

    # Optional override so a test can force a specific reply if needed.
    fixed_reply: str | None = None

    @property
    def _llm_type(self) -> str:
        return "zweiplus-stub"

    def _generate(
        self,
        messages: Sequence[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        content = self._respond(list(messages))
        message = AIMessage(content=content)
        return ChatResult(generations=[ChatGeneration(message=message)])

    def _respond(self, messages: list[BaseMessage]) -> str:
        if self.fixed_reply is not None:
            return self.fixed_reply

        last = ""
        for msg in reversed(messages):
            if getattr(msg, "type", None) == "human":
                last = str(msg.content)
                break

        if _JSON_MARKER in last:
            return json.dumps(self._structured_payload(last), ensure_ascii=False)

        return (
            "Hinweis (KI, unverbindlich): Bitte beachten Sie die Datenschutz-"
            "Leitlinien. Diese Antwort ist ein Vorschlag und muss geprüft werden."
        )

    def _structured_payload(self, prompt: str) -> dict:
        """Return a deterministic payload matching whichever schema is requested.

        The provider embeds the JSON schema in the prompt; we branch on its
        distinctive field names to produce a schema-conforming object.
        """
        # Validation schema has a "checks"/"issues"/"passed" shape.
        if '"checks"' in prompt or '"passed"' in prompt:
            return {
                "passed": True,
                "checks": [
                    {
                        "question": "used_software",
                        "ok": True,
                        "note": "Angabe ist plausibel und ausreichend konkret.",
                    }
                ],
                "issues": [],
            }
        # Suggestion schema has "suggestionType"/"proposedValue".
        return {
            "suggestionType": "answer_proposal",
            "proposedValue": "Microsoft 365",
            "confidence": 0.6,
            "requiresReview": True,
            "openQuestions": [
                "Bitte bestätigen Sie, ob weitere Systeme im Einsatz sind.",
            ],
        }
