import os
import logging
import asyncio
from typing import List

# Official SDKs
import google.generativeai as genai
from cerebras.cloud.sdk import Cerebras

logger = logging.getLogger(__name__)

CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Models
CEREBRAS_MODEL = "llama3.1-8b"
GEMINI_MODEL = "gemini-1.5-flash"
EMBEDDING_MODEL = "models/gemini-embedding-001" # Matches "gemini-embedding-001" requirement, usually prefixed with models/

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

async def cerebras_call(prompt: str, system_prompt: str, timeout: int = 10) -> str:
    if not cerebras_client:
        raise Exception("Cerebras client not initialized")
    
    # Cerebras SDK is synchronous by default unless using async client. 
    # The standard 'Cerebras' client is sync. 'AsyncCerebras' exists but let's wrap in thread for simplicity 
    # if strictly needed, or just run it. FastAPI handles sync calls in threadpool if defined def (not async),
    # but since we are async def, we should avoid blocking loop.
    # However, for this prototype, blocking for 1-2s is "okay", but let's try to use AsyncCerebras if available 
    # or just run_in_executor.
    
    # Checking import for AsyncCerebras... 
    # For safety/simplicity in this env, we will run the sync call in a thread.
    
    def _call():
        response = cerebras_client.chat.completions.create(
            model=CEREBRAS_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content

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

async def generate_text(prompt: str, system_prompt: str) -> str:
    """
    Tries Cerebras first, falls back to Gemini.
    """
    try:
        return await cerebras_call(prompt, system_prompt)
    except Exception as e:
        logger.warning(f"Cerebras call failed: {e}. Falling back to Gemini.")
        try:
            return await gemini_call(prompt, system_prompt)
        except Exception as e2:
            logger.error(f"Gemini call failed: {e2}")
            # Mock fallback if everything fails and we are in dev/mock mode
            if os.getenv("MOCK_LLM", "false").lower() == "true":
                 return "<!-- Mock Error Fallback --> <p>AI Unavailable. Showing static backup.</p>"
            raise Exception(f"All LLM providers failed. Cerebras: {e}, Gemini: {e2}")

async def generate_embedding(text: str) -> List[float]:
    """
    Generates embedding using Gemini API (gemini-embedding-001).
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY.startswith("placeholder"):
        # Mock
        return [0.0] * 768

    def _call():
        # model="models/embedding-001" or "models/gemini-embedding-001"
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=text,
            task_type="retrieval_document", 
            title="Resume Section" # Optional, sometimes helps
        )
        return result['embedding']

    try:
        return await asyncio.to_thread(_call)
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        # Return zero vector on error to prevent crash? Or raise?
        # Better to raise or return zeros if non-critical.
        return [0.0] * 768