from typing import Literal
from datetime import datetime
import hashlib
from app.agents.base import MessageTransport
from app.models.message import IncomingMessage, OutgoingMessage, QuickReplyButton
from app.config import settings
from app.api.mock import mock_message_queue


class MockTransport(MessageTransport):
    async def receive(self, raw_payload: dict) -> IncomingMessage:
        phone_number = raw_payload.get("phone_number", "+1234567890")
        message_type = raw_payload.get("message_type", "text")
        content = raw_payload.get("content")
        media_url = raw_payload.get("media_url")
        
        message_id = hashlib.md5(
            f"{phone_number}_{datetime.now().isoformat()}_{content}".encode()
        ).hexdigest()
        
        return IncomingMessage(
            message_id=message_id,
            sender_phone=phone_number,
            timestamp=datetime.utcnow(),
            type=message_type,
            content=content,
            media_url=media_url,
        )

    async def send(self, user_id: str, message: OutgoingMessage) -> bool:
        mock_outgoing = {
            "message_id": hashlib.md5(f"{user_id}_{datetime.now().isoformat()}".encode()).hexdigest(),
            "phone_number": user_id,
            "message_type": message.type,
            "text": message.text,
            "image_url": message.image_url,
            "buttons": [{"id": b.id, "title": b.title} for b in message.buttons] if message.buttons else None,
            "created_at": datetime.utcnow().isoformat(),
        }
        mock_message_queue.append(mock_outgoing)
        return True


class WhatsAppTransport(MessageTransport):
    def __init__(self):
        self.access_token = settings.whatsapp_access_token
        self.phone_number_id = settings.whatsapp_phone_number_id
        self.api_url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages"

    async def receive(self, raw_payload: dict) -> IncomingMessage:
        entry = raw_payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        
        if not messages:
            raise ValueError("No messages in webhook payload")
        
        wa_message = messages[0]
        sender_phone = wa_message.get("from")
        message_id = wa_message.get("id")
        timestamp = datetime.fromtimestamp(int(wa_message.get("timestamp", 0)))
        
        message_type = wa_message.get("type", "text")
        
        content = None
        media_url = None
        quick_reply_payload = None
        
        if message_type == "text":
            content = wa_message.get("text", {}).get("body")
        elif message_type == "image":
            content = wa_message.get("image", {}).get("caption")
            media_url = wa_message.get("image", {}).get("id")
        elif message_type == "interactive":
            interactive = wa_message.get("interactive", {})
            interactive_type = interactive.get("type")
            if interactive_type == "nfm_reply":
                quick_reply_payload = interactive.get("nfm_reply", {}).get("id")
        
        return IncomingMessage(
            message_id=message_id,
            sender_phone=sender_phone,
            timestamp=timestamp,
            type=message_type,
            content=content,
            media_url=media_url,
            quick_reply_payload=quick_reply_payload,
        )

    async def send(self, user_id: str, message: OutgoingMessage) -> bool:
        import httpx
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": user_id,
            "recipient_type": "individual",
        }
        
        if message.type == "text" and message.text:
            payload["type"] = "text"
            payload["text"] = {"body": message.text}
        elif message.type == "image" and message.image_url:
            payload["type"] = "image"
            payload["image"] = {"link": message.image_url}
        elif message.type == "interactive" and message.buttons:
            payload["type"] = "interactive"
            payload["interactive"] = {
                "type": "button",
                "body": {"text": message.text or ""},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": b.id, "title": b.title}}
                        for b in message.buttons
                    ]
                },
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.api_url, headers=headers, json=payload)
            return response.status_code == 200


def get_transport() -> MessageTransport:
    if settings.transport == "mock":
        return MockTransport()
    elif settings.transport == "whatsapp":
        return WhatsAppTransport()
    else:
        raise ValueError(f"Unsupported transport: {settings.transport}")
