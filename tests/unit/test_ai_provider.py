import json
from dataclasses import replace

import httpx
import pytest

from app.domain.article import Article, VerificationStatus
from app.settings import Settings
from app.summarization.ai_provider import OptionalAISummaryProvider


def _article(url: str = "https://example.com/a") -> Article:
    return Article(
        original_headline="China announces export controls",
        original_url=url,
        canonical_url=url,
        source_name="Reuters",
        extracted_content=(
            "China announced new export controls. Officials said details remain limited."
        ),
    )


def _settings(**kwargs) -> Settings:
    base = Settings.from_env()
    values = {
        "summary_provider": "ai",
        "ai_provider": "openrouter",
        "openrouter_api_key": "openrouter-key",
        "openrouter_model": "openrouter/free",
        "gemini_api_key": "gemini-key",
        "gemini_model": "gemini-2.5-flash",
    }
    values.update(kwargs)
    return replace(base, **values)


def _json_content(summary: str = "China announced new export controls.") -> str:
    return f"""
{{
  "summary": "{summary}",
  "why_it_matters": "The move may affect supply chains and diplomatic positioning.",
  "editorial_angle": "Watch for official details and responses from trading partners.",
  "verification_status": "SINGLE_SOURCE"
}}
"""


@pytest.mark.asyncio
async def test_openrouter_success_returns_structured_summary():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/chat/completions"
        body = json.loads(request.content)
        assert body["max_tokens"] == 1000
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": _json_content()}}]},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OptionalAISummaryProvider(_settings(), client)

    summary = await provider.summarize(_article())

    assert summary.provider == "openrouter:openrouter/free"
    assert summary.summary.startswith("China announced")
    assert summary.verification_status == VerificationStatus.SINGLE_SOURCE
    await client.aclose()


@pytest.mark.asyncio
async def test_gemini_success_returns_structured_summary():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1beta/models/gemini-2.5-flash:generateContent"
        return httpx.Response(
            200,
            json={
                "candidates": [{"content": {"parts": [{"text": _json_content("Gemini summary.")}]}}]
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OptionalAISummaryProvider(
        _settings(ai_provider="gemini"), clients={"gemini": client}
    )

    summary = await provider.summarize(_article())

    assert summary.provider == "gemini:gemini-2.5-flash"
    assert summary.summary == "Gemini summary."
    await client.aclose()


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [404, 429])
async def test_single_provider_limit_or_model_error_falls_back(status_code):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json={"error": "not available"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OptionalAISummaryProvider(_settings(), client)

    summary = await provider.summarize(_article())

    assert summary.provider == "deterministic-fallback:ai-providers-failed"
    assert "China announced new export controls." in summary.summary
    await client.aclose()


@pytest.mark.asyncio
async def test_failover_router_tries_openrouter_then_gemini_on_429():
    calls: list[str] = []

    def openrouter_handler(request: httpx.Request) -> httpx.Response:
        calls.append("openrouter")
        return httpx.Response(429, json={"error": "limit"})

    def gemini_handler(request: httpx.Request) -> httpx.Response:
        calls.append("gemini")
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {"content": {"parts": [{"text": _json_content("Gemini fallback.")}]}}
                ]
            },
        )

    openrouter_client = httpx.AsyncClient(transport=httpx.MockTransport(openrouter_handler))
    gemini_client = httpx.AsyncClient(transport=httpx.MockTransport(gemini_handler))
    provider = OptionalAISummaryProvider(
        _settings(ai_provider="failover", ai_provider_order="openrouter,gemini"),
        clients={"openrouter": openrouter_client, "gemini": gemini_client},
    )

    summary = await provider.summarize(_article())

    assert summary.provider == "gemini:gemini-2.5-flash"
    assert summary.summary == "Gemini fallback."
    assert calls == ["openrouter", "gemini"]
    await openrouter_client.aclose()
    await gemini_client.aclose()


@pytest.mark.asyncio
async def test_missing_keys_falls_back_without_request():
    provider = OptionalAISummaryProvider(
        _settings(
            ai_provider="failover",
            openrouter_api_key=None,
            gemini_api_key=None,
        )
    )

    summary = await provider.summarize(_article())

    assert summary.provider == "deterministic-fallback:ai-providers-failed"


@pytest.mark.asyncio
async def test_bad_json_falls_back():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "not json"}}]},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OptionalAISummaryProvider(_settings(), client)

    summary = await provider.summarize(_article())

    assert summary.provider == "deterministic-fallback:ai-providers-failed"
    await client.aclose()


def test_failover_order_defaults_openrouter_then_gemini():
    provider = OptionalAISummaryProvider(
        _settings(ai_provider="failover", ai_provider_order="openrouter,gemini")
    )

    assert [backend.name for backend in provider.backends] == ["openrouter", "gemini"]
