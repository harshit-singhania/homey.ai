import random
from datetime import datetime, timedelta
from app.agents.base import PerceptionAgent
from app.models.scene import SceneDescriptor, DetectedObject


class MockPerceptionAgent(PerceptionAgent):
    def __init__(self):
        self.scenarios = [
            {"objects": [], "motion": False},
            {"objects": [{"type": "cat", "confidence": 0.92}], "motion": True},
            {"objects": [{"type": "person", "confidence": 0.85}], "motion": True},
            {"objects": [{"type": "dog", "confidence": 0.78}], "motion": True},
            {"objects": [{"type": "person", "confidence": 0.72}, {"type": "cat", "confidence": 0.88}], "motion": True},
        ]
        self.scene_history: dict[str, list[SceneDescriptor]] = {}

    async def get_latest_scene(self, camera_id: str) -> SceneDescriptor:
        scenario = random.choice(self.scenarios)
        
        scene = SceneDescriptor(
            camera_id=camera_id,
            timestamp=datetime.utcnow(),
            objects=[DetectedObject(**o) for o in scenario["objects"]],
            motion=scenario["motion"],
            motion_score=random.random() if scenario["motion"] else None,
        )
        
        history = self.scene_history.get(camera_id, [])
        history.append(scene)
        self.scene_history[camera_id] = history[-100:]
        
        return scene

    async def get_scene_history(self, camera_id: str, since: datetime) -> list[SceneDescriptor]:
        history = self.scene_history.get(camera_id, [])
        return [s for s in history if s.timestamp >= since]

    async def request_snapshot(self, camera_id: str) -> str | None:
        return f"https://example.com/snapshots/{camera_id}/{datetime.utcnow().timestamp()}.jpg"
