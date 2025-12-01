from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID

class Experience(BaseModel):
    id: Optional[UUID] = None
    title: str
    content: str
    skills: List[str]
    metadata: Dict[str, Any]
    # embedding field is usually handled internally, not exposed in API often

class ChatRequest(BaseModel):
    message: Optional[str] = None # Optional because initial load might not have a message
    visitor_context: Optional[Dict[str, Any]] = None
    history: Optional[List[Dict[str, str]]] = None  # List of {"role": "user"|"assistant", "content": str}

class ChatResponse(BaseModel):
    ready: bool
    visitor_summary: Optional[str] = None
    message: Optional[str] = None

class GenerateBlockRequest(BaseModel):
    visitor_summary: str
    previous_block_summary: Optional[str] = None
    action_type: Optional[str] = None
    action_value: Optional[str] = None
    regenerate: bool = False

class GenerateBlockResponse(BaseModel):
    html: str
    block_summary: str
