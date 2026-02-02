from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from typing import Literal


class DetectedObject(BaseModel):
    type: str  # "person", "cat", "dog", "package", etc.
    confidence: float  # 0.0 - 1.0
    bbox: Optional[list[int]] = None  # [x1, y1, x2, y2]


class SceneDescriptor(BaseModel):
    camera_id: str
    timestamp: datetime
    objects: list[DetectedObject] = Field(default_factory=list)
    motion: bool = False
    motion_score: Optional[float] = None
    snapshot_url: Optional[str] = None
    enhanced: bool = False


class UserIntent(str):
    STATUS_CHECK = "status_check"
    OBJECT_QUERY = "object_query"
    SNAPSHOT_REQUEST = "snapshot"
    ALERT_ACKNOWLEDGE = "alert_ack"
    ESCALATION_CONFIRM = "escalate"
    HELP = "help"
    SETTINGS = "settings"
    GREETING = "greeting"
    UNKNOWN = "unknown"
