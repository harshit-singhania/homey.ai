from fastapi import APIRouter, Request, HTTPException
from app.config import settings

router = APIRouter()


@router.get("/messages")
async def webhook_verify(request: Request):
    if settings.transport == "mock":
        return {"status": "mock mode - verification not required"}
    
    hub_mode = request.query_params.get("hub.mode")
    hub_verify_token = request.query_params.get("hub.verify_token")
    hub_challenge = request.query_params.get("hub.challenge")
    
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return hub_challenge
    
    raise HTTPException(status_code=403, detail="Invalid verification token")


@router.post("/messages")
async def webhook_receive(request: Request):
    if settings.transport == "mock":
        return {"status": "mock mode - use /api/v1/mock/send instead"}
    
    payload = await request.json()
    
    return {"status": "received", "entry_count": len(payload.get("entry", []))}
