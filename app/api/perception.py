from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from app.models.scene import SceneDescriptor
from app.models.user import Camera, Scene, User, AlertRule, Event
from app.models.event import DEFAULT_RULES
from app.services.storage import AsyncSessionLocal
from app.agents.event import EventAgentImpl
from app.agents.communication import get_transport
from app.models.message import OutgoingMessage
from datetime import datetime
import uuid

router = APIRouter()


@router.post("/cameras/{device_id}/scenes")
async def upload_scene(device_id: str, scene_data: SceneDescriptor):
    """
    Upload a new scene descriptor from a camera.
    """
    async with AsyncSessionLocal() as session:
        # 1. Find or create camera
        stmt = select(Camera).where(Camera.device_id == device_id)
        result = await session.execute(stmt)
        camera = result.scalar_one_or_none()

        if not camera:
            # Auto-register camera (linked to a default admin user or orphan?)
            # For now, let's create it as an orphan or link to the first user found
            stmt = select(User).limit(1)
            user_result = await session.execute(stmt)
            user = user_result.scalar_one_or_none()

            if not user:
                raise HTTPException(
                    status_code=400, detail="No users registered to claim this camera"
                )

            camera = Camera(device_id=device_id, user_id=user.id, name=f"Camera {device_id[:6]}")
            session.add(camera)
            await session.commit()
            await session.refresh(camera)
        else:
            # Ensure user is loaded
            stmt = select(User).where(User.id == camera.user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

        # 2. Save Scene
        # SceneDescriptor objects are Pydantic models, need to convert to dict
        objects_json = [obj.model_dump() for obj in scene_data.objects]

        db_scene = Scene(
            camera_id=camera.id,
            captured_at=scene_data.timestamp,
            objects=objects_json,
            motion=scene_data.motion,
            motion_score=scene_data.motion_score,
            snapshot_url=scene_data.snapshot_url,
            enhanced=scene_data.enhanced,
            received_at=datetime.utcnow(),
        )

        session.add(db_scene)
        await session.commit()
        await session.refresh(db_scene)  # Get ID

        # 3. Event Evaluation
        if user:
            # Load Alert Rules
            stmt = select(AlertRule).where(AlertRule.user_id == user.id)
            result = await session.execute(stmt)
            rules = result.scalars().all()

            # Initialize default rules if none exist
            if not rules:
                rules = []
                for rule_def in DEFAULT_RULES:
                    new_rule = AlertRule(
                        user_id=user.id,
                        camera_id=camera.id,  # Optional: bind to this camera or all?
                        name=rule_def["name"],
                        enabled=True,
                        trigger_type=rule_def["trigger"]["type"],
                        trigger_config=rule_def["trigger"],
                        conditions=rule_def["conditions"],
                        severity=rule_def["severity"],
                        cooldown_seconds=300,  # Default 5 min
                    )
                    session.add(new_rule)
                    rules.append(new_rule)
                await session.commit()
                # Refresh rules to get IDs if needed, but we have objects

            # Run Event Agent
            event_agent = EventAgentImpl()
            context = {"rules": rules, "user_status": user.status}

            event_result = await event_agent.evaluate(scene_data, context)

            if event_result:
                rule_id = event_result["rule_id"]

                # Create Event Record
                new_event = Event(
                    camera_id=camera.id,
                    user_id=user.id,
                    scene_id=db_scene.id,
                    event_type="alert",
                    severity=event_result["severity"],
                    title=f"Alert: {event_result['rule_name']}",
                    description=f"Triggered by {event_result['rule_name']}",
                    extra_metadata={"rule_id": str(rule_id)},
                )
                session.add(new_event)

                # Update Rule Cooldown
                stmt = select(AlertRule).where(AlertRule.id == uuid.UUID(rule_id))
                result = await session.execute(stmt)
                triggered_rule = result.scalar_one()
                triggered_rule.last_triggered_at = datetime.utcnow()

                await session.commit()

                # Send Notification
                transport = get_transport()
                message_text = f"⚠️ *{event_result['rule_name']}*\n"
                if scene_data.objects:
                    obj_summary = ", ".join(
                        [f"{o.type} ({int(o.confidence * 100)}%)" for o in scene_data.objects]
                    )
                    message_text += f"Objects: {obj_summary}"

                if scene_data.snapshot_url:
                    await transport.send(
                        str(user.telegram_id),
                        OutgoingMessage(
                            type="photo",
                            photo_url=scene_data.snapshot_url,
                            text=message_text,
                            parse_mode="Markdown",
                        ),
                    )
                else:
                    await transport.send(
                        str(user.telegram_id),
                        OutgoingMessage(type="text", text=message_text, parse_mode="Markdown"),
                    )

        return {"status": "recorded", "scene_id": str(db_scene.id)}


@router.get("/cameras/{device_id}/status")
async def get_camera_status(device_id: str):
    """Heartbeat check"""
    async with AsyncSessionLocal() as session:
        stmt = select(Camera).where(Camera.device_id == device_id)
        result = await session.execute(stmt)
        camera = result.scalar_one_or_none()

        if not camera:
            raise HTTPException(status_code=404, detail="Camera not found")

        return {
            "device_id": camera.device_id,
            "is_active": camera.is_active,
            "last_heartbeat": camera.last_heartbeat,
        }
