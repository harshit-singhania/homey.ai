from fastapi import APIRouter, HTTPException, Depends
from app.models.scene import SceneDescriptor
from app.models.event import DEFAULT_RULES
from app.services.storage import db
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
    # 1. Find or create camera
    camera = await db.camera.find_unique(where={"device_id": device_id})

    if not camera:
        raise HTTPException(
            status_code=404, detail="Camera not registered. Please register device via admin."
        )

    # Ensure user is loaded
    user = await db.user.find_unique(where={"id": camera.user_id})

    # 2. Save Scene
    # SceneDescriptor objects are Pydantic models, need to convert to dict
    objects_json = [obj.model_dump() for obj in scene_data.objects]

    db_scene = await db.scene.create(
        data={
            "camera_id": camera.id,
            "captured_at": scene_data.timestamp,
            "objects": objects_json,
            "motion": scene_data.motion,
            "motion_score": scene_data.motion_score,
            "snapshot_url": scene_data.snapshot_url,
            "enhanced": scene_data.enhanced,
            "received_at": datetime.utcnow(),
        }
    )

    # 3. Event Evaluation
    if user:
        # Load Alert Rules
        rules = await db.alertrule.find_many(where={"user_id": user.id})

        # Initialize default rules if none exist
        if not rules:
            new_rules_data = []
            for rule_def in DEFAULT_RULES:
                new_rules_data.append({
                    "user_id": user.id,
                    "camera_id": camera.id,
                    "name": rule_def["name"],
                    "enabled": True,
                    "trigger_type": rule_def["trigger"]["type"],
                    "trigger_config": rule_def["trigger"],
                    "conditions": rule_def["conditions"],
                    "severity": rule_def["severity"],
                    "cooldown_seconds": 300,
                })
            
            if new_rules_data:
                await db.alertrule.create_many(data=new_rules_data)
                rules = await db.alertrule.find_many(where={"user_id": user.id})

            # Run Event Agent
            event_agent = EventAgentImpl()
            context = {"rules": rules, "user_status": user.status}

            event_result = await event_agent.evaluate(scene_data, context)

        if event_result:
            rule_id = event_result["rule_id"]

            # Create Event Record
            await db.event.create(
                data={
                    "camera_id": camera.id,
                    "user_id": user.id,
                    "scene_id": db_scene.id,
                    "event_type": "alert",
                    "severity": event_result["severity"],
                    "title": f"Alert: {event_result['rule_name']}",
                    "description": f"Triggered by {event_result['rule_name']}",
                    "extra_metadata": {"rule_id": str(rule_id)},
                }
            )

            # Update Rule Cooldown
            try:
                await db.alertrule.update(
                    where={"id": rule_id},
                    data={"last_triggered_at": datetime.utcnow()}
                )
            except Exception as e:
                print(f"Error updating rule cooldown: {e}")

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
    camera = await db.camera.find_unique(where={"device_id": device_id})

    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    return {
        "device_id": camera.device_id,
        "is_active": camera.is_active,
        "last_heartbeat": camera.last_heartbeat,
    }
