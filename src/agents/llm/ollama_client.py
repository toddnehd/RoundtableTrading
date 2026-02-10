import httpx
from loguru import logger

from src.agents.llm.base import LLMClient, LLMResponse


class OllamaClient(LLMClient):
    """Ollama local LLM client."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.1:8b",
    ):
        self._base_url = base_url
        self._model = model

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        **kwargs,
    ) -> LLMResponse:
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self._base_url}/api/chat",
                    json={
                        "model": kwargs.get("model", self._model),
                        "messages": messages,
                        "stream": False,
                    },
                    timeout=120.0,
                )
                response.raise_for_status()
                result = response.json()

            return LLMResponse(
                content=result["message"]["content"],
                model=self._model,
            )
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise

    def get_model(self) -> str:
        return self._model
