import os
import logging
import asyncio
import re
import time
import json
from typing import List, Literal, Optional, Callable, Type, TypeVar
from enum import Enum

# Official SDKs
from google import genai
from google.genai import types
from cerebras.cloud.sdk import Cerebras
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Model size definitions
class ModelSize(Enum):
    SMALL = "small"   # Fast, simple tasks (8B)
    MEDIUM = "medium" # Balanced quality/speed (32B)
    LARGE = "large"   # High quality generation (235B)

# Model configurations
MODEL_CONFIG = {
    ModelSize.SMALL: {
        "main": "llama3.1-8b",
        "fallback": "gemini-flash-lite-latest"
    },
    ModelSize.MEDIUM: {
        "main": "qwen-3-32b",
        "fallback": "gemini-flash-lite-latest"
    },
    ModelSize.LARGE: {
        "main": "qwen-3-235b-a22b-instruct-2507",
        "fallback": "gemini-flash-latest"
    }
}

EMBEDDING_MODEL = "text-embedding-004"

# Retry configuration
MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 1.0


class StructuredOutputError(Exception):
    """Raised when structured output generation fails after all retries."""
    pass


class LLMHandler:
    """Handles LLM client initialization and request routing with fallback support."""

    def __init__(self):
        self.cerebras_client: Optional[Cerebras] = None
        self.gemini_client: Optional[genai.Client] = None
        self.gemini_configured: bool = False
        self._init_clients()

    def _init_clients(self):
        """Initialize API clients."""
        if CEREBRAS_API_KEY:
            try:
                self.cerebras_client = Cerebras(api_key=CEREBRAS_API_KEY)
                logger.info("Cerebras client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Cerebras client: {e}")

        if GEMINI_API_KEY:
            try:
                # New google-genai library uses Client initialization instead of configure()
                self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
                self.gemini_configured = True
                logger.info("Gemini API client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client: {e}")

    def _format_schema_for_cerebras(self, pydantic_model: Type[BaseModel]) -> dict:
        """
        Convert Pydantic model to Cerebras-compatible schema format.

        Cerebras uses OpenAI-compatible structured output with json_schema format.
        """
        base_schema = pydantic_model.model_json_schema()

        # Extract schema name from model
        schema_name = pydantic_model.__name__

        return {
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "strict": True,
                "schema": base_schema
            }
        }

    def _format_schema_for_gemini(self, pydantic_model: Type[BaseModel]) -> dict:
        """
        Convert Pydantic model to Gemini-compatible schema format.

        Gemini accepts JSON schema directly via response_json_schema parameter.
        """
        return pydantic_model.model_json_schema()

    async def _cerebras_call(self, prompt: str, system_prompt: str, model: str, timeout: int = 10) -> str:
        """Make a Cerebras API call with retry logic."""
        if not self.cerebras_client:
            raise Exception("Cerebras client not initialized")

        def _call():
            response = self.cerebras_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            content = response.choices[0].message.content
            # Remove <think> tags and their content
            clean_content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
            return clean_content

        # Retry logic with exponential backoff
        last_exception = None
        for attempt in range(MAX_RETRIES):
            try:
                return await asyncio.to_thread(_call)
            except Exception as e:
                last_exception = e
                if attempt < MAX_RETRIES - 1:
                    backoff_time = BASE_BACKOFF_SECONDS * (2 ** attempt)
                    logger.warning(f"Cerebras call attempt {attempt + 1}/{MAX_RETRIES} failed: {e}. Retrying in {backoff_time}s...")
                    await asyncio.sleep(backoff_time)
                else:
                    logger.error(f"Cerebras call failed after {MAX_RETRIES} attempts: {e}")

        raise last_exception

    async def _cerebras_structured_call(
        self,
        prompt: str,
        system_prompt: str,
        model: str,
        response_model: Type[BaseModel],
        timeout: int = 10
    ) -> BaseModel:
        """Make a Cerebras API call with structured output and retry logic."""
        if not self.cerebras_client:
            raise Exception("Cerebras client not initialized")

        schema_format = self._format_schema_for_cerebras(response_model)

        def _call():
            response = self.cerebras_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format=schema_format,
                temperature=0.0  # Use deterministic temperature for structured output
            )
            content = response.choices[0].message.content

            # Remove <think> tags and their content
            clean_content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()

            # Parse and validate against response model
            try:
                json_data = json.loads(clean_content)
                return response_model.model_validate(json_data)
            except (json.JSONDecodeError, ValidationError) as e:
                raise Exception(f"Failed to parse/validate structured output: {e}")

        # Retry logic with exponential backoff
        last_exception = None
        for attempt in range(MAX_RETRIES):
            try:
                return await asyncio.to_thread(_call)
            except Exception as e:
                last_exception = e
                if attempt < MAX_RETRIES - 1:
                    backoff_time = BASE_BACKOFF_SECONDS * (2 ** attempt)
                    logger.warning(
                        f"Cerebras structured call attempt {attempt + 1}/{MAX_RETRIES} failed: {e}. "
                        f"Retrying in {backoff_time}s..."
                    )
                    await asyncio.sleep(backoff_time)
                else:
                    logger.error(f"Cerebras structured call failed after {MAX_RETRIES} attempts: {e}")

        raise last_exception

    async def _gemini_call(self, prompt: str, system_prompt: str, timeout: int = 30) -> str:
        """Make a Gemini API call with retry logic."""
        if not self.gemini_client or not self.gemini_configured:
            raise Exception("Gemini API key not configured")

        def _call():
            # New google-genai library uses client.models.generate_content()
            response = self.gemini_client.models.generate_content(
                model=MODEL_CONFIG[ModelSize.SMALL]["fallback"],
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part(text=prompt)]
                    )
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7
                )
            )
            return response.text

        # Retry logic with exponential backoff
        last_exception = None
        for attempt in range(MAX_RETRIES):
            try:
                return await asyncio.to_thread(_call)
            except Exception as e:
                last_exception = e
                if attempt < MAX_RETRIES - 1:
                    backoff_time = BASE_BACKOFF_SECONDS * (2 ** attempt)
                    logger.warning(f"Gemini call attempt {attempt + 1}/{MAX_RETRIES} failed: {e}. Retrying in {backoff_time}s...")
                    await asyncio.sleep(backoff_time)
                else:
                    logger.error(f"Gemini call failed after {MAX_RETRIES} attempts: {e}")

        raise last_exception

    async def _gemini_structured_call(
        self,
        prompt: str,
        system_prompt: str,
        response_model: Type[BaseModel],
        timeout: int = 30
    ) -> BaseModel:
        """Make a Gemini API call with structured output and retry logic."""
        if not self.gemini_client or not self.gemini_configured:
            raise Exception("Gemini API key not configured")

        schema_format = self._format_schema_for_gemini(response_model)

        def _call():
            # New google-genai library uses response_json_schema parameter
            response = self.gemini_client.models.generate_content(
                model=MODEL_CONFIG[ModelSize.SMALL]["fallback"],
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part(text=prompt)]
                    )
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_json_schema=schema_format,
                    temperature=1.0
                )
            )

            # Parse and validate against response model
            try:
                json_data = json.loads(response.text)
                return response_model.model_validate(json_data)
            except (json.JSONDecodeError, ValidationError) as e:
                raise Exception(f"Failed to parse/validate structured output: {e}")

        # Retry logic with exponential backoff
        last_exception = None
        for attempt in range(MAX_RETRIES):
            try:
                return await asyncio.to_thread(_call)
            except Exception as e:
                last_exception = e
                if attempt < MAX_RETRIES - 1:
                    backoff_time = BASE_BACKOFF_SECONDS * (2 ** attempt)
                    logger.warning(
                        f"Gemini structured call attempt {attempt + 1}/{MAX_RETRIES} failed: {e}. "
                        f"Retrying in {backoff_time}s..."
                    )
                    await asyncio.sleep(backoff_time)
                else:
                    logger.error(f"Gemini structured call failed after {MAX_RETRIES} attempts: {e}")

        raise last_exception

    async def handle_fallback(self, main_callable: Callable, fallback_callable: Callable) -> str:
        """
        Try main provider with retries, fallback to secondary if all retries fail.

        The main provider will retry MAX_RETRIES times with exponential backoff
        before falling back to the secondary provider.
        """
        try:
            return await main_callable()
        except Exception as e:
            logger.warning(f"Main provider failed after all retries: {e}. Falling back to secondary provider.")
            return await fallback_callable()

    async def llm_call(
        self,
        prompt: str,
        system_prompt: str,
        size: ModelSize,
        timeout: int = 10
    ) -> str:
        """
        Make an LLM call with automatic fallback.

        Args:
            prompt: User prompt
            system_prompt: System instruction
            size: Model size (SMALL, MEDIUM, or LARGE)
            timeout: Request timeout in seconds
        """
        config = MODEL_CONFIG[size]

        return await self.handle_fallback(
            lambda: self._cerebras_call(prompt, system_prompt, config["main"], timeout),
            lambda: self._gemini_call(prompt, system_prompt, timeout)
        )

    async def output_structure(
        self,
        prompt: str,
        system_prompt: str,
        size: ModelSize,
        response_model: Type[BaseModel],
        timeout: int = 10
    ) -> BaseModel:
        """
        Make an LLM call with structured output validation using Pydantic models.

        This method enforces schema constraints at the API level and validates
        responses against the provided Pydantic model. It includes automatic
        retry logic (3 attempts per provider) and fallback from Cerebras to Gemini.

        Args:
            prompt: User prompt
            system_prompt: System instruction
            size: Model size (SMALL, MEDIUM, or LARGE)
            response_model: Pydantic model class for response validation
            timeout: Request timeout in seconds

        Returns:
            Instance of response_model with validated data

        Raises:
            StructuredOutputError: If all attempts fail (3 retries × 2 providers)

        Example:
            >>> from models import ButtonList
            >>> result = await llm_handler.output_structure(
            ...     prompt="Generate buttons",
            ...     system_prompt=BUTTON_PROMPT,
            ...     size=ModelSize.SMALL,
            ...     response_model=ButtonList
            ... )
            >>> print(result.buttons[0].label)
        """
        config = MODEL_CONFIG[size]

        try:
            return await self.handle_fallback(
                lambda: self._cerebras_structured_call(
                    prompt, system_prompt, config["main"], response_model, timeout
                ),
                lambda: self._gemini_structured_call(
                    prompt, system_prompt, response_model, timeout
                )
            )
        except Exception as e:
            # Both providers failed after all retries
            error_msg = (
                f"Structured output generation failed after all retries. "
                f"Model: {response_model.__name__}, Error: {e}"
            )
            logger.error(error_msg)
            raise StructuredOutputError(error_msg) from e

    async def generate_embedding(self, text: str, task_type: str = "retrieval_document") -> List[float]:
        """
        Generates embedding using Gemini API (text-embedding-004).

        Args:
            text: The text to embed
            task_type: Either "retrieval_document" for stored content or "retrieval_query" for search queries
        """
        if not self.gemini_client or not self.gemini_configured:
            raise Exception("Gemini API key not configured")

        def _call():
            # New google-genai library uses client.models.embed_content()
            result = self.gemini_client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=768
                )
            )
            # The new SDK returns embeddings as a list of values
            return result.embeddings[0].values

        try:
            return await asyncio.to_thread(_call)
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise


# Global LLM handler instance
llm_handler = LLMHandler()
