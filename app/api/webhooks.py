from fastapi import APIRouter, Request, HTTPException
from app.config import settings

router = APIRouter()


@router.post("/telegram")
async def telegram_webhook(request: Request):
    """
    Telegram webhook endpoint.
    Receives Update objects from Telegram Bot API.

    Telegram doesn't require GET verification like WhatsApp - just set webhook URL via API:
    curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
      -H "Content-Type: application/json" \
      -d '{"url": "https://your-domain.com/webhooks/telegram"}'
    """
    if settings.transport == "mock":
        return {"status": "mock mode - use /api/v1/mock/send instead"}

    payload = await request.json()

    # TODO: Validate webhook secret if configured
    # if settings.telegram_webhook_secret:
    #     # Verify X-Telegram-Bot-Api-Secret-Token header
    #     secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    #     if secret_header != settings.telegram_webhook_secret:
    #         raise HTTPException(status_code=403, detail="Invalid webhook secret")

    # TODO: Process the Telegram update
    # This is where we'd integrate with the Communication Agent:
    # 1. Parse Update using TelegramTransport.receive(payload)
    # 2. Pass to Conversation Agent
    # 3. Get response from agents
    # 4. Send back via TelegramTransport.send()

    update_id = payload.get("update_id")
    return {"status": "received", "update_id": update_id}
