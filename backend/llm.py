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

async def cerebras_call(messages: List[Dict[str, str]], timeout: int = 10) -> str:
    if not cerebras_client:
        raise Exception("Cerebras client not initialized")
    
    def _call():
        response = cerebras_client.chat.completions.create(
            model=CEREBRAS_MODEL,
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content

    return await asyncio.to_thread(_call)

async def gemini_call(messages: List[Dict[str, str]], timeout: int = 30) -> str:
    if not GEMINI_API_KEY or GEMINI_API_KEY.startswith("placeholder"):
         if os.getenv("MOCK_LLM", "false").lower() == "true":
             return "<!-- Mock HTML Content --> <section><h2>Mock Content</h2><p>This is generated content (Mock).</p></section>"
         raise Exception("Gemini API key not configured")

    # GenAI SDK
    def _call():
        # Extract system instruction if present
        system_instruction = None
        chat_messages = messages
        if messages and messages[0]["role"] == "system":
            system_instruction = messages[0]["content"]
            chat_messages = messages[1:]
        
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=system_instruction
        )
        
        # Use chat session for history
        chat = model.start_chat(history=chat_messages[:-1])  # all except the last message
        response = chat.send_message(chat_messages[-1]["content"])
        return response.text

    return await asyncio.to_thread(_call)

async def generate_text(messages: List[Dict[str, str]]) -> str:
    """
    Tries Cerebras first, falls back to Gemini.
    """
    try:
        return await cerebras_call(messages)
    except Exception as e:
        logger.warning(f"Cerebras call failed: {e}. Falling back to Gemini.")
        try:
            return await gemini_call(messages)
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