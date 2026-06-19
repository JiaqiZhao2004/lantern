from dataclasses import dataclass
from functools import lru_cache
import json
import os
from typing import Any, Protocol

import httpx


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str


class LLMProviderError(Exception):
    pass


class LLMClient(Protocol):
    def generate_structured(
        self,
        *,
        messages: list[LLMMessage],
        schema_name: str,
        json_schema: dict[str, Any],
    ) -> dict[str, Any]:
        ...


class NotConfiguredLLMClient:
    def generate_structured(
        self,
        *,
        messages: list[LLMMessage],
        schema_name: str,
        json_schema: dict[str, Any],
    ) -> dict[str, Any]:
        raise LLMProviderError("LLM provider is not configured")


class OpenAILLMClient:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: float = 30.0,
        client_factory: Any | None = None,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.client_factory = client_factory or self._default_client_factory

    def generate_structured(
        self,
        *,
        messages: list[LLMMessage],
        schema_name: str,
        json_schema: dict[str, Any],
    ) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": [
                {"role": message.role, "content": message.content} for message in messages
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": json_schema,
                },
            },
        }

        try:
            with self.client_factory() as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise LLMProviderError("OpenAI request failed") from exc

        if response.status_code >= 400:
            raise LLMProviderError(_format_openai_error(response))

        try:
            body = response.json()
        except ValueError as exc:
            raise LLMProviderError("OpenAI returned invalid JSON") from exc

        content = _extract_message_content(body)
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise LLMProviderError("OpenAI returned non-JSON structured output") from exc

    def _default_client_factory(self) -> httpx.Client:
        return httpx.Client(timeout=self.timeout_seconds)


def _extract_message_content(body: dict[str, Any]) -> str:
    choices = body.get("choices")
    if not isinstance(choices, list) or not choices:
        raise LLMProviderError("OpenAI returned no choices")

    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise LLMProviderError("OpenAI returned an invalid message payload")

    refusal = message.get("refusal")
    if isinstance(refusal, str) and refusal.strip():
        raise LLMProviderError(refusal.strip())

    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content

    raise LLMProviderError("OpenAI returned empty content")


def _format_openai_error(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return f"OpenAI request failed with status {response.status_code}"

    error = body.get("error")
    if isinstance(error, dict):
        message = error.get("message")
        if isinstance(message, str) and message.strip():
            return f"OpenAI request failed: {message.strip()}"

    return f"OpenAI request failed with status {response.status_code}"


@lru_cache
def get_llm_client() -> LLMClient:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    if not api_key:
        return NotConfiguredLLMClient()

    return OpenAILLMClient(
        api_key=api_key,
        model=model,
        base_url=base_url,
    )
