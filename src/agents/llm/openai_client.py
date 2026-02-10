from loguru import logger
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from src.agents.llm.base import LLMClient, LLMResponse


class OpenAIClient(LLMClient):
    """OpenAI GPT API client."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
    ):
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        **kwargs,
    ) -> LLMResponse:
        try:
            messages: list[ChatCompletionMessageParam] = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            response = await self._client.chat.completions.create(
                model=kwargs.get("model", self._model),
                max_tokens=kwargs.get("max_tokens", 2000),
                messages=messages,
            )

            usage = None
            if response.usage:
                usage = {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                }

            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=response.model,
                usage=usage,
            )
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    def get_model(self) -> str:
        return self._model
