"""Unit tests for structured output functionality in LLMHandler."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from typing import List
from pydantic import BaseModel, ValidationError

from ai.llm import llm_handler, ModelSize, StructuredOutputError
from models import SuggestedButton, ButtonList


# Test models for structured output validation
class SimpleModel(BaseModel):
    """Simple test model with basic fields."""
    text: str
    count: int


class ButtonTestModel(BaseModel):
    """Test model matching ButtonList structure."""
    buttons: List[SuggestedButton]


class TestSchemaAdapters:
    """Tests for schema format conversion methods."""

    def test_cerebras_schema_format(self):
        """Test that Cerebras schema formatter produces correct structure."""
        schema = llm_handler._format_schema_for_cerebras(SimpleModel)

        assert "type" in schema
        assert schema["type"] == "json_schema"
        assert "json_schema" in schema

        json_schema = schema["json_schema"]
        assert json_schema["name"] == "SimpleModel"
        assert json_schema["strict"] is True
        assert "schema" in json_schema
        assert "properties" in json_schema["schema"]

    def test_gemini_schema_format(self):
        """Test that Gemini schema formatter returns the model class."""
        schema = llm_handler._format_schema_for_gemini(SimpleModel)

        assert schema == SimpleModel
        assert issubclass(schema, BaseModel)

    def test_schema_adapter_preserves_model_info(self):
        """Test that schema adapters preserve model metadata."""
        cerebras_schema = llm_handler._format_schema_for_cerebras(ButtonList)
        assert cerebras_schema["json_schema"]["name"] == "ButtonList"

        gemini_schema = llm_handler._format_schema_for_gemini(ButtonList)
        assert gemini_schema.__name__ == "ButtonList"


class TestStructuredOutputExceptions:
    """Tests for exception handling in structured outputs."""

    def test_structured_output_error_creation(self):
        """Test that StructuredOutputError can be created and raised."""
        error_msg = "Test error message"
        error = StructuredOutputError(error_msg)

        assert str(error) == error_msg
        assert isinstance(error, Exception)

    @pytest.mark.asyncio
    async def test_output_structure_raises_on_all_failures(self):
        """Test that output_structure raises StructuredOutputError when all providers fail."""
        with patch.object(llm_handler, '_cerebras_structured_call', new_callable=AsyncMock) as mock_cerebras, \
             patch.object(llm_handler, '_gemini_structured_call', new_callable=AsyncMock) as mock_gemini:

            mock_cerebras.side_effect = Exception("Cerebras error")
            mock_gemini.side_effect = Exception("Gemini error")

            with pytest.raises(StructuredOutputError) as excinfo:
                await llm_handler.output_structure(
                    prompt="test",
                    system_prompt="test",
                    size=ModelSize.SMALL,
                    response_model=SimpleModel
                )

            assert "failed after all retries" in str(excinfo.value).lower()
            assert "SimpleModel" in str(excinfo.value)


class TestCerebrasStructuredCall:
    """Tests for Cerebras structured output calls."""

    @pytest.mark.asyncio
    async def test_cerebras_structured_call_success(self):
        """Test successful Cerebras structured output call."""
        with patch.object(llm_handler, 'cerebras_client') as mock_client:
            # Setup mock response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '{"text": "test", "count": 42}'
            mock_client.chat.completions.create.return_value = mock_response

            result = await llm_handler._cerebras_structured_call(
                prompt="test",
                system_prompt="test",
                model="llama3.1-8b",
                response_model=SimpleModel
            )

            assert isinstance(result, SimpleModel)
            assert result.text == "test"
            assert result.count == 42

    @pytest.mark.asyncio
    async def test_cerebras_structured_call_removes_think_tags(self):
        """Test that Cerebras removes <think> tags from response."""
        with patch.object(llm_handler, 'cerebras_client') as mock_client:
            # Setup mock response with think tags
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = (
                '<think>Let me think about this...</think>{"text": "result", "count": 5}'
            )
            mock_client.chat.completions.create.return_value = mock_response

            result = await llm_handler._cerebras_structured_call(
                prompt="test",
                system_prompt="test",
                model="llama3.1-8b",
                response_model=SimpleModel
            )

            assert result.text == "result"
            assert result.count == 5

    @pytest.mark.asyncio
    async def test_cerebras_structured_call_validation_error_retries(self):
        """Test that validation errors trigger retries."""
        with patch.object(llm_handler, 'cerebras_client') as mock_client:
            # First call returns invalid data, second call returns valid
            mock_response_invalid = MagicMock()
            mock_response_invalid.choices = [MagicMock()]
            mock_response_invalid.choices[0].message.content = '{"text": "test"}'  # Missing 'count'

            mock_response_valid = MagicMock()
            mock_response_valid.choices = [MagicMock()]
            mock_response_valid.choices[0].message.content = '{"text": "test", "count": 10}'

            mock_client.chat.completions.create.side_effect = [mock_response_invalid, mock_response_valid]

            result = await llm_handler._cerebras_structured_call(
                prompt="test",
                system_prompt="test",
                model="llama3.1-8b",
                response_model=SimpleModel,
                timeout=10
            )

            assert result.text == "test"
            assert result.count == 10
            assert mock_client.chat.completions.create.call_count == 2

    @pytest.mark.asyncio
    async def test_cerebras_structured_call_not_initialized_raises(self):
        """Test that error is raised if Cerebras client not initialized."""
        original_client = llm_handler.cerebras_client
        try:
            llm_handler.cerebras_client = None

            with pytest.raises(Exception) as excinfo:
                await llm_handler._cerebras_structured_call(
                    prompt="test",
                    system_prompt="test",
                    model="llama3.1-8b",
                    response_model=SimpleModel
                )

            assert "not initialized" in str(excinfo.value)
        finally:
            llm_handler.cerebras_client = original_client


class TestGeminiStructuredCall:
    """Tests for Gemini structured output calls."""

    @pytest.mark.asyncio
    async def test_gemini_structured_call_success(self):
        """Test successful Gemini structured output call."""
        with patch('ai.llm.genai.GenerativeModel') as mock_model_class:
            mock_model = MagicMock()
            mock_model_class.return_value = mock_model

            mock_response = MagicMock()
            mock_response.text = '{"text": "gemini_result", "count": 99}'
            mock_model.generate_content.return_value = mock_response

            result = await llm_handler._gemini_structured_call(
                prompt="test",
                system_prompt="test",
                response_model=SimpleModel
            )

            assert isinstance(result, SimpleModel)
            assert result.text == "gemini_result"
            assert result.count == 99

    @pytest.mark.asyncio
    async def test_gemini_structured_call_validation_error_retries(self):
        """Test that Gemini validation errors trigger retries."""
        with patch('ai.llm.genai.GenerativeModel') as mock_model_class:
            mock_model = MagicMock()
            mock_model_class.return_value = mock_model

            # First call returns invalid data, second call returns valid
            mock_response_invalid = MagicMock()
            mock_response_invalid.text = '{"text": "test"}'  # Missing 'count'

            mock_response_valid = MagicMock()
            mock_response_valid.text = '{"text": "test", "count": 20}'

            mock_model.generate_content.side_effect = [mock_response_invalid, mock_response_valid]

            result = await llm_handler._gemini_structured_call(
                prompt="test",
                system_prompt="test",
                response_model=SimpleModel
            )

            assert result.text == "test"
            assert result.count == 20
            assert mock_model.generate_content.call_count == 2

    @pytest.mark.asyncio
    async def test_gemini_structured_call_not_configured_raises(self):
        """Test that error is raised if Gemini not configured."""
        original_configured = llm_handler.gemini_configured
        try:
            llm_handler.gemini_configured = False

            with pytest.raises(Exception) as excinfo:
                await llm_handler._gemini_structured_call(
                    prompt="test",
                    system_prompt="test",
                    response_model=SimpleModel
                )

            assert "not configured" in str(excinfo.value)
        finally:
            llm_handler.gemini_configured = original_configured


class TestOutputStructureMethod:
    """Tests for the public output_structure method."""

    @pytest.mark.asyncio
    async def test_output_structure_cerebras_success(self):
        """Test output_structure succeeds when Cerebras works."""
        with patch.object(llm_handler, '_cerebras_structured_call', new_callable=AsyncMock) as mock_cerebras:
            expected = SimpleModel(text="test", count=42)
            mock_cerebras.return_value = expected

            result = await llm_handler.output_structure(
                prompt="test",
                system_prompt="test",
                size=ModelSize.SMALL,
                response_model=SimpleModel
            )

            assert result == expected
            mock_cerebras.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_output_structure_fallback_to_gemini(self):
        """Test output_structure falls back to Gemini when Cerebras fails."""
        with patch.object(llm_handler, '_cerebras_structured_call', new_callable=AsyncMock) as mock_cerebras, \
             patch.object(llm_handler, '_gemini_structured_call', new_callable=AsyncMock) as mock_gemini:

            mock_cerebras.side_effect = Exception("Cerebras error")
            expected = SimpleModel(text="gemini", count=99)
            mock_gemini.return_value = expected

            result = await llm_handler.output_structure(
                prompt="test",
                system_prompt="test",
                size=ModelSize.SMALL,
                response_model=SimpleModel
            )

            assert result == expected
            mock_cerebras.assert_awaited_once()
            mock_gemini.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_output_structure_uses_correct_model_size(self):
        """Test that output_structure passes correct model to Cerebras."""
        with patch.object(llm_handler, '_cerebras_structured_call', new_callable=AsyncMock) as mock_cerebras:
            mock_cerebras.return_value = SimpleModel(text="test", count=1)

            await llm_handler.output_structure(
                prompt="test",
                system_prompt="test",
                size=ModelSize.LARGE,
                response_model=SimpleModel
            )

            # Verify that the LARGE model was passed
            call_args = mock_cerebras.call_args
            assert call_args[0][2] == "qwen-3-235b-a22b-instruct-2507"  # LARGE model


class TestButtonListModel:
    """Tests for ButtonList model validation."""

    def test_button_list_valid_data(self):
        """Test ButtonList validates correct data."""
        valid_data = {
            "buttons": [
                {"label": "Test", "prompt": "Test prompt"},
                {"label": "Another", "prompt": "Another prompt"}
            ]
        }
        button_list = ButtonList.model_validate(valid_data)

        assert len(button_list.buttons) == 2
        assert button_list.buttons[0].label == "Test"
        assert button_list.buttons[0].prompt == "Test prompt"
        assert button_list.buttons[1].label == "Another"

    def test_button_list_invalid_data_missing_field(self):
        """Test ButtonList rejects data missing required field."""
        invalid_data = {"buttons": [{"label": "No prompt"}]}

        with pytest.raises(ValidationError):
            ButtonList.model_validate(invalid_data)

    def test_button_list_invalid_data_empty_buttons(self):
        """Test ButtonList accepts empty buttons array."""
        valid_data = {"buttons": []}
        button_list = ButtonList.model_validate(valid_data)

        assert len(button_list.buttons) == 0

    def test_button_list_many_buttons(self):
        """Test ButtonList handles many buttons."""
        valid_data = {
            "buttons": [
                {"label": f"Button {i}", "prompt": f"Prompt {i}"}
                for i in range(10)
            ]
        }
        button_list = ButtonList.model_validate(valid_data)

        assert len(button_list.buttons) == 10
        assert button_list.buttons[5].label == "Button 5"

    def test_button_list_special_characters(self):
        """Test ButtonList handles special characters in labels and prompts."""
        valid_data = {
            "buttons": [
                {"label": "AI/ML 🤖", "prompt": "Tell me about AI & ML projects (C++/Python)"},
            ]
        }
        button_list = ButtonList.model_validate(valid_data)

        assert "🤖" in button_list.buttons[0].label
        assert "C++" in button_list.buttons[0].prompt


class TestIntegrationScenarios:
    """Integration tests for structured output workflows."""

    @pytest.mark.asyncio
    async def test_button_generation_with_structured_output(self):
        """Test end-to-end button generation using structured output."""
        from ai.generation import generation_handler

        with patch.object(generation_handler.llm, 'output_structure', new_callable=AsyncMock) as mock_llm, \
             patch('ai.generation.search_similar_experiences', new_callable=AsyncMock) as mock_search:

            # Setup mocks
            mock_search.return_value = []
            mock_llm.return_value = ButtonList(buttons=[
                SuggestedButton(label="ML", prompt="Tell me about ML projects"),
                SuggestedButton(label="Backend", prompt="What backend experience do you have?"),
                SuggestedButton(label="Leadership", prompt="Describe your leadership experience")
            ])

            # Execute
            buttons = await generation_handler.generate_buttons(
                visitor_summary="Software recruiter looking for ML talent",
                chat_history=[],
                context=None
            )

            # Verify
            assert len(buttons) == 3
            assert buttons[0].label == "ML"
            assert buttons[1].label == "Backend"
            assert buttons[2].label == "Leadership"
            mock_llm.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_button_generation_fallback_on_error(self):
        """Test button generation returns fallback when structured output fails."""
        from ai.generation import generation_handler

        with patch.object(generation_handler.llm, 'output_structure', new_callable=AsyncMock) as mock_llm, \
             patch('ai.generation.search_similar_experiences', new_callable=AsyncMock) as mock_search:

            # Setup failure
            mock_search.return_value = []
            mock_llm.side_effect = StructuredOutputError("All providers failed")

            # Execute
            buttons = await generation_handler.generate_buttons(
                visitor_summary="Test visitor",
                chat_history=[],
                context=None
            )

            # Verify fallback buttons returned
            assert len(buttons) == 3
            assert buttons[0].label == "Experience"
            assert buttons[1].label == "Skills"
            assert buttons[2].label == "Projects"

    @pytest.mark.asyncio
    async def test_output_structure_with_button_list(self):
        """Test output_structure correctly handles ButtonList model."""
        with patch.object(llm_handler, '_cerebras_structured_call', new_callable=AsyncMock) as mock_cerebras:
            expected = ButtonList(buttons=[
                SuggestedButton(label="Test", prompt="Test prompt")
            ])
            mock_cerebras.return_value = expected

            result = await llm_handler.output_structure(
                prompt="test",
                system_prompt="test",
                size=ModelSize.SMALL,
                response_model=ButtonList
            )

            assert isinstance(result, ButtonList)
            assert len(result.buttons) == 1
            assert result.buttons[0].label == "Test"
