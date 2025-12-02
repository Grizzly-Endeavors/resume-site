import os
import logging
import asyncio
import re
from typing import List

# Official SDKs
import google.generativeai as genai
from cerebras.cloud.sdk import Cerebras

from prompts import QUERY_EXPANSION_PROMPT

logger = logging.getLogger(__name__)

CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Models
CEREBRAS_MODEL_BUTTON = "llama3.1-8b"
CEREBRAS_MODEL_QUERY = "qwen-3-32b"
CEREBRAS_MODEL_BLOCK = "qwen-3-235b-a22b-instruct-2507"

GEMINI_MODEL = "gemini-2.5-flash"
EMBEDDING_MODEL = "models/text-embedding-004" 

# Initialize Clients
cerebras_client = None
if CEREBRAS_API_KEY and not CEREBRAS_API_KEY.startswith("placeholder"):
    try:
        cerebras_client = Cerebras(api_key=CEREBRAS_API_KEY)
    except Exception as e:
        logger.warning(f"Failed to initialize Cerebras client: {e}")

if GEMINI_API_KEY and not GEMINI_API_KEY.startswith("placeholder"):
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.warning(f"Failed to configure Gemini: {e}")

async def cerebras_call(prompt: str, system_prompt: str, model: str, timeout: int = 10) -> str:
    if not cerebras_client:
        raise Exception("Cerebras client not initialized")
    
    def _call():
        response = cerebras_client.chat.completions.create(
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

async def gemini_call(prompt: str, system_prompt: str, timeout: int = 30) -> str:
    if not GEMINI_API_KEY or GEMINI_API_KEY.startswith("placeholder"):
         if os.getenv("MOCK_LLM", "false").lower() == "true":
             return "<!-- Mock HTML Content --> <section><h2>Mock Content</h2><p>This is generated content (Mock).</p></section>"
         raise Exception("Gemini API key not configured")

    # GenAI SDK
    def _call():
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=system_prompt
        )
        response = model.generate_content(prompt)
        return response.text

    return await asyncio.to_thread(_call)

async def generate_button_suggestions(system_prompt: str, timeout: int = 10) -> str:
    """Fast button generation using Llama 70B"""
    try:
        return await cerebras_call("", system_prompt, CEREBRAS_MODEL_BUTTON, timeout)
    except Exception as e:
        logger.warning(f"Cerebras button generation failed: {e}. Falling back to Gemini.")
        return await gemini_call("Generate buttons", system_prompt)

async def expand_query(query: str, visitor_summary: str) -> str:
    """Expand search query using Qwen 32B"""
    prompt = f"Visitor: {visitor_summary}\nQuery: {query}"
    try:
        expanded = await cerebras_call(prompt, QUERY_EXPANSION_PROMPT, CEREBRAS_MODEL_QUERY, timeout=5)
        # Clean up output - it should be comma separated terms
        expanded = expanded.strip()
        return f"{query} {expanded}"  # Combine original + expanded
    except Exception as e:
        logger.warning(f"Query expansion failed: {e}, using original query")
        return query  # Fallback to original

async def generate_block_content(prompt: str, system_prompt: str) -> str:
    """High-quality block generation using Qwen 235B"""
    try:
        return await cerebras_call(prompt, system_prompt, CEREBRAS_MODEL_BLOCK)
    except Exception as e:
        logger.warning(f"Cerebras block generation failed: {e}. Falling back to Gemini.")
        try:
            return await gemini_call(prompt, system_prompt)
        except Exception as e2:
             logger.error(f"Gemini call failed: {e2}")
             if os.getenv("MOCK_LLM", "false").lower() == "true":
                 return "<!-- Mock Error Fallback --> <p>AI Unavailable. Showing static backup.</p>"
             raise Exception(f"All LLM providers failed. Cerebras: {e}, Gemini: {e2}")

async def generate_text(prompt: str, system_prompt: str) -> str:
    """
    Generic text generation (for Chat), uses Qwen 235B (Block model) by default for quality.
    """
    return await generate_block_content(prompt, system_prompt)

async def generate_embedding(text: str, task_type: str = "retrieval_document") -> List[float]:
    """
    Generates embedding using Gemini API (text-embedding-004).

    Args:
        text: The text to embed
        task_type: Either "retrieval_document" for stored content or "retrieval_query" for search queries
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY.startswith("placeholder"):
        # Mock
        return [0.0] * 768

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
        # Return zero vector on error
        return [0.0] * 768
