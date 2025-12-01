import os
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import ValidationError
import json

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
        # Construct the messages
        user_msg = request.message or "Hello, I just arrived at the site."
        
        messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]
        if request.history:
            messages.extend(request.history)
        messages.append({"role": "user", "content": user_msg})
        
        response_text = await generate_text(messages)
        
        # Check if response is JSON (ready signal)
        try:
            # Heuristic to find JSON block if LLM adds text around it
            if "{" in response_text and "}" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
                data = json.loads(json_str)
                return ChatResponse(ready=True, visitor_summary=data.get("visitor_summary"), message=None)
            else:
                 return ChatResponse(ready=False, message=response_text)
        except json.JSONDecodeError:
            # Fallback if not valid JSON, treat as chat message
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
            
        experiences = await search_similar_experiences(query)
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
