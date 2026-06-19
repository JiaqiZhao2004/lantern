import json

import httpx
import pytest

from src.infrastructure.llm.client import (
    LLMMessage,
    LLMProviderError,
    OpenAILLMClient,
    NotConfiguredLLMClient,
    get_llm_client,
)


def test_not_configured_client_raises_provider_error():
    client = NotConfiguredLLMClient()

    with pytest.raises(LLMProviderError, match="not configured"):
        client.generate_structured(
            messages=[LLMMessage(role="user", content="hello")],
            schema_name="test_schema",
            json_schema={"type": "object"},
        )


def test_openai_client_posts_structured_output_request_and_parses_json():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers["Authorization"]
        captured["payload"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "type": "named_query_candidate",
                                    "name": "Spending by category",
                                    "candidate": {
                                        "sql_query": "SELECT 1",
                                        "chart_type": "bar",
                                    },
                                }
                            )
                        }
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    client = OpenAILLMClient(
        api_key="test-key",
        model="test-model",
        base_url="https://example.test/v1",
        client_factory=lambda: httpx.Client(transport=transport),
    )
    result = client.generate_structured(
        messages=[
            LLMMessage(role="system", content="system prompt"),
            LLMMessage(role="user", content="show spending"),
        ],
        schema_name="named_query_generation",
        json_schema={"type": "object"},
    )

    assert captured["url"] == "https://example.test/v1/chat/completions"
    assert captured["authorization"] == "Bearer test-key"
    assert captured["payload"]["model"] == "test-model"
    assert captured["payload"]["messages"][0] == {
        "role": "system",
        "content": "system prompt",
    }
    assert captured["payload"]["response_format"]["json_schema"]["name"] == (
        "named_query_generation"
    )
    assert result["name"] == "Spending by category"


def test_openai_client_surfaces_provider_error_message():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            401,
            json={"error": {"message": "Incorrect API key provided"}},
        )
    )
    client = OpenAILLMClient(
        api_key="bad-key",
        model="test-model",
        base_url="https://example.test/v1",
        client_factory=lambda: httpx.Client(transport=transport),
    )
    with pytest.raises(LLMProviderError, match="Incorrect API key provided"):
        client.generate_structured(
            messages=[LLMMessage(role="user", content="hello")],
            schema_name="test_schema",
            json_schema={"type": "object"},
        )


def test_get_llm_client_returns_openai_client_when_api_key_present(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "configured-key")
    monkeypatch.setenv("OPENAI_MODEL", "configured-model")
    get_llm_client.cache_clear()

    client = get_llm_client()

    assert isinstance(client, OpenAILLMClient)
    assert client.api_key == "configured-key"
    assert client.model == "configured-model"

    get_llm_client.cache_clear()


def test_get_llm_client_returns_not_configured_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    get_llm_client.cache_clear()

    client = get_llm_client()

    assert isinstance(client, NotConfiguredLLMClient)

    get_llm_client.cache_clear()
