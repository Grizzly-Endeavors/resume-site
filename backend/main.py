import os
import json
import logging
import re
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import ValidationError

from contextlib import asynccontextmanager

from db import init_db, close_db_pool
from ai.generation import generation_handler
from models import ChatRequest, ChatResponse, GenerateBlockRequest, GenerateBlockResponse, GenerateButtonsRequest, GenerateButtonsResponse, SuggestedButton, CompressedContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database...")
    await init_db()

    logger.info("Running automatic incremental seed...")
    try:
        from seed import seed_data
        await seed_data()
        logger.info("Seed completed successfully")
    except Exception as e:
        logger.error(f"Seed failed: {e}", exc_info=True)
        # Don't crash the app - allow it to start with existing data
        logger.warning("App starting with existing data (seed failed)")

    yield

    # Shutdown
    logger.info("Closing database pool...")
    await close_db_pool()

app = FastAPI(lifespan=lifespan)

# Serve static files
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

        # Calculate user turns
        user_turns = sum(1 for msg in history if msg.get("role") == "user")
        if user_msg:
            user_turns += 1

        # Handle initial greeting
        if not history and not user_msg:
            return ChatResponse(
                ready=False,
                message="Heya! I'm Astra, Bear's personal assistant. I'll be here to answer any questions you may have. To get started, could you tell me a bit about who you are (e.g., recruiter, engineer) and what you're looking for?"
            )

        # Generate response using GenerationHandler
        result = await generation_handler.generate_chat_response(
            message=user_msg,
            history=history,
            user_turns=user_turns
        )

        return ChatResponse(
            ready=result["ready"],
            visitor_summary=result.get("visitor_summary"),
            message=result.get("message")
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-block", response_model=GenerateBlockResponse)
async def generate_block(request: GenerateBlockRequest):
    try:
        # Generate block using GenerationHandler
        result = await generation_handler.generate_block(
            visitor_summary=request.visitor_summary,
            action_type=request.action_type or "initial_load",
            action_value=request.action_value or request.visitor_summary,
            context=request.context
        )

        return GenerateBlockResponse(
            html=result["html"],
            block_summary=result["block_summary"],
            experience_ids=result["experience_ids"]
        )

    except Exception as e:
        logger.error(f"Block generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-buttons", response_model=GenerateButtonsResponse)
async def generate_buttons(request: GenerateButtonsRequest):
    try:
        # Generate buttons using GenerationHandler
        buttons = await generation_handler.generate_buttons(
            visitor_summary=request.visitor_summary,
            chat_history=request.chat_history,
            context=request.context
        )

        return GenerateButtonsResponse(buttons=buttons)

    except Exception as e:
        logger.error(f"Button generation error: {e}")
        # Fallback buttons on any error
        return GenerateButtonsResponse(buttons=[
            SuggestedButton(label="Experience", prompt="Tell me about your professional experience"),
            SuggestedButton(label="Skills", prompt="What are your key technical skills?"),
            SuggestedButton(label="Projects", prompt="Show me some of your notable projects")
        ])