import google.generativeai as genai
from typing import Any
from app.config import settings

if settings.gemini_api_key:
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)
else:
    model = None


async def generate_response(prompt: str, history: list[dict[str, Any]] | None = None) -> str:
    if not model:
        raise ValueError("Gemini API key not configured")
    
    if history:
        chat = model.start_chat(history=history)
        response = chat.send_message(prompt)
    else:
        response = model.generate_content(prompt)
    
    return response.text


async def classify_intent(message: str) -> str:
    if not model:
        return "unknown"
    
    prompt = f"""Classify the user's intent from their message.

Possible intents:
- STATUS_CHECK: User asking about current home status ("how are things?", "what's happening?")
- OBJECT_QUERY: User asking about specific object/person ("is my cat there?", "anyone home?")
- SNAPSHOT_REQUEST: User wants to see an image ("show me", "send a picture")
- ALERT_ACK: User responding to alert ("VIEW", "IGNORE", "OK")
- ESCALATION_CONFIRM: User confirming/denying escalation ("YES", "NO")
- SETTINGS: User changing preferences ("turn off alerts", "set status to away")
- HELP: User asking what you can do ("help", "what can you do?")
- GREETING: Casual greeting ("hi", "hello")
- UNKNOWN: Cannot determine intent

User message: "{message}"

Respond with ONLY the intent name, nothing else."""
    
    response = model.generate_content(prompt)
    return response.text.strip().upper()
