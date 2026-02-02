from datetime import datetime, timedelta
from app.agents.base import EventAgent
from app.models.scene import SceneDescriptor
from app.models.event import AlertTrigger, AlertCondition, AlertRule as AlertRuleModel, DEFAULT_RULES


class EventAgentImpl(EventAgent):
    def __init__(self, rules: list[dict] | None = None):
        self.rules = rules or DEFAULT_RULES
        self.cooldowns: dict[str, datetime] = {}

    async def evaluate(self, scene: SceneDescriptor, context: dict) -> dict | None:
        for rule_config in self.rules:
            rule = AlertRuleModel(**rule_config)
            
            if not rule.enabled:
                continue
            
            if self._check_cooldown(rule):
                continue
            
            if self._evaluate_trigger(rule.trigger, scene):
                if self._evaluate_conditions(rule.conditions, context):
                    self._update_cooldown(rule.id, rule.cooldown_seconds)
                    
                    return {
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "severity": rule.severity,
                        "scene": scene,
                        "context": context,
                    }
        
        return None

    def _check_cooldown(self, rule: AlertRuleModel) -> bool:
        if rule.id not in self.cooldowns:
            return False
        
        return datetime.utcnow() < self.cooldowns[rule.id]

    def _update_cooldown(self, rule_id: str, cooldown_seconds: int):
        self.cooldowns[rule_id] = datetime.utcnow() + timedelta(seconds=cooldown_seconds)

    def _evaluate_trigger(self, trigger: AlertTrigger, scene: SceneDescriptor) -> bool:
        if trigger.type == "motion":
            return scene.motion
        elif trigger.type == "object_detected":
            if not trigger.object_type:
                return len(scene.objects) > 0
            
            for obj in scene.objects:
                if obj.type == trigger.object_type and obj.confidence >= trigger.confidence_threshold:
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
