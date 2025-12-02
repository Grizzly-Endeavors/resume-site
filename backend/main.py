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
from llm import generate_text, generate_block_content, generate_button_suggestions, expand_query
from rag import search_similar_experiences, format_rag_results
from prompts import CHAT_SYSTEM_PROMPT, BLOCK_GENERATION_SYSTEM_PROMPT, BUTTON_GENERATION_PROMPT
from models import ChatRequest, ChatResponse, GenerateBlockRequest, GenerateBlockResponse, GenerateButtonsRequest, GenerateButtonsResponse, SuggestedButton, CompressedContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database...")
    await init_db()
    
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
        
        user_turns = sum(1 for msg in history if msg.get("role") == "user")
        if user_msg:
             user_turns += 1

        history_text = ""
        for msg in history:
            role = "Visitor" if msg.get("role") == "user" else "Assistant"
            history_text += f"{role}: {msg.get('content')}\n"
        
        if user_msg:
            history_text += f"Visitor: {user_msg}\n"

        system_instruction = CHAT_SYSTEM_PROMPT
        
        if user_turns >= 5:
            system_instruction += "\n\nCRITICAL: You have reached the maximum conversation turns. You MUST now respond with the JSON ready signal. Summarize what you know so far."
        elif user_turns >= 2:
            system_instruction += "\n\nNote: You have gathered enough information. Please wrap up the conversation and provide the JSON ready signal."

        full_prompt = f"{history_text}\nAssistant:"
        
        if not history and not user_msg:
            return ChatResponse(
                ready=False, 
                message="Hi! I'm an AI assistant for this resume. To get started, could you tell me a bit about who you are (e.g., recruiter, engineer) and what you're looking for?"
            )

        response_text = await generate_text(full_prompt, system_instruction)
        
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

def parse_block_response(response: str) -> tuple[str, str]:
    """Extract HTML and summary from structured response"""
    block_match = re.search(r'<block>(.*?)</block>', response, re.DOTALL)
    summary_match = re.search(r'<summary>(.*?)</summary>', response, re.DOTALL)

    if block_match and summary_match:
        html = block_match.group(1).strip()
        summary = summary_match.group(1).strip()
    else:
        # Fallback: treat entire response as HTML
        html = response.strip()
        summary = "Displayed relevant experience block"
        logger.warning("Failed to parse structured response, using fallback")

    # Filter out any summary tags and their content from the HTML
    html = re.sub(r'<summary[^>]*>.*?</summary>', '', html, flags=re.DOTALL | re.IGNORECASE)

    return html, summary

@app.post("/api/generate-block", response_model=GenerateBlockResponse)
async def generate_block(request: GenerateBlockRequest):
    try:
        # 1. Query Expansion
        query = request.action_value or request.visitor_summary
        expanded_query = await expand_query(query, request.visitor_summary)
        logger.info(f"[QUERY] Original: '{query}' -> Expanded: '{expanded_query}'")

        # 2. RAG with Diversity Scoring
        shown_ids = request.context.shown_experience_ids if request.context else []
        experiences = await search_similar_experiences(
            query=expanded_query,
            limit=10,
            shown_ids=shown_ids
        )

        experience_ids = [exp['id'] for exp in experiences]
        rag_results = await format_rag_results(experiences)

        # 3. Build Context Summary
        context_summary = ""
        if request.context:
            if request.context.recent_block_summary:
                context_summary += f"Most Recent Block: {request.context.recent_block_summary}\n"
            if request.context.topics_covered:
                context_summary += f"Topics Already Covered: {', '.join(request.context.topics_covered)}\n"

        # 4. Format Prompt
        formatted_prompt = BLOCK_GENERATION_SYSTEM_PROMPT.format(
            visitor_summary=request.visitor_summary,
            context_summary=context_summary,
            rag_results=rag_results,
            action_type=request.action_type or "initial_load",
            action_value=request.action_value or "None"
        )

        # 5. Generate Block
        response = await generate_block_content("Generate the next block with summary.", formatted_prompt)

        # 6. Parse Response
        html, summary = parse_block_response(response)

        return GenerateBlockResponse(
            html=html,
            block_summary=summary,
            experience_ids=experience_ids
        )

    except Exception as e:
        logger.error(f"Block generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-buttons", response_model=GenerateButtonsResponse)
async def generate_buttons(request: GenerateButtonsRequest):
    try:
        # Format chat history
        history_text = ""
        for msg in request.chat_history[-6:]:
            role = "Visitor" if msg.get("role") == "user" else "Assistant"
            history_text += f"{role}: {msg.get('content', '')}\n"

        # Build Context Summary
        context_summary = ""
        shown_ids = []
        if request.context:
            if request.context.recent_block_summary:
                context_summary += f"Most Recent Block: {request.context.recent_block_summary}\n"
            if request.context.topics_covered:
                context_summary += f"Topics Already Covered: {', '.join(request.context.topics_covered)}\n"
            shown_ids = request.context.shown_experience_ids

        # RAG Search (Consistent with block generation)
        query = request.visitor_summary or "General professional experience"
        expanded_query = await expand_query(query, request.visitor_summary)
        
        experiences = await search_similar_experiences(
            query=expanded_query,
            limit=10,
            shown_ids=shown_ids
        )
        rag_results = await format_rag_results(experiences)

        # Construct prompt
        formatted_prompt = BUTTON_GENERATION_PROMPT.format(
            visitor_summary=request.visitor_summary or "Unknown visitor",
            chat_history=history_text if history_text else "No prior conversation",
            context_summary=context_summary,
            rag_results=rag_results
        )

        # Generate using Llama 70B (fast JSON generation)
        response_text = await generate_button_suggestions(formatted_prompt)

        # Parse JSON
        clean_response = response_text.replace("```json", "").replace("```", "").strip()
        try:
            buttons_data = json.loads(clean_response)
        except json.JSONDecodeError:
             # Try to find JSON in the text
             match = re.search(r'\[.*\]', clean_response, re.DOTALL)
             if match:
                 buttons_data = json.loads(match.group(0))
             else:
                 raise

        buttons = [SuggestedButton(label=btn["label"], prompt=btn["prompt"]) for btn in buttons_data]

        return GenerateButtonsResponse(buttons=buttons)

    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to parse button generation response: {e}")
        # Fallback
        return GenerateButtonsResponse(buttons=[
            SuggestedButton(label="Experience", prompt="Tell me about your professional experience"),
            SuggestedButton(label="Skills", prompt="What are your key technical skills?"),
            SuggestedButton(label="Projects", prompt="Show me some of your notable projects")
        ])
    except Exception as e:
        logger.error(f"Button generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))