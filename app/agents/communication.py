from typing import Literal
from datetime import datetime
import hashlib
from telegram import Update, Bot
from app.agents.base import MessageTransport
from app.models.message import IncomingMessage, OutgoingMessage, InlineKeyboardButton
from app.config import settings
from app.api.mock import mock_message_queue
from app.services.telegram import TelegramBotClient


class MockTransport(MessageTransport):
    """Mock transport for development/testing - REST-based interface"""
    async def receive(self, raw_payload: dict) -> IncomingMessage:
        telegram_id = raw_payload.get("telegram_id", 123456789)
        username = raw_payload.get("username")
        message_type = raw_payload.get("message_type", "text")
        content = raw_payload.get("content")
        media_file_id = raw_payload.get("media_file_id")
        callback_data = raw_payload.get("callback_data")

        message_id = int(hashlib.md5(
            f"{telegram_id}_{datetime.now().isoformat()}_{content}".encode()
        ).hexdigest()[:8], 16)

        return IncomingMessage(
            message_id=message_id,
            sender_telegram_id=telegram_id,
            sender_username=username,
            timestamp=datetime.utcnow(),
            type=message_type,
            content=content,
            media_file_id=media_file_id,
            callback_data=callback_data,
        )

    async def send(self, user_id: str, message: OutgoingMessage) -> bool:
        mock_outgoing = {
            "message_id": int(hashlib.md5(f"{user_id}_{datetime.now().isoformat()}".encode()).hexdigest()[:8], 16),
            "telegram_id": user_id,
            "message_type": message.type,
            "text": message.text,
            "photo_file_id": message.photo_file_id,
            "photo_url": message.photo_url,
            "inline_keyboard": [
                [{"text": btn.text, "callback_data": btn.callback_data} for btn in row]
                for row in message.inline_keyboard
            ] if message.inline_keyboard else None,
            "parse_mode": message.parse_mode,
            "created_at": datetime.utcnow().isoformat(),
        }
        mock_message_queue.append(mock_outgoing)
        return True


class TelegramTransport(MessageTransport):
    """Real Telegram Bot API integration using python-telegram-bot"""
    def __init__(self):
        self.client = TelegramBotClient(token=settings.telegram_bot_token)

    async def receive(self, raw_payload: dict) -> IncomingMessage:
        """
        Parse Telegram Update object into IncomingMessage.
        Handles: text messages, photos, callback queries, locations.
        """
        # Parse Telegram Update from webhook payload
        update = Update.de_json(raw_payload, self.client.bot)

        if not update:
            raise ValueError("Invalid Telegram update payload")

        # Initialize defaults
        message_id = None
        sender_telegram_id = None
        sender_username = None
        timestamp = None
        message_type = None
        content = None
        media_file_id = None
        callback_data = None

        # Handle regular messages (text, photo, location)
        if update.message:
            msg = update.message
            message_id = msg.message_id
            sender_telegram_id = msg.from_user.id
            sender_username = msg.from_user.username
            timestamp = msg.date

            if msg.text:
                message_type = "text"
                content = msg.text
            elif msg.photo:
                message_type = "photo"
                # Get largest photo size
                media_file_id = msg.photo[-1].file_id
                content = msg.caption
            elif msg.location:
                message_type = "location"
                content = f"{msg.location.latitude},{msg.location.longitude}"

        # Handle callback queries (inline keyboard button presses)
        elif update.callback_query:
            query = update.callback_query
            message_id = query.message.message_id
            sender_telegram_id = query.from_user.id
            sender_username = query.from_user.username
            timestamp = query.message.date
            message_type = "callback_query"
            callback_data = query.data
            content = callback_data  # Store callback_data in content too

        if not message_id or not sender_telegram_id:
            raise ValueError("Unable to parse Telegram update - missing required fields")

        return IncomingMessage(
            message_id=message_id,
            sender_telegram_id=sender_telegram_id,
            sender_username=sender_username,
            timestamp=timestamp,
            type=message_type,
            content=content,
            media_file_id=media_file_id,
            callback_data=callback_data,
        )

    async def send(self, user_id: str, message: OutgoingMessage) -> bool:
        """
        Send message via Telegram Bot API.
        Delegates to TelegramBotClient.send()
        """
        try:
            chat_id = int(user_id)
            await self.client.send(chat_id=chat_id, message=message)
            return True
        except Exception as e:
            print(f"Failed to send Telegram message: {e}")
            return False


def get_transport() -> MessageTransport:
    """Factory function to get the configured message transport"""
    if settings.transport == "mock":
        return MockTransport()
    elif settings.transport == "telegram":
        return TelegramTransport()
    else:
        raise ValueError(f"Unsupported transport: {settings.transport}")
