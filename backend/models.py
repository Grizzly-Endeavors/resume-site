from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID

class Experience(BaseModel):
    id: Optional[UUID] = None
    title: str
    content: str
    skills: List[str]
    metadata: Dict[str, Any]

class ChatRequest(BaseModel):
    message: Optional[str] = None 
    visitor_context: Optional[Dict[str, Any]] = None
    history: List[Dict[str, str]] = [] 

class ChatResponse(BaseModel):
    ready: bool
    visitor_summary: Optional[str] = None
    message: Optional[str] = None

class CompressedContext(BaseModel):
    recent_block_summary: Optional[str] = None
    shown_experience_ids: List[str] = []
    topics_covered: List[str] = []

class GenerateBlockRequest(BaseModel):
    visitor_summary: str
    context: Optional[CompressedContext] = None 
    action_type: Optional[str] = None
    action_value: Optional[str] = None
    regenerate: bool = False
    
    # Keep for backward compatibility 
    previous_block_summary: Optional[str] = None

class GenerateBlockResponse(BaseModel):
    html: str
    block_summary: str
    experience_ids: List[str] = []

class SuggestedButton(BaseModel):
    label: str
    prompt: str

class ButtonList(BaseModel):
    """Wrapper for structured button generation output.

    Used with output_structure() to ensure API-level schema compliance.
    Most structured output APIs require a root object, not an array.
    """
    buttons: List[SuggestedButton]

class GenerateButtonsRequest(BaseModel):
    visitor_summary: Optional[str] = None
    chat_history: List[Dict[str, str]] = []
    context: Optional[CompressedContext] = None

class GenerateButtonsResponse(BaseModel):
    buttons: List[SuggestedButton]