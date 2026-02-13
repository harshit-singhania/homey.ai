from fastapi import APIRouter, Request, HTTPException
from app.config import settings
from app.agents.communication import get_transport
from app.agents.conversation import ConversationAgentImpl
from app.agents.perception import DatabasePerceptionAgent
from app.services.storage import db

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

    transport = get_transport()

    try:
        # 1. Parse Update
        incoming_message = await transport.receive(payload)

        # 2. Database Persistence & Context
        # Find or create User
        user = await db.user.find_unique(where={"telegram_id": incoming_message.sender_telegram_id})

        if not user:
            user = await db.user.create(
                data={
                    "telegram_id": incoming_message.sender_telegram_id,
                    "username": incoming_message.sender_username,
                    "first_name": incoming_message.sender_username,  # Fallback
                }
            )

        # Find or create active Conversation
        conversation = await db.conversation.find_first(
            where={
                "user_id": user.id,
                "is_active": True
            }
        )

        if not conversation:
            conversation = await db.conversation.create(
                data={"user_id": user.id}
            )

        # Save Incoming Message
        db_message = await db.message.create(
            data={
                "conversation_id": conversation.id,
                "direction": "inbound",
                "content": incoming_message.content or "",
                "message_type": incoming_message.type,
                "external_id": str(incoming_message.message_id),
            }
        )

        # Load History (last 10 messages)
        recent_messages = await db.message.find_many(
            where={"conversation_id": conversation.id},
            order={"created_at": "desc"},
            take=10
        )

        # Convert to Gemini history format (oldest first)
        history = []
        for msg in reversed(recent_messages):
            role = "user" if msg.direction == "inbound" else "model"
            # Skip the current message we just added, effectively (or include it?
            if msg.id == db_message.id:
                continue
            history.append({"role": role, "parts": [msg.content]})

        # 3. Setup Agents
        perception_agent = DatabasePerceptionAgent()
        conversation_agent = ConversationAgentImpl(perception=perception_agent)

        # 4. Build Context
        camera_id = "default_cam"
        scene = await perception_agent.get_latest_scene(camera_id)

        context = {
            "latest_scene": scene,
            "user_status": user.status,
            "user_name": user.first_name or user.username or "User",
            "conversation_history": history,
            "camera_id": camera_id,
            "recent_events_summary": "None",
        }

        # 5. Process Message
        outgoing_message = await conversation_agent.process(incoming_message, context)

        # 6. Send Response
        await transport.send(str(incoming_message.sender_telegram_id), outgoing_message)

        # 7. Save Outgoing Message
        await db.message.create(
            data={
                "conversation_id": conversation.id,
                "direction": "outbound",
                "content": outgoing_message.text
                or (outgoing_message.photo_url if outgoing_message.type == "photo" else ""),
                "message_type": outgoing_message.type,
            }
        )

    except ValueError as e:
        # Log parsing errors but return 200 to Telegram
        print(f"Error parsing update: {e}")
    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"Error processing webhook: {e}")
        # Optionally send an error message back to the user if we have their ID
        # but for now just log it to avoid loop

    update_id = payload.get("update_id")
    return {"status": "received", "update_id": update_id}
