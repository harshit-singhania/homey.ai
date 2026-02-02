from datetime import datetime
from app.agents.base import ConversationAgent, PerceptionAgent
from app.models.message import IncomingMessage, OutgoingMessage, QuickReplyButton
from app.models.scene import SceneDescriptor, UserIntent
from app.services.gemini import generate_response, classify_intent
from app.models.event import DEFAULT_RULES


SYSTEM_PROMPT = """You are Homey, a friendly and concise home monitoring assistant.

## Your Capabilities
- Report current scene status (what objects are visible, motion detected)
- Describe what's happening at home based on camera data
- Send alerts when unusual activity occurs
- Answer questions about recent events

## Communication Style
- Be concise: 1-2 sentences for simple queries
- Be friendly but professional
- Use present tense for current state ("A cat is visible")
- Use past tense for events ("Motion was detected at 2:14 PM")

## Strict Rules (NEVER violate)
1. NEVER identify specific individuals ("your wife", "John") - only say "a person"
2. NEVER make emotional judgments ("looks worried", "seems upset")
3. NEVER suggest calling police or emergency services
4. NEVER diagnose medical conditions
5. NEVER share information about one user with another
6. If unsure, say "I'm not sure" rather than guessing

## Context
Current time: {current_time}
User status: {user_status}
User name: {user_name}

## Latest Scene Data
Camera: {camera_name}
Last updated: {scene_timestamp}
Objects detected: {objects_list}
Motion: {motion_status}

## Recent Events (last 24h)
{recent_events}
"""


RESPONSE_TEMPLATES = {
    "STATUS_CHECK": {
        "no_activity": "All quiet at home. No motion detected since {last_motion_time}.",
        "objects_present": "{object_list} {verb} currently visible. {motion_status}",
        "motion_only": "Motion detected {time_ago}. No specific objects identified.",
    },
    "OBJECT_QUERY": {
        "found": "Yes, {object_type} is visible. Confidence: {confidence}%.",
        "not_found": "I don't see {object_type} right now. Last seen: {last_seen}.",
        "never_seen": "I haven't detected {object_type} in recent history.",
    },
    "HELP": """Here's what I can do:
• "How are things?" - Get current status
• "Is my cat there?" - Check for specific objects
• "Send a picture" - Request snapshot
• "Set status to away" - Enable away mode alerts
• "Turn off alerts" - Disable notifications""",
}


class ConversationAgentImpl(ConversationAgent):
    def __init__(self, perception: PerceptionAgent):
        self.perception = perception

    async def process(self, message: IncomingMessage, context: dict) -> OutgoingMessage:
        intent = await classify_intent(message.content or "")
        
        if intent == UserIntent.STATUS_CHECK:
            return await self._handle_status_check(context)
        elif intent == UserIntent.OBJECT_QUERY:
            return await self._handle_object_query(message, context)
        elif intent == UserIntent.SNAPSHOT_REQUEST:
            return await self._handle_snapshot_request(context)
        elif intent == UserIntent.HELP:
            return OutgoingMessage(type="text", text=RESPONSE_TEMPLATES["HELP"])
        elif intent == UserIntent.SETTINGS:
            return OutgoingMessage(type="text", text="Settings updates coming soon.")
        elif intent == UserIntent.GREETING:
            return OutgoingMessage(type="text", text="Hi there! How can I help with your home today?")
        else:
            scene = context.get("latest_scene")
            prompt = SYSTEM_PROMPT.format(
                current_time=datetime.now().isoformat(),
                user_status=context.get("user_status", "home"),
                user_name=context.get("user_name", "User"),
                camera_name=scene.camera_id if scene else "N/A",
                scene_timestamp=scene.timestamp.isoformat() if scene else "N/A",
                objects_list=", ".join([o.type for o in scene.objects]) if scene and scene.objects else "None",
                motion_status="Motion detected" if scene and scene.motion else "No motion",
                recent_events=context.get("recent_events_summary", "None"),
            )
            
            history = context.get("conversation_history", [])
            history.append({"role": "user", "parts": [message.content or ""]})
            
            response_text = await generate_response(prompt, history)
            
            history.append({"role": "model", "parts": [response_text]})
            context["conversation_history"] = history
            
            return OutgoingMessage(type="text", text=response_text)

    async def _handle_status_check(self, context: dict) -> OutgoingMessage:
        scene: SceneDescriptor = context.get("latest_scene")
        
        if not scene or not scene.objects and not scene.motion:
            return OutgoingMessage(
                type="text",
                text="All quiet at home. No recent activity detected.",
            )
        
        if scene.objects:
            objects_str = ", ".join([f"{o.type} ({int(o.confidence * 100)}%)" for o in scene.objects])
            motion_str = "with motion" if scene.motion else "no motion"
            return OutgoingMessage(
                type="text",
                text=f"I can see: {objects_str}. {motion_str}.",
            )
        
        return OutgoingMessage(
            type="text",
            text="Motion detected recently. No specific objects identified.",
        )

    async def _handle_object_query(self, message: IncomingMessage, context: dict) -> OutgoingMessage:
        scene: SceneDescriptor = context.get("latest_scene")
        content_lower = (message.content or "").lower()
        
        if not scene:
            return OutgoingMessage(type="text", text="No scene data available right now.")
        
        for obj in scene.objects:
            if obj.type.lower() in content_lower:
                return OutgoingMessage(
                    type="text",
                    text=f"Yes, {obj.type} is visible. Confidence: {int(obj.confidence * 100)}%.",
                )
        
        return OutgoingMessage(
            type="text",
            text=f"I don't see that right now. The area appears empty.",
        )

    async def _handle_snapshot_request(self, context: dict) -> OutgoingMessage:
        camera_id = context.get("camera_id")
        if not camera_id:
            return OutgoingMessage(type="text", text="No camera configured.")
        
        snapshot_url = await self.perception.request_snapshot(camera_id)
        if snapshot_url:
            return OutgoingMessage(type="image", image_url=snapshot_url, text="Here's a snapshot from your home.")
        return OutgoingMessage(type="text", text="Unable to capture snapshot right now.")
