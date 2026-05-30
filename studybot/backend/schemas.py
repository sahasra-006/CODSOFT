from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class ChatRequest(BaseModel):
    session_id: int
    message: str


class ChatResponse(BaseModel):
    response: str
    type: str  # "rule", "ai", "pdf"


class SessionCreate(BaseModel):
    title: str = "New Chat"


class SessionUpdate(BaseModel):
    title: str


class SessionOut(BaseModel):
    id: int
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    response_type: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class PDFOut(BaseModel):
    id: int
    filename: str
    filepath: str
    uploaded_at: datetime
    is_active: bool

    class Config:
        from_attributes = True
