from anthropic import AsyncAnthropic
from anthropic.types import TextBlock
from loguru import logger

from src.agents.llm.base import LLMClient, LLMResponse


class AnthropicClient(LLMClient):
    """Anthropic Claude API client."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-5-20250929",
    ):
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        **kwargs,
    ) -> LLMResponse:
        try:
            response = await self._client.messages.create(
                model=kwargs.get("model", self._model),
                max_tokens=kwargs.get("max_tokens", 2000),
                system=system or "",
                messages=[{"role": "user", "content": prompt}],
            )

            content = ""
            for block in response.content:
                if isinstance(block, TextBlock):
                    content = block.text
                    break

            return LLMResponse(
                content=content,
                model=response.model,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
            )
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

    def get_model(self) -> str:
        return self._model
