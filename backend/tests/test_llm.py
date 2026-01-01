import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import os


@pytest.mark.asyncio
async def test_llm_handler_cerebras_call():
    with patch("ai.llm.Cerebras") as mock_cerebras_class, \
         patch.dict(os.environ, {"CEREBRAS_API_KEY": "test-key", "GEMINI_API_KEY": ""}):

        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Cerebras response"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_cerebras_class.return_value = mock_client

        # Import after patching
        from ai.llm import LLMHandler, ModelSize

        handler = LLMHandler()
        handler.cerebras_client = mock_client

        result = await handler._cerebras_call("test prompt", "test system", "llama3.1-8b")

        assert result == "Cerebras response"


@pytest.mark.asyncio
async def test_llm_handler_removes_think_tags():
    with patch("ai.llm.Cerebras") as mock_cerebras_class, \
         patch.dict(os.environ, {"CEREBRAS_API_KEY": "test-key", "GEMINI_API_KEY": ""}):

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="<think>some thinking</think>Actual response"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_cerebras_class.return_value = mock_client

        from ai.llm import LLMHandler

        handler = LLMHandler()
        handler.cerebras_client = mock_client

        result = await handler._cerebras_call("test prompt", "test system", "llama3.1-8b")

        assert result == "Actual response"
        assert "<think>" not in result


@pytest.mark.asyncio
async def test_llm_handler_fallback():
    with patch("ai.llm.Cerebras") as mock_cerebras_class, \
         patch("ai.llm.genai") as mock_genai, \
         patch.dict(os.environ, {"CEREBRAS_API_KEY": "test-key", "GEMINI_API_KEY": "test-gemini-key"}):

        # Setup Cerebras to fail
        mock_cerebras_client = MagicMock()
        mock_cerebras_client.chat.completions.create.side_effect = Exception("Cerebras error")
        mock_cerebras_class.return_value = mock_cerebras_client

        # Setup Gemini to succeed
        mock_gemini_client = MagicMock()
        mock_gemini_response = MagicMock()
        mock_gemini_response.text = "Gemini response"
        mock_gemini_client.models.generate_content.return_value = mock_gemini_response
        mock_genai.Client.return_value = mock_gemini_client

        from ai.llm import LLMHandler, ModelSize

        handler = LLMHandler()
        handler.cerebras_client = mock_cerebras_client
        handler.gemini_client = mock_gemini_client
        handler.gemini_configured = True

        result = await handler.llm_call("test prompt", "test system", ModelSize.SMALL)

        assert result == "Gemini response"


@pytest.mark.asyncio
async def test_generate_embedding():
    with patch("ai.llm.genai") as mock_genai, \
         patch.dict(os.environ, {"CEREBRAS_API_KEY": "", "GEMINI_API_KEY": "test-gemini-key"}):

        mock_client = MagicMock()
        mock_embedding_result = MagicMock()
        mock_embedding_result.embeddings = [MagicMock(values=[0.1, 0.2, 0.3])]
        mock_client.models.embed_content.return_value = mock_embedding_result
        mock_genai.Client.return_value = mock_client

        from ai.llm import LLMHandler

        handler = LLMHandler()
        handler.gemini_client = mock_client
        handler.gemini_configured = True

        result = await handler.generate_embedding("test text")

        assert result == [0.1, 0.2, 0.3]
