from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from anthropic.types import TextBlock

from src.agents.llm.anthropic_client import AnthropicClient
from src.agents.llm.base import LLMResponse
from src.agents.llm.factory import LLMClientFactory, get_llm_client
from src.agents.llm.ollama_client import OllamaClient
from src.agents.llm.openai_client import OpenAIClient


class TestLLMResponse:
    def test_create_response(self):
        response = LLMResponse(
            content="Hello, world!",
            model="test-model",
            usage={"input_tokens": 10, "output_tokens": 5},
        )

        assert response.content == "Hello, world!"
        assert response.model == "test-model"
        assert response.usage == {"input_tokens": 10, "output_tokens": 5}

    def test_create_response_without_usage(self):
        response = LLMResponse(content="Test", model="model")

        assert response.content == "Test"
        assert response.usage is None


class TestAnthropicClient:
    def test_get_model(self):
        client = AnthropicClient(api_key="test-key", model="claude-test")
        assert client.get_model() == "claude-test"

    async def test_generate(self):
        client = AnthropicClient(api_key="test-key")

        mock_text_block = TextBlock(type="text", text="Generated text")
        mock_response = MagicMock()
        mock_response.content = [mock_text_block]
        mock_response.model = "claude-sonnet-4-5-20250929"
        mock_response.usage = MagicMock(input_tokens=10, output_tokens=20)

        with patch.object(client._client.messages, "create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            result = await client.generate(prompt="Hello", system="Be helpful")

            assert result.content == "Generated text"
            assert result.model == "claude-sonnet-4-5-20250929"
            assert result.usage == {"input_tokens": 10, "output_tokens": 20}


class TestOpenAIClient:
    def test_get_model(self):
        client = OpenAIClient(api_key="test-key", model="gpt-test")
        assert client.get_model() == "gpt-test"

    async def test_generate(self):
        client = OpenAIClient(api_key="test-key")

        mock_message = MagicMock()
        mock_message.content = "Generated text"

        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.model = "gpt-4o"
        mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=20)

        with patch.object(
            client._client.chat.completions, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response

            result = await client.generate(prompt="Hello", system="Be helpful")

            assert result.content == "Generated text"
            assert result.model == "gpt-4o"
            assert result.usage == {"input_tokens": 10, "output_tokens": 20}


class TestOllamaClient:
    def test_get_model(self):
        client = OllamaClient(model="llama-test")
        assert client.get_model() == "llama-test"

    async def test_generate(self):
        client = OllamaClient()

        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Generated text"}}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            result = await client.generate(prompt="Hello", system="Be helpful")

            assert result.content == "Generated text"
            assert result.model == "llama3.1:8b"


class TestLLMClientFactory:
    def test_create_anthropic_client(self):
        with patch("src.agents.llm.factory.settings") as mock_settings:
            mock_settings.anthropic_api_key = "test-key"

            client = LLMClientFactory.create("anthropic")

            assert isinstance(client, AnthropicClient)

    def test_create_openai_client(self):
        with patch("src.agents.llm.factory.settings") as mock_settings:
            mock_settings.openai_api_key = "test-key"

            client = LLMClientFactory.create("openai")

            assert isinstance(client, OpenAIClient)

    def test_create_ollama_client(self):
        with patch("src.agents.llm.factory.settings") as mock_settings:
            mock_settings.ollama_base_url = "http://localhost:11434"
            mock_settings.ollama_model = "llama3.1:8b"

            client = LLMClientFactory.create("ollama")

            assert isinstance(client, OllamaClient)

    def test_create_unsupported_provider(self):
        with pytest.raises(ValueError, match="Unsupported provider"):
            LLMClientFactory.create("unsupported")

    def test_create_anthropic_without_api_key(self):
        with patch("src.agents.llm.factory.settings") as mock_settings:
            mock_settings.anthropic_api_key = ""

            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not configured"):
                LLMClientFactory.create("anthropic")

    def test_create_openai_without_api_key(self):
        with patch("src.agents.llm.factory.settings") as mock_settings:
            mock_settings.openai_api_key = ""

            with pytest.raises(ValueError, match="OPENAI_API_KEY not configured"):
                LLMClientFactory.create("openai")


class TestGetLLMClient:
    def test_get_llm_client(self):
        with patch("src.agents.llm.factory.settings") as mock_settings:
            mock_settings.anthropic_api_key = "test-key"

            client = get_llm_client("anthropic")

            assert isinstance(client, AnthropicClient)
