from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Response from LLM API call.

    Attributes:
        content: Generated text content.
        model: Model identifier used for generation.
        usage: Token usage statistics (input_tokens, output_tokens).
    """

    content: str
    model: str
    usage: dict[str, int] | None = None


class LLMClient(ABC):
    """Abstract base class for LLM clients.

    All LLM provider implementations must inherit from this class
    and implement the generate() and get_model() methods.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate text from the LLM.

        Args:
            prompt: User prompt to send to the model.
            system: Optional system prompt for context/instructions.
            **kwargs: Additional provider-specific parameters.

        Returns:
            LLMResponse containing generated content and metadata.

        Raises:
            Exception: If API call fails.
        """
        pass

    @abstractmethod
    def get_model(self) -> str:
        """Get the current model identifier.

        Returns:
            Model name/identifier string.
        """
        pass
