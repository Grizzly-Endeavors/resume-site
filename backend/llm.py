import os
import logging
import asyncio
import re
from typing import List, Literal, Optional, Callable
from enum import Enum

# Official SDKs
import google.generativeai as genai
from cerebras.cloud.sdk import Cerebras

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
        "fallback": "gemini-2.5-flash"
    },
    ModelSize.MEDIUM: {
        "main": "qwen-3-32b",
        "fallback": "gemini-2.5-flash"
    },
    ModelSize.LARGE: {
        "main": "qwen-3-235b-a22b-instruct-2507",
        "fallback": "gemini-2.5-flash"
    }
}

EMBEDDING_MODEL = "models/text-embedding-004"

class LLMHandler:
    """Handles LLM client initialization and request routing with fallback support."""

    def __init__(self):
        self.cerebras_client: Optional[Cerebras] = None
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
                genai.configure(api_key=GEMINI_API_KEY)
                self.gemini_configured = True
                logger.info("Gemini API configured successfully")
            except Exception as e:
                logger.warning(f"Failed to configure Gemini: {e}")

    async def _cerebras_call(self, prompt: str, system_prompt: str, model: str, timeout: int = 10) -> str:
        """Make a Cerebras API call."""
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

        return await asyncio.to_thread(_call)

    async def _gemini_call(self, prompt: str, system_prompt: str, timeout: int = 30) -> str:
        """Make a Gemini API call."""
        if not self.gemini_configured:
            raise Exception("Gemini API key not configured")

        def _call():
            model = genai.GenerativeModel(
                model_name=MODEL_CONFIG[ModelSize.SMALL]["fallback"],
                system_instruction=system_prompt
            )
            response = model.generate_content(prompt)
            return response.text

        return await asyncio.to_thread(_call)

    async def handle_fallback(self, main_callable: Callable, fallback_callable: Callable) -> str:
        """Try main provider, fallback to secondary if it fails."""
        try:
            return await main_callable()
        except Exception as e:
            logger.warning(f"Main provider failed: {e}. Falling back to secondary provider.")
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

    async def generate_embedding(self, text: str, task_type: str = "retrieval_document") -> List[float]:
        """
        Generates embedding using Gemini API (text-embedding-004).

        Args:
            text: The text to embed
            task_type: Either "retrieval_document" for stored content or "retrieval_query" for search queries
        """
        if not self.gemini_configured:
            raise Exception("Gemini API key not configured")

        def _call():
            result = genai.embed_content(
                model=EMBEDDING_MODEL,
                content=text,
                task_type=task_type,
                title="Resume Section" if task_type == "retrieval_document" else None,
                output_dimensionality=768
            )
            return result['embedding']

        try:
            return await asyncio.to_thread(_call)
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise


# Global LLM handler instance
llm_handler = LLMHandler()
