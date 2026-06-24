"""OpenAI LLM adapter using the openai Python SDK."""

import json
import logging
from typing import Any

from openai import AsyncOpenAI

from order_shared.adapters.base import LLMAdapter, LLMResponse

logger = logging.getLogger(__name__)


class OpenAILLMAdapter(LLMAdapter):
    """LLM adapter calling OpenAI API directly.

    Uses gpt-4o for extraction and gpt-4o-mini for classification.
    """

    def __init__(
        self,
        api_key: str,
        default_model: str = "gpt-4o",
        classification_model: str = "gpt-4o-mini",
    ) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
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

        oai_messages: list[dict[str, str]] = []
        if system:
            oai_messages.append({"role": "system", "content": system})
        oai_messages.extend(messages)

        response = await self._client.chat.completions.create(
            model=model,
            messages=oai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = response.choices[0].message.content or ""
        usage = response.usage

        result = LLMResponse(
            content=content,
            model=response.model,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            stop_reason=response.choices[0].finish_reason,
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
            f'Respond with a JSON object: {{"category": "<chosen_category>", '
            f'"confidence": <0-100>}}. Nothing else.'
        )

        response = await self.complete(
            messages=[{"role": "user", "content": text}],
            system=classification_system,
            model=self._classification_model,
            temperature=0,
            max_tokens=256,
        )

        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            parsed = json.loads(content)
            category = parsed["category"]
            confidence = float(parsed["confidence"])
            if category not in categories:
                logger.warning(f"LLM returned unknown category '{category}', defaulting to first")
                category = categories[0]
                confidence = 0.0
            return category, confidence
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse classification response: {e}")
            return categories[0], 0.0
