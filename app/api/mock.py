from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class MockIncomingMessage(BaseModel):
    phone_number: str
    message_type: str = "text"
    content: Optional[str] = None
    media_url: Optional[str] = None


class MockOutgoingMessage(BaseModel):
    message_id: str
    phone_number: str
    message_type: str
    text: Optional[str] = None
    image_url: Optional[str] = None
    buttons: Optional[list[dict]] = None


mock_message_queue: list[MockOutgoingMessage] = []


@router.post("/send")
async def mock_send_message(message: MockIncomingMessage):
    message_id = f"msg_{len(mock_message_queue)}"
    
    return {
        "status": "processed",
        "message_id": message_id,
        "phone_number": message.phone_number,
    }


@router.get("/messages")
async def get_mock_messages():
    return {"messages": mock_message_queue}


@router.delete("/messages")
async def clear_mock_messages():
    mock_message_queue.clear()
    return {"status": "cleared", "count": 0}
