import re
from app.agents.base import GatekeeperAgent
from app.models.message import OutgoingMessage


class GatekeeperAgentImpl(GatekeeperAgent):
    BLOCKED_PATTERNS = [
        r"call.*police",
        r"call.*911",
        r"call.*999",
        r"call.*000",
        r"emergency services",
        r"emergencies",
        r"looks (sad|angry|scared|anxious|depressed|worried|upset)",
        r"your (friend|family|wife|husband|child|son|daughter|mom|dad)",
        r"the (friend|family|wife|husband|child|son|daughter|mom|dad)",
    ]

    async def validate_response(self, response: OutgoingMessage, context: dict) -> OutgoingMessage:
        if response.text:
            response.text = self._redact_response(response.text)
        
        return response

    def _redact_response(self, text: str) -> str:
        for pattern in self.BLOCKED_PATTERNS:
            text = re.sub(pattern, "[REDACTED]", text, flags=re.IGNORECASE)
        
        return text

    async def check_escalation_safety(self, event: dict) -> bool:
        return False
