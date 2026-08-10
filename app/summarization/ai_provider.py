from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from app.domain.article import Article, ArticleSummary, VerificationStatus
from app.settings import Settings
from app.summarization.deterministic import DeterministicSummaryProvider

logger = logging.getLogger(__name__)

VALID_VERIFICATION_STATUSES = {status.value for status in VerificationStatus}
RETRYABLE_STATUS_CODES = {400, 401, 402, 403, 404, 408, 409, 422, 429}


class AIProviderError(RuntimeError):
    pass


class AISummaryBackend(Protocol):
    name: str

    async def generate(self, article: Article) -> str: ...


@dataclass(slots=True)
class SummaryPromptBuilder:
    language: str

    def system_prompt(self) -> str:
        return (
            "You write concise geopolitical news summaries for Lenswire. "
            "Use only the supplied article text. Do not invent facts. Preserve uncertainty. "
            "Do not claim verification. Return only valid JSON with keys: summary, "
            "why_it_matters, editorial_angle, verification_status."
        )

    def article_prompt(self, article: Article) -> str:
        content = article.extracted_content or article.raw_description or article.original_headline
        return (
            f"Output language: {self.language}\n"
            f"Headline: {article.original_headline}\n"
            f"Source: {article.source_name or 'Unknown'}\n"
            f"URL: {article.canonical_url}\n"
            f"Article text:\n{content[:7000]}\n\n"
            "Return JSON only. Use 2-4 sentences for summary. "
            "Use verification_status SINGLE_SOURCE unless the supplied text clearly indicates "
            "multiple independent sources or a primary source."
        )


class OpenRouterSummaryBackend:
    name = "openrouter"

    def __init__(
        self,
        api_key: str | None,
        base_url: str,
        model: str,
        timeout: float,
        prompt_builder: SummaryPromptBuilder,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.prompt_builder = prompt_builder
        self._client = client

    async def generate(self, article: Article) -> str:
        if not self.api_key:
            raise AIProviderError("missing OpenRouter API key")

        client = self._client or httpx.AsyncClient(timeout=self.timeout)
        close_client = self._client is None
        try:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://factlensbd.com",
                    "X-OpenRouter-Title": "Lenswire",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": self.prompt_builder.system_prompt()},
                        {"role": "user", "content": self.prompt_builder.article_prompt(article)},
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1000,
                },
            )
            if response.status_code in RETRYABLE_STATUS_CODES:
                raise AIProviderError(f"OpenRouter returned HTTP {response.status_code}")
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise AIProviderError("OpenRouter returned empty content")
            return content
        finally:
            if close_client:
                await client.aclose()


class GeminiSummaryBackend:
    name = "gemini"

    def __init__(
        self,
        api_key: str | None,
        base_url: str,
        model: str,
        timeout: float,
        prompt_builder: SummaryPromptBuilder,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model.removeprefix("models/")
        self.timeout = timeout
        self.prompt_builder = prompt_builder
        self._client = client

    async def generate(self, article: Article) -> str:
        if not self.api_key:
            raise AIProviderError("missing Gemini API key")

        client = self._client or httpx.AsyncClient(timeout=self.timeout)
        close_client = self._client is None
        try:
            response = await client.post(
                f"{self.base_url}/models/{self.model}:generateContent",
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.api_key,
                },
                json={
                    "systemInstruction": {"parts": [{"text": self.prompt_builder.system_prompt()}]},
                    "contents": [
                        {
                            "role": "user",
                            "parts": [{"text": self.prompt_builder.article_prompt(article)}],
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.2,
                        "maxOutputTokens": 600,
                        "responseMimeType": "application/json",
                    },
                },
            )
            if response.status_code in RETRYABLE_STATUS_CODES:
                raise AIProviderError(f"Gemini returned HTTP {response.status_code}")
            response.raise_for_status()
            data = response.json()
            parts = data["candidates"][0]["content"]["parts"]
            text = "".join(str(part.get("text", "")) for part in parts).strip()
            if not text:
                raise AIProviderError("Gemini returned empty content")
            return text
        finally:
            if close_client:
                await client.aclose()


class AISummaryProviderFactory:
    def __init__(
        self,
        settings: Settings,
        clients: dict[str, httpx.AsyncClient] | None = None,
    ) -> None:
        self.settings = settings
        self.clients = clients or {}
        self.prompt_builder = SummaryPromptBuilder(settings.summary_output_language)

    def create(self) -> list[AISummaryBackend]:
        providers: dict[str, AISummaryBackend] = {
            "openrouter": OpenRouterSummaryBackend(
                self.settings.openrouter_api_key,
                self.settings.openrouter_api_base_url,
                self.settings.openrouter_model,
                self.settings.ai_request_timeout_seconds,
                self.prompt_builder,
                self.clients.get("openrouter"),
            ),
            "gemini": GeminiSummaryBackend(
                self.settings.gemini_api_key,
                self.settings.gemini_api_base_url,
                self.settings.gemini_model,
                self.settings.ai_request_timeout_seconds,
                self.prompt_builder,
                self.clients.get("gemini"),
            ),
        }

        provider_mode = self.settings.ai_provider.lower().strip()
        if provider_mode in providers:
            return [providers[provider_mode]]
        if provider_mode == "failover":
            return [providers[name] for name in self._ordered_names() if name in providers]
        return [providers["openrouter"], providers["gemini"]]

    def _ordered_names(self) -> list[str]:
        names = [
            name.strip().lower()
            for name in self.settings.ai_provider_order.split(",")
            if name.strip()
        ]
        if not names:
            return ["openrouter", "gemini"]
        return names


class OptionalAISummaryProvider:
    """Routes AI summaries across configured providers with deterministic fallback."""

    name = "ai-router"

    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient | None = None,
        clients: dict[str, httpx.AsyncClient] | None = None,
    ) -> None:
        self.settings = settings
        self.language = settings.summary_output_language
        if client is not None and clients is None:
            clients = {"openrouter": client}
        self.backends = AISummaryProviderFactory(settings, clients).create()
        self._fallback = DeterministicSummaryProvider(self.language)

    async def summarize(self, article: Article) -> ArticleSummary:
        errors: list[str] = []
        for backend in self.backends:
            try:
                parsed = parse_summary_json(await backend.generate(article))
                model = self._model_for_backend(backend.name)
                return ArticleSummary(
                    article_id=None,
                    summary=parsed["summary"],
                    why_it_matters=parsed["why_it_matters"],
                    editorial_angle=parsed["editorial_angle"],
                    verification_status=VerificationStatus(parsed["verification_status"]),
                    language=self.language,
                    provider=f"{backend.name}:{model}",
                    status="SUCCESS",
                )
            except Exception as exc:
                errors.append(f"{backend.name}: {exc}")
                logger.warning(
                    "ai provider failed; trying next provider",
                    extra={
                        "provider": backend.name,
                        "article_url": article.canonical_url,
                        "error": str(exc),
                    },
                )

        summary = await self._fallback.summarize(article)
        summary.provider = "deterministic-fallback:ai-providers-failed"
        logger.warning(
            "all ai providers failed; using deterministic fallback",
            extra={"article_url": article.canonical_url, "errors": " | ".join(errors)},
        )
        return summary

    def _model_for_backend(self, name: str) -> str:
        if name == "gemini":
            return self.settings.gemini_model
        return self.settings.openrouter_model


def parse_summary_json(content: str) -> dict[str, str]:
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL)
    raw = match.group(1) if match else content
    data: Any = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("AI summary response must be a JSON object")

    required = {
        "summary",
        "why_it_matters",
        "editorial_angle",
        "verification_status",
    }
    missing = required - set(data)
    if missing:
        raise ValueError(f"AI summary missing fields: {sorted(missing)}")

    parsed = {key: str(data[key]).strip() for key in required}
    if parsed["verification_status"] not in VALID_VERIFICATION_STATUSES:
        parsed["verification_status"] = VerificationStatus.SINGLE_SOURCE.value
    for key in ("summary", "why_it_matters", "editorial_angle"):
        if not parsed[key]:
            raise ValueError(f"AI summary field is empty: {key}")
    return parsed
