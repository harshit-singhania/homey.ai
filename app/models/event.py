from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from typing import Literal


class AlertTrigger(BaseModel):
    type: Literal["motion", "object_detected", "object_absent", "no_motion"]
    object_type: Optional[str] = None
    confidence_threshold: float = 0.7


class AlertCondition(BaseModel):
    type: Literal["time_range", "user_status", "day_of_week"]
    value: str | dict


class AlertRule(BaseModel):
    id: str
    name: str
    enabled: bool = True
    trigger: AlertTrigger
    conditions: list[AlertCondition] = Field(default_factory=list)
    cooldown_seconds: int = 300
    severity: Literal["low", "medium", "high"] = "medium"


class Event(BaseModel):
    id: str
    camera_id: str
    user_id: str
    scene_id: Optional[str] = None
    event_type: str
    severity: Literal["low", "medium", "high"] = "medium"
    title: Optional[str] = None
    description: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    response: Optional[str] = None
    created_at: datetime


DEFAULT_RULES: list[dict] = [
    {
        "id": "motion_when_away",
        "name": "Motion while away",
        "trigger": {"type": "motion"},
        "conditions": [{"type": "user_status", "value": {"status": "away"}}],
        "severity": "medium",
    },
    {
        "id": "person_at_night",
        "name": "Person detected at night",
        "trigger": {"type": "object_detected", "object_type": "person"},
        "conditions": [{"type": "time_range", "value": "22:00-06:00"}],
        "severity": "high",
    },
    {
        "id": "package_detected",
        "name": "Package detected",
        "trigger": {"type": "object_detected", "object_type": "package"},
        "conditions": [],
        "severity": "low",
    },
]
