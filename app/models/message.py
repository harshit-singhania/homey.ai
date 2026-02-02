from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class IncomingMessage(BaseModel):
    message_id: str
    sender_phone: str
    timestamp: datetime
    type: Literal["text", "image", "quick_reply", "location"]
    content: Optional[str] = None
    media_url: Optional[str] = None
    quick_reply_payload: Optional[str] = None


class QuickReplyButton(BaseModel):
    id: str
    title: str  # max 20 chars


class OutgoingMessage(BaseModel):
    type: Literal["text", "image", "interactive"]
    text: Optional[str] = None
    image_url: Optional[str] = None
    buttons: Optional[list[QuickReplyButton]] = None
