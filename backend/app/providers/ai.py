"""AI provider seam (Architektur §7, §8).

``AiProvider`` is an ABC so the concrete LLM backend is swappable. The single
product implementation is :class:`LangChainAiProvider`, which wraps a LangChain
``ChatOpenAI`` configured against any **OpenAI-compatible** chat-completions API
(``AI_BASE_URL``). This makes OpenAI, Ollama, LM Studio and vLLM interchangeable.

Design notes
------------
- The underlying LangChain ``BaseChatModel`` is **injectable** (DI): production
  builds a ``ChatOpenAI`` from settings, tests inject :class:`StubChatModel`.
- ``structured`` prefers LangChain native structured output
  (``with_structured_output``) but falls back to robust JSON parsing of the raw
  text, so endpoints that cannot do tool/function calling still work. This also
  lets the deterministic test stub work without implementing tool-calling.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel

from app.config import Settings, get_settings


class AiProvider(ABC):
    """Abstract LLM access used by the AI service layer."""

    @abstractmethod
    def chat(self, system: str, messages: list[dict]) -> str:
        """Free-form chat. ``messages`` are ``{"role", "content"}`` dicts
        (roles ``user``/``assistant``). Returns the assistant reply text."""

    @abstractmethod
    def structured(
        self, system: str, prompt: str, schema: dict | type[BaseModel]
    ) -> dict:
        """Schema-guided JSON output. ``schema`` may be a Pydantic model class
        or a JSON schema dict. Returns a plain ``dict`` (Backend validates it
        before persistence — FR-AI-007)."""


def _to_lc_messages(system: str, messages: list[dict]):
    lc: list[Any] = []
    if system:
        lc.append(SystemMessage(content=system))
    for msg in messages:
        role = (msg.get("role") or "user").lower()
        content = msg.get("content") or ""
        if role == "assistant":
            lc.append(AIMessage(content=content))
        else:
            lc.append(HumanMessage(content=content))
    return lc


def _extract_json(text: str) -> dict:
    """Parse the first JSON object found in ``text`` (robust fallback)."""
    text = text.strip()
    try:
        loaded = json.loads(text)
        if isinstance(loaded, dict):
            return loaded
    except json.JSONDecodeError:
        pass
    # Strip ```json fences and grab the outermost {...} block.
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            loaded = json.loads(match.group(0))
            if isinstance(loaded, dict):
                return loaded
        except json.JSONDecodeError:
            pass
    raise ValueError("KI-Antwort enthielt kein gültiges JSON")


def _schema_hint(schema: dict | type[BaseModel]) -> str:
    if isinstance(schema, type) and issubclass(schema, BaseModel):
        json_schema = schema.model_json_schema()
    else:
        json_schema = schema
    return json.dumps(json_schema, ensure_ascii=False)


class LangChainAiProvider(AiProvider):
    """Product provider: LangChain ChatOpenAI against an OpenAI-compatible API."""

    def __init__(self, chat_model: BaseChatModel) -> None:
        # The chat model is injected so tests can swap in a deterministic stub.
        self._model = chat_model

    def chat(self, system: str, messages: list[dict]) -> str:
        result = self._model.invoke(_to_lc_messages(system, messages))
        content = getattr(result, "content", result)
        return content if isinstance(content, str) else str(content)

    def structured(
        self, system: str, prompt: str, schema: dict | type[BaseModel]
    ) -> dict:
        # Always instruct the model to emit JSON matching the schema. This is
        # what makes the JSON-parse fallback (and the test stub) work even when
        # the endpoint has no tool/function-calling support.
        guided = (
            f"{prompt}\n\n"
            "Antworte ausschließlich mit einem einzigen JSON-Objekt, das exakt "
            "diesem JSON-Schema entspricht (keine Erklärungen, kein Markdown):\n"
            f"{_schema_hint(schema)}"
        )
        messages = _to_lc_messages(system, [{"role": "user", "content": guided}])

        # Preferred path: native structured output (function/json-schema mode).
        try:
            structured_llm = self._model.with_structured_output(schema)
            out = structured_llm.invoke(messages)
            if isinstance(out, BaseModel):
                return out.model_dump()
            if isinstance(out, dict):
                return out
        except Exception:
            # Fall through to robust JSON parsing of the raw text response.
            pass

        raw = self._model.invoke(messages)
        text = getattr(raw, "content", raw)
        return _extract_json(text if isinstance(text, str) else str(text))


def build_chat_model(settings: Settings) -> BaseChatModel:
    """Construct the production ChatOpenAI from settings."""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        base_url=settings.ai_base_url,
        api_key=settings.ai_api_key,
        model=settings.ai_model,
        temperature=0,
    )


def get_ai_provider(
    settings: Settings | None = None,
    chat_model: BaseChatModel | None = None,
) -> AiProvider:
    """Build the product AI provider.

    ``chat_model`` may be injected (tests pass a :class:`StubChatModel`); when a
    ``AI_USE_STUB`` flag is set the stub is used for a local, key-free smoke test.
    """
    settings = settings or get_settings()
    if chat_model is None:
        if settings.ai_use_stub:
            from app.providers.ai_stub import StubChatModel

            chat_model = StubChatModel()
        else:
            chat_model = build_chat_model(settings)
    return LangChainAiProvider(chat_model)
