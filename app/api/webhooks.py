from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import select
from app.config import settings
from app.agents.communication import get_transport
from app.agents.conversation import ConversationAgentImpl
from app.agents.perception import MockPerceptionAgent, DatabasePerceptionAgent
from app.services.storage import AsyncSessionLocal
from app.models.user import User, Conversation, Message
from app.models.message import IncomingMessage

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

        async with AsyncSessionLocal() as session:
            # 2. Database Persistence & Context
            # Find or create User
            stmt = select(User).where(User.telegram_id == incoming_message.sender_telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                user = User(
                    telegram_id=incoming_message.sender_telegram_id,
                    username=incoming_message.sender_username,
                    first_name=incoming_message.sender_username,  # Fallback
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)

            # Find or create active Conversation
            stmt = select(Conversation).where(
                Conversation.user_id == user.id, Conversation.is_active == True
            )
            result = await session.execute(stmt)
            conversation = result.scalar_one_or_none()

            if not conversation:
                conversation = Conversation(user_id=user.id)
                session.add(conversation)
                await session.commit()
                await session.refresh(conversation)

            # Save Incoming Message
            db_message = Message(
                conversation_id=conversation.id,
                direction="inbound",
                content=incoming_message.content or "",
                message_type=incoming_message.type,
                external_id=str(incoming_message.message_id),
            )
            session.add(db_message)
            await session.commit()

            # Load History (last 10 messages)
            # We need to format this for Gemini (user/model roles)
            # TODO: Add specific ordering and limits
            stmt = (
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .order_by(Message.created_at.desc())
                .limit(10)
            )
            result = await session.execute(stmt)
            recent_messages = result.scalars().all()

            # Convert to Gemini history format (oldest first)
            history = []
            for msg in reversed(recent_messages):
                role = "user" if msg.direction == "inbound" else "model"
                # Skip the current message we just added, effectively (or include it?
                # ConversationAgent appends the *current* message to history manually.
                # So we should provide history *excluding* the current one if the agent adds it.
                # But wait, the agent adds the current message content.
                # Let's filter out the message we just added by ID or just use all previous.)
                if msg.id == db_message.id:
                    continue
                history.append({"role": role, "parts": [msg.content]})

            # 3. Setup Agents
            # perception_agent = MockPerceptionAgent()
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
            out_db_message = Message(
                conversation_id=conversation.id,
                direction="outbound",
                content=outgoing_message.text
                or (outgoing_message.photo_url if outgoing_message.type == "photo" else ""),
                message_type=outgoing_message.type,
            )
            session.add(out_db_message)
            await session.commit()

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
