from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class IncomingMessage(BaseModel):
    """Telegram incoming message schema per AGENTS.md spec lines 319-328"""
    message_id: int
    sender_telegram_id: int
    sender_username: Optional[str] = None
    timestamp: datetime
    type: Literal["text", "photo", "callback_query", "location"]
    content: Optional[str] = None
    media_file_id: Optional[str] = None  # Telegram's file_id for photos/documents
    callback_data: Optional[str] = None  # Data from inline keyboard button press


class InlineKeyboardButton(BaseModel):
    """Telegram inline keyboard button per AGENTS.md spec lines 338-341"""
    text: str  # Button label (no strict length limit like WhatsApp)
    callback_data: str  # Data returned when pressed (max 64 bytes)


class OutgoingMessage(BaseModel):
    """Telegram outgoing message schema per AGENTS.md spec lines 330-337"""
    type: Literal["text", "photo", "interactive"]
    text: Optional[str] = None
    photo_file_id: Optional[str] = None  # Can reuse existing file_id
    photo_url: Optional[str] = None  # Upload from URL
    inline_keyboard: Optional[list[list[InlineKeyboardButton]]] = None
    parse_mode: Optional[Literal["HTML", "Markdown"]] = None
