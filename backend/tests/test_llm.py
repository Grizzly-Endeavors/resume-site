import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import os
from llm import generate_text, generate_button_suggestions, expand_query, generate_block_content

@pytest.mark.asyncio
async def test_generate_text_cerebras_success():
    with patch("llm.cerebras_call", new_callable=AsyncMock) as mock_cerebras:
        mock_cerebras.return_value = "Cerebras response"
        
        response = await generate_text("prompt", "system")
        
        assert response == "Cerebras response"
        mock_cerebras.assert_awaited_once()

@pytest.mark.asyncio
async def test_generate_text_fallback_to_gemini():
    with patch("llm.cerebras_call", new_callable=AsyncMock) as mock_cerebras, \
         patch("llm.gemini_call", new_callable=AsyncMock) as mock_gemini:
        
        mock_cerebras.side_effect = Exception("Cerebras error")
        mock_gemini.return_value = "Gemini response"
        
        response = await generate_text("prompt", "system")
        
        assert response == "Gemini response"
        mock_cerebras.assert_awaited_once()
        mock_gemini.assert_awaited_once()

@pytest.mark.asyncio
async def test_generate_text_all_fail():
    with patch("llm.cerebras_call", new_callable=AsyncMock) as mock_cerebras, \
         patch("llm.gemini_call", new_callable=AsyncMock) as mock_gemini:
        
        mock_cerebras.side_effect = Exception("Cerebras error")
        mock_gemini.side_effect = Exception("Gemini error")
        
        with pytest.raises(Exception) as excinfo:
            await generate_text("prompt", "system")
        
        assert "Gemini error" in str(excinfo.value)

@pytest.mark.asyncio
async def test_generate_button_suggestions():
    with patch("llm.cerebras_call", new_callable=AsyncMock) as mock_cerebras:
        mock_cerebras.return_value = '["button1"]'
        
        res = await generate_button_suggestions("system_prompt")
        
        mock_cerebras.assert_awaited_once()
        assert res == '["button1"]'

@pytest.mark.asyncio
async def test_expand_query():
    with patch("llm.cerebras_call", new_callable=AsyncMock) as mock_cerebras:
        mock_cerebras.return_value = "term1, term2"
        
        query = "original"
        res = await expand_query(query, "visitor")
        
        # Should combine
        assert "original term1, term2" in res
        mock_cerebras.assert_awaited_once()

@pytest.mark.asyncio
async def test_generate_block_content():
    with patch("llm.cerebras_call", new_callable=AsyncMock) as mock_cerebras:
        mock_cerebras.return_value = "block content"
        
        res = await generate_block_content("prompt", "system")
        
        assert res == "block content"
        mock_cerebras.assert_awaited_once()