"""Local LLM adapter using Anthropic API directly."""

import json
import logging
from typing import Any

from anthropic import AsyncAnthropic

from order_shared.adapters.base import LLMAdapter, LLMResponse

logger = logging.getLogger(__name__)


class AnthropicLLMAdapter(LLMAdapter):
    """LLM adapter calling Anthropic API directly for local development.

    Uses claude-sonnet-4-20250514 for extraction and claude-3-5-haiku for classification.
    """

    def __init__(
        self,
        api_key: str,
        default_model: str = "claude-sonnet-4-20250514",
        classification_model: str = "claude-3-haiku-20240307",
    ) -> None:
        self._client = AsyncAnthropic(api_key=api_key)
        self._default_model = default_model
        self._classification_model = classification_model

    async def complete(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
        model: str | None = None,
        temperature: float = 0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        model = model or self._default_model
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system:
            kwargs["system"] = system

        response = await self._client.messages.create(**kwargs)

        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        result = LLMResponse(
            content=content,
            model=response.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            stop_reason=response.stop_reason,
        )
        logger.info(
            f"LLM completion: model={model}, "
            f"tokens_in={result.input_tokens}, tokens_out={result.output_tokens}"
        )
        return result

    async def classify(
        self,
        text: str,
        categories: list[str],
        system: str | None = None,
    ) -> tuple[str, float]:
        categories_str = ", ".join(categories)
        classification_system = system or (
            f"You are a text classifier. Classify the following text into exactly one of "
            f"these categories: {categories_str}. "
            f"Respond with a JSON object: {{\"category\": \"<chosen_category>\", "
            f"\"confidence\": <0-100>}}. Nothing else."
        )

        response = await self.complete(
            messages=[{"role": "user", "content": text}],
            system=classification_system,
            model=self._classification_model,
            temperature=0,
            max_tokens=256,
        )

        try:
            parsed = json.loads(response.content)
            category = parsed["category"]
            confidence = float(parsed["confidence"])
            # Validate category is in the allowed list
            if category not in categories:
                logger.warning(f"LLM returned unknown category '{category}', defaulting to first")
                category = categories[0]
                confidence = 0.0
            return category, confidence
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse classification response: {e}")
            return categories[0], 0.0
