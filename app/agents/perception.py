import random
from datetime import datetime, timedelta
from sqlalchemy import select
from app.agents.base import PerceptionAgent
from app.models.scene import SceneDescriptor, DetectedObject
from app.models.user import Scene, Camera
from app.services.storage import AsyncSessionLocal


class MockPerceptionAgent(PerceptionAgent):
    def __init__(self):
        self.scenarios = [
            {"objects": [], "motion": False},
            {"objects": [{"type": "cat", "confidence": 0.92}], "motion": True},
            {"objects": [{"type": "person", "confidence": 0.85}], "motion": True},
            {"objects": [{"type": "dog", "confidence": 0.78}], "motion": True},
            {
                "objects": [
                    {"type": "person", "confidence": 0.72},
                    {"type": "cat", "confidence": 0.88},
                ],
                "motion": True,
            },
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


class DatabasePerceptionAgent(PerceptionAgent):
    """Perception agent that retrieves real data from the database"""

    async def get_latest_scene(self, camera_id: str) -> SceneDescriptor:
        async with AsyncSessionLocal() as session:
            # Query latest scene for this camera (by device_id)
            stmt = (
                select(Scene)
                .join(Camera)
                .where(Camera.device_id == camera_id)
                .order_by(Scene.captured_at.desc())
                .limit(1)
            )
            result = await session.execute(stmt)
            db_scene = result.scalar_one_or_none()

            if not db_scene:
                return SceneDescriptor(
                    camera_id=camera_id, timestamp=datetime.utcnow(), objects=[], motion=False
                )

            return SceneDescriptor(
                camera_id=camera_id,
                timestamp=db_scene.captured_at,
                objects=[DetectedObject(**obj) for obj in db_scene.objects],
                motion=db_scene.motion,
                motion_score=db_scene.motion_score,
                snapshot_url=db_scene.snapshot_url,
                enhanced=db_scene.enhanced,
            )

    async def get_scene_history(self, camera_id: str, since: datetime) -> list[SceneDescriptor]:
        async with AsyncSessionLocal() as session:
            stmt = (
                select(Scene)
                .join(Camera)
                .where(Camera.device_id == camera_id, Scene.captured_at >= since)
                .order_by(Scene.captured_at.asc())
            )
            result = await session.execute(stmt)
            db_scenes = result.scalars().all()

            return [
                SceneDescriptor(
                    camera_id=camera_id,
                    timestamp=s.captured_at,
                    objects=[DetectedObject(**obj) for obj in s.objects],
                    motion=s.motion,
                    motion_score=s.motion_score,
                    snapshot_url=s.snapshot_url,
                    enhanced=s.enhanced,
                )
                for s in db_scenes
            ]

    async def request_snapshot(self, camera_id: str) -> str | None:
        # For now, return the latest snapshot URL from DB if available
        # In future, this would trigger a push notification to Android
        scene = await self.get_latest_scene(camera_id)
        return scene.snapshot_url
