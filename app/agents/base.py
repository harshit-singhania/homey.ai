from typing import Protocol, Any
from app.models.scene import SceneDescriptor
from app.models.message import IncomingMessage, OutgoingMessage


class MessageTransport(Protocol):
    async def receive(self, raw_payload: dict) -> IncomingMessage: ...

    async def send(self, user_id: str, message: OutgoingMessage) -> bool: ...


class PerceptionAgent(Protocol):
    async def get_latest_scene(self, camera_id: str) -> SceneDescriptor: ...

    async def get_scene_history(self, camera_id: str, since: Any) -> list[SceneDescriptor]: ...

    async def request_snapshot(self, camera_id: str) -> str | None: ...


class ConversationAgent(Protocol):
    async def process(self, message: IncomingMessage, context: dict) -> OutgoingMessage: ...


class EventAgent(Protocol):
    async def evaluate(self, scene: SceneDescriptor, context: dict) -> dict | None: ...


class GatekeeperAgent(Protocol):
    async def validate_response(self, response: OutgoingMessage, context: dict) -> OutgoingMessage: ...
