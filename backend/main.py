import os
import json
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import ValidationError

from contextlib import asynccontextmanager

from db import init_db, close_db_pool
from llm import generate_text
from rag import search_similar_experiences, format_rag_results
from prompts import CHAT_SYSTEM_PROMPT, BLOCK_GENERATION_SYSTEM_PROMPT
from models import ChatRequest, ChatResponse, GenerateBlockRequest, GenerateBlockResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database...")
    await init_db()
    
    # Try seeding if data exists and env var says so? Or just let the seed script handle it manually.
    # The plan says "Seed script runs on first startup". 
    # Usually better to run it explicitly or have a check. 
    # For now, we assume user runs seed script manually or via docker command.
    
    yield
    
    # Shutdown
    logger.info("Closing database pool...")
    await close_db_pool()

app = FastAPI(lifespan=lifespan)

# Serve static files
# We expect frontend files to be in /app/frontend in the container
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return FileResponse("frontend/index.html")

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        user_msg = request.message or ""
        history = request.history or []
        
        # Count user turns (messages where role is 'user')
        user_turns = sum(1 for msg in history if msg.get("role") == "user")
        if user_msg:
             user_turns += 1

        # Construct Prompt with History
        # We format history into a text block for the LLM
        history_text = ""
        for msg in history:
            role = "Visitor" if msg.get("role") == "user" else "Assistant"
            history_text += f"{role}: {msg.get('content')}\n"
        
        if user_msg:
            history_text += f"Visitor: {user_msg}\n"

        system_instruction = CHAT_SYSTEM_PROMPT
        
        # Turn Logic
        if user_turns >= 5:
            # Force finish
            system_instruction += "\n\nCRITICAL: You have reached the maximum conversation turns. You MUST now respond with the JSON ready signal. Summarize what you know so far."
        elif user_turns >= 2:
            # Suggest finish
            system_instruction += "\n\nNote: You have gathered enough information. Please wrap up the conversation and provide the JSON ready signal."

        full_prompt = f"{history_text}\nAssistant:"
        
        # Special case for initial load (empty history, empty message)
        if not history and not user_msg:
            # Static initial greeting
            return ChatResponse(
                ready=False, 
                message="Hi! I'm an AI assistant for this resume. To get started, could you tell me a bit about who you are (e.g., recruiter, engineer) and what you're looking for?"
            )

        response_text = await generate_text(full_prompt, system_instruction)
        
        # Check if response is JSON (ready signal)
        try:
            if "{" in response_text and "}" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
                data = json.loads(json_str)
                return ChatResponse(ready=True, visitor_summary=data.get("visitor_summary"), message=None)
            else:
                 return ChatResponse(ready=False, message=response_text)
        except json.JSONDecodeError:
            return ChatResponse(ready=False, message=response_text)
            
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-block", response_model=GenerateBlockResponse)
async def generate_block(request: GenerateBlockRequest):
    try:
        # 1. RAG Retrieval
        # We use visitor summary and optionally action info to guide retrieval
        query = f"{request.visitor_summary}"
        if request.action_value:
            query += f" {request.action_value}"

        logger.info(f"[RAG] Query: '{query}'")
        logger.info(f"[RAG] Action Type: {request.action_type}, Action Value: {request.action_value}")

        experiences = await search_similar_experiences(query, limit=10)

        # Log what was retrieved
        logger.info(f"[RAG] Retrieved {len(experiences)} experiences:")
        for i, exp in enumerate(experiences, 1):
            logger.info(f"  {i}. [{exp.get('similarity', 0):.4f}] {exp['title']} (type: {exp['metadata'].get('type', 'unknown')})")

        rag_results = await format_rag_results(experiences)
        
        # 2. Prompt Construction
        formatted_prompt = BLOCK_GENERATION_SYSTEM_PROMPT.format(
            visitor_summary=request.visitor_summary,
            rag_results=rag_results,
            previous_block=request.previous_block_summary or "None",
            action_type=request.action_type or "initial_load",
            action_value=request.action_value or "None"
        )
        
        # 3. LLM Generation
        # The prompt asks for "ONLY the HTML".
        html_response = await generate_text("Generate the next block.", formatted_prompt)
        
        # Clean up markdown code blocks if present
        clean_html = html_response.replace("```html", "").replace("```", "").strip()
        
        # Summarize what was generated for the next context (simplified)
        # In a real app, we might ask the LLM to return a summary too, or parse it.
        # For now, we'll just use the title of the first experience or a generic string.
        block_summary = f"Displayed block based on: {query}"
        
        return GenerateBlockResponse(html=clean_html, block_summary=block_summary)
        
    except Exception as e:
        logger.error(f"Block generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
