from datetime import datetime, timedelta
from typing import Optional, Any
from app.agents.base import EventAgent
from app.models.scene import SceneDescriptor
from app.models.event import (
    AlertTrigger,
    AlertCondition,
    AlertRule as AlertRuleModel,
    DEFAULT_RULES,
)


class EventAgentImpl(EventAgent):
    def __init__(self):
        pass

    async def evaluate(self, scene: SceneDescriptor, context: dict) -> dict | None:
        """
        Evaluate scene against a list of rules provided in context.
        context must contain:
        - "rules": list[dict] or list[SQLAlchemy Model] representing alert rules
        - "user_status": str
        """
        rules = context.get("rules", [])

        # If no rules provided, fallback to default rules (but only if explicitly requested or empty)
        if not rules:
            # We convert DEFAULT_RULES dicts to objects if needed,
            # but usually we want DB rules.
            # For now, let's just return None if no rules are passed to avoid noise.
            return None

        for rule_obj in rules:
            # Handle Prisma models, dicts, or Pydantic models
            if isinstance(rule_obj, dict):
                rule = AlertRuleModel(**rule_obj)
                last_triggered = None
            else:
                # Handle Prisma model or other object
                rule = AlertRuleModel(
                    id=str(getattr(rule_obj, "id")),
                    name=getattr(rule_obj, "name"),
                    enabled=getattr(rule_obj, "enabled"),
                    trigger=getattr(rule_obj, "trigger_config"),
                    conditions=getattr(rule_obj, "conditions"),
                    cooldown_seconds=getattr(rule_obj, "cooldown_seconds"),
                    severity=getattr(rule_obj, "severity"),
                )
                last_triggered = getattr(rule_obj, "last_triggered_at", None)

            if not rule.enabled:
                continue

            # Check Cooldown
            if self._check_cooldown(last_triggered, rule.cooldown_seconds):
                continue

            # Check Trigger & Conditions
            if self._evaluate_trigger(rule.trigger, scene):
                if self._evaluate_conditions(rule.conditions, context):
                    return {
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "severity": rule.severity,
                        "scene": scene,
                        "context": context,
                    }

        return None

    def _check_cooldown(self, last_triggered_at: datetime | None, cooldown_seconds: int) -> bool:
        if not last_triggered_at:
            return False

        # Ensure timezone awareness compatibility
        now = datetime.utcnow()
        if last_triggered_at.tzinfo:
            now = now.replace(tzinfo=last_triggered_at.tzinfo)

        return now < (last_triggered_at + timedelta(seconds=cooldown_seconds))

    def _evaluate_trigger(self, trigger: AlertTrigger, scene: SceneDescriptor) -> bool:
        if trigger.type == "motion":
            return scene.motion
        elif trigger.type == "object_detected":
            if not trigger.object_type:
                return len(scene.objects) > 0

            for obj in scene.objects:
                if (
                    obj.type == trigger.object_type
                    and obj.confidence >= trigger.confidence_threshold
                ):
                    return True
            return False
        elif trigger.type == "object_absent":
            if not trigger.object_type:
                return len(scene.objects) == 0

            for obj in scene.objects:
                if obj.type == trigger.object_type:
                    return False
            return True
        elif trigger.type == "no_motion":
            return not scene.motion

        return False

    def _evaluate_conditions(self, conditions: list[AlertCondition], context: dict) -> bool:
        if not conditions:
            return True

        for condition in conditions:
            if condition.type == "user_status":
                if isinstance(condition.value, dict):
                    expected_status = condition.value.get("status")
                    current_status = context.get("user_status")
                    if expected_status != current_status:
                        return False
            elif condition.type == "time_range":
                if isinstance(condition.value, str):
                    if not self._check_time_range(condition.value):
                        return False
            elif condition.type == "day_of_week":
                if isinstance(condition.value, str):
                    current_day = datetime.utcnow().strftime("%A").lower()
                    if current_day != condition.value.lower():
                        return False

        return True

    def _check_time_range(self, time_range: str) -> bool:
        try:
            start_str, end_str = time_range.split("-")
            start_hour = int(start_str.split(":")[0])
            end_hour = int(end_str.split(":")[0])

            current_hour = datetime.utcnow().hour

            if start_hour <= end_hour:
                return start_hour <= current_hour < end_hour
            else:
                return current_hour >= start_hour or current_hour < end_hour
        except (ValueError, IndexError):
            return False
