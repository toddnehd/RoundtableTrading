from src.agents.llm.anthropic_client import AnthropicClient
from src.agents.llm.base import LLMClient
from src.agents.llm.ollama_client import OllamaClient
from src.agents.llm.openai_client import OpenAIClient
from src.config import settings


class LLMClientFactory:
    """Factory for creating LLM clients."""

    @staticmethod
    def create(
        provider: str = "anthropic",
        model: str | None = None,
    ) -> LLMClient:
        """Create an LLM client for the specified provider.

        Args:
            provider: Provider name ("anthropic", "openai", "ollama").
            model: Optional model override.

        Returns:
            Configured LLMClient instance.

        Raises:
            ValueError: If provider is unsupported or API key is missing.
        """
        if provider == "anthropic":
            if not settings.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY not configured")
            return AnthropicClient(
                api_key=settings.anthropic_api_key,
                model=model or "claude-sonnet-4-5-20250929",
            )

        if provider == "openai":
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            return OpenAIClient(
                api_key=settings.openai_api_key,
                model=model or "gpt-4o",
            )

        if provider == "ollama":
            return OllamaClient(
                base_url=settings.ollama_base_url,
                model=model or settings.ollama_model,
            )

        raise ValueError(f"Unsupported provider: {provider}")


def get_llm_client(provider: str = "anthropic", model: str | None = None) -> LLMClient:
    """Convenience function to get an LLM client."""
    return LLMClientFactory.create(provider, model)
