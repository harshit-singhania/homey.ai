AGENTS.md — Homey.ai

Homey.ai is a WhatsApp-first conversational surveillance system that turns a smartphone camera into an intelligent safety monitor. Users interact entirely through natural language over WhatsApp. The system detects activity, summarizes scene state, and responds to user queries.

Overview

Homey.ai is built with agentic components that perform distinct roles:
	1.	Perception Agent – Visual scene understanding on device
	2.	Communication Agent – WhatsApp message handling
	3.	Conversation Agent – Natural language interpretation & response
	4.	Event Agent – Incident detection & alert generation
	5.	Decision Gatekeeper – Safety checks & human-in-loop escalation

This document describes each agent’s role, responsibilities, and boundaries.

1. Perception Agent

Purpose

Extract structured visual and activity information from the surveillance phone’s camera feed.

Responsibilities
	•	Run object detection (e.g., using YOLOv10)
	•	Infer presence of people, animals, motion
	•	Generate structured scene descriptors (object type, bounding box, confidence)

Modes
	•	Offline Mode — inference runs completely locally
	•	Online Mode — enhanced models used via cloud APIs when internet is available

Output

A structured JSON scene description, e.g.:

{
  "timestamp": 1627635123,
  "objects": [
    { "type": "person", "confidence": 0.78 },
    { "type": "cat", "confidence": 0.85 }
  ],
  "motion": true
}

Rules
	•	No facial recognition
	•	No identification of individuals
	•	No emotional inference

⸻

2. Communication Agent

Purpose

Interface with WhatsApp using the WhatsApp Cloud API to receive and send messages.

Responsibilities
	•	Listen to incoming WhatsApp webhook events
	•	Normalize user messages (text, media, quick replies)
	•	Deliver messages to the Conversation Agent
	•	Send replies back to users
	•	Format structured responses (text, images, quick reply buttons)

Constraints
	•	All interactions are user-initiated or alert-triggered
	•	No unsolicited messaging except event alerts
	•	Must respect WhatsApp policy and rate limits

⸻

3. Conversation Agent

Purpose

Interpret user intent and generate responses grounded in scene data or history.

Responsibilities
	•	Parse natural language requests
	•	Map queries to system actions (status, snapshot, explanation)
	•	Use LLM(s) for interpretation and text generation
	•	Follow domain-specific rules for surveillance communication

Examples

User → “Hey Homey, how are things at home?”
Response → “No unusual activity. Last motion detected 3h ago.”

User → “Can you see my cat?”
Response → “Yes. A cat is present at 02:14 PM in the center of the room.”

Safety Boundaries
	•	Descriptive responses only
	•	No medical or emotional judgments
	•	No inference about identity

⸻

4. Event Agent

Purpose

Monitor perception outputs over time and detect noteworthy events.

Responsibilities
	•	Track scene changes and motion history
	•	Apply rule-based logic for alerts
	•	Assign confidence scores to events
	•	Trigger alert messages via the Communication Agent

Alert Triggers

Examples:
	•	Motion when the user is “away”
	•	Presence of a person during restricted hours
	•	Repeated activity above a threshold

Alert Message Format

Alerts should be concise and actionable, e.g:

⚠️ Motion detected at 02:14 AM
Objects: person (78%)
Reply VIEW or IGNORE


⸻

5. Decision Gatekeeper

Purpose

Act as the human-in-the-loop control layer to prevent unsafe or autonomous actions.

Responsibilities
	•	Validate responses before sending
	•	Enforce safety policies
	•	Confirm escalations only after explicit user consent

No-Action Rules
	•	The system must not contact law enforcement
	•	Must not autonomously call emergency services
	•	Must not label emotional or medical states

The Decision Gatekeeper can prompt the user:

Reply YES to confirm escalation
Reply NO to ignore


⸻

Agent Interaction Workflow

User (WhatsApp) ──> Communication Agent
                     │
                     ▼
           Conversation Agent ──> Perception Agent
                     │               │
                     ▼               ▼
                 Decision Gatekeeper ◀─ Event Agent
                     │
                     ▼
            Communication Agent ──> User


⸻

Closed-Loop Cases

Status Query
	1.	User: “How are things at home?”
	2.	Conversation Agent interprets intent
	3.	Perception Agent retrieves latest scene
	4.	Decision Gatekeeper formats response
	5.	Communication Agent sends it to WhatsApp

Alert Trigger
	1.	Perception Agent detects motion
	2.	Event Agent evaluates severity
	3.	Decision Gatekeeper creates alert
	4.	Communication Agent pushes alert message

⸻

Safety and Ethical Boundaries

Homey.ai must follow ethical guidelines:

Restriction	Reason
No facial recognition	Privacy, legal risks
No emotional inference	Safety, liability
No autonomous enforcement	Prevent misuse
No public space monitoring	Consent required

All agents enforce these boundaries.

⸻

Notes on Offline vs Online intelligence
	•	Offline: Perception Agent uses local, lightweight models
	•	Online: Enhanced reasoning via cloud LLMs and vision APIs
	•	Conversation Agent blends both gracefully

Users should not notice backend mode changes.

⸻

Glossary
	•	Scene Descriptor: Structured representation of what was seen
	•	Alert: Event notification to user
	•	Quick Reply: WhatsApp button to reduce friction

⸻

Deployment Considerations
	•	Webhook listener must be reachable (HTTPS)
	•	Surveillance phone must run inference service (e.g., Android background agent)
	•	Communication Agent must handle retries
	•	Logging must respect privacy

⸻

Implementation Plan
===================

This section provides complete technical specifications for implementing Homey.ai, intended as a reference for LLMs and agents working on the project.

Technology Stack
----------------

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Backend | Python 3.11+ / FastAPI | Async support, type hints, rapid development |
| LLM | Google Gemini | Strong multimodal capabilities, cost-effective |
| Database | PostgreSQL | Relational reliability, JSON support, time-series queries |
| Cache/Queue | Redis | Task queue, caching, pub/sub for real-time |
| Perception | Hybrid: Android (YOLO) + Cloud (Gemini Vision) | Offline capability + enhanced reasoning |
| WhatsApp | Meta Cloud API (swappable with mock) | Production transport, mock for dev |
| ORM | SQLAlchemy | Mature Python ORM with async support |
| Migrations | Alembic | Database version control |
| Deployment | Docker + Railway/Render | Containerized, managed services |

Project Structure
-----------------

```
homeyai/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI entry point
│   ├── config.py                  # Settings, environment variables
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py                # Base agent interface
│   │   ├── communication.py       # WhatsApp message handling
│   │   ├── conversation.py        # LLM intent & response
│   │   ├── perception.py          # Scene descriptor interface
│   │   ├── event.py               # Alert detection logic
│   │   └── gatekeeper.py          # Safety validation
│   ├── models/
│   │   ├── __init__.py
│   │   ├── scene.py               # Scene, Object, Motion schemas
│   │   ├── event.py               # Alert, EventType schemas
│   │   ├── user.py                # User, Conversation state
│   │   └── message.py             # WhatsApp message models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── whatsapp.py           # WhatsApp Cloud API client
│   │   ├── gemini.py              # Gemini LLM integration
│   │   └── storage.py             # PostgreSQL operations
│   ├── api/
│   │   ├── __init__.py
│   │   ├── webhooks.py            # WhatsApp webhook endpoints
│   │   ├── perception.py          # Phone → Server scene upload
│   │   ├── mock.py                # Mock testing interface
│   │   └── health.py              # Health checks
│   └── utils/
│       ├── __init__.py
│       └── safety.py             # Safety policy enforcement
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── alembic/                       # Database migrations
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── pyproject.toml
├── .env.example
└── AGENTS.md                      # This file
```

Detailed Agent Specifications
-----------------------------

### Communication Agent

The Communication Agent handles all message transport between users and the system. It supports both WhatsApp Cloud API (production) and a mock transport (development/testing).

Interface Protocol
````python
class MessageTransport(Protocol):
    async def receive(self, raw_payload: dict) -> IncomingMessage: ...
    async def send(self, user_id: str, message: OutgoingMessage) -> bool: ...

class MockTransport(MessageTransport):
    """For local dev & testing - REST-based interface"""

class WhatsAppTransport(MessageTransport):
    """Real WhatsApp Cloud API integration"""
````

Message Schemas
````python
class IncomingMessage(BaseModel):
    message_id: str
    sender_phone: str
    timestamp: datetime
    type: Literal["text", "image", "quick_reply", "location"]
    content: str | None
    media_url: str | None
    quick_reply_payload: str | None

class OutgoingMessage(BaseModel):
    type: Literal["text", "image", "interactive"]
    text: str | None
    image_url: str | None
    buttons: list[QuickReplyButton] | None

class QuickReplyButton(BaseModel):
    id: str
    title: str  # max 20 chars
````

Responsibilities:
- Validate webhook signatures (WhatsApp) or API keys (mock)
- Parse message types: text, image, quick reply, location
- Extract sender phone, timestamp, message_id
- Normalize to IncomingMessage schema
- Deduplicate (WhatsApp sends retries)
- Format outgoing messages for transport
- Handle rate limiting & retries
- Track delivery status (sent, delivered, read)

API Endpoints:
- POST /webhooks/messages - Receive incoming messages
- GET /webhooks/messages - WhatsApp verification challenge
- POST /api/v1/mock/send - Simulate user sending message (mock only)
- GET /api/v1/mock/messages - View sent messages (mock only)

---

### Conversation Agent

The Conversation Agent uses Google Gemini to interpret user intent and generate contextual responses grounded in scene data and event history.

Intent Classification
````python
class UserIntent(Enum):
    STATUS_CHECK = "status_check"        # "How are things?"
    OBJECT_QUERY = "object_query"        # "Can you see my cat?"
    SNAPSHOT_REQUEST = "snapshot"        # "Send me a picture"
    ALERT_ACKNOWLEDGE = "alert_ack"      # "VIEW", "IGNORE"
    ESCALATION_CONFIRM = "escalate"      # "YES", "NO"
    HELP = "help"                        # "What can you do?"
    SETTINGS = "settings"                # "Turn off alerts"
    GREETING = "greeting"                # "Hi", "Hello"
    UNKNOWN = "unknown"
````

System Prompt Template
````python
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
````

Intent Classification Prompt
````python
INTENT_PROMPT = """Classify the user's intent from their message.

Possible intents:
- STATUS_CHECK: User asking about current home status ("how are things?", "what's happening?")
- OBJECT_QUERY: User asking about specific object/person ("is my cat there?", "anyone home?")
- SNAPSHOT_REQUEST: User wants to see an image ("show me", "send a picture")
- ALERT_ACK: User responding to alert ("VIEW", "IGNORE", "OK")
- ESCALATION_CONFIRM: User confirming/denying escalation ("YES", "NO")
- SETTINGS: User changing preferences ("turn off alerts", "set status to away")
- HELP: User asking what you can do ("help", "what can you do?")
- GREETING: Casual greeting ("hi", "hello")
- UNKNOWN: Cannot determine intent

User message: "{message}"

Respond with ONLY the intent name, nothing else."""
````

Response Templates
````python
RESPONSE_TEMPLATES = {
    "STATUS_CHECK": {
        "no_activity": "All quiet at home. No motion detected since {last_motion_time}.",
        "objects_present": "{object_list} {verb} currently visible. {motion_status}",
        "motion_only": "Motion detected {time_ago}. No specific objects identified.",
    },
    "OBJECT_QUERY": {
        "found": "Yes, {object_type} is visible in the {location}. Confidence: {confidence}%.",
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
````

Few-Shot Examples
````python
FEW_SHOT_EXAMPLES = [
    {
        "scene": {"objects": [{"type": "cat", "confidence": 0.92}], "motion": False},
        "user": "How are things at home?",
        "response": "All quiet! Your cat is lounging around. No unusual activity."
    },
    {
        "scene": {"objects": [{"type": "person", "confidence": 0.78}], "motion": True},
        "user": "What's happening?",
        "response": "Motion detected. A person is currently visible in frame."
    },
    {
        "scene": {"objects": [], "motion": False},
        "user": "Can you see my dog?",
        "response": "I don't see a dog right now. The area appears empty."
    },
]
````

Processing Flow:
1. IncomingMessage from Communication Agent
2. Intent Classification → Gemini with few-shot examples
3. Context Retrieval → Latest scene, user preferences, conversation history
4. Response Generation → Gemini with system prompt + context
5. Safety Check → Gatekeeper validates
6. OutgoingMessage → Communication Agent

---

### Perception Agent

The Perception Agent extracts structured visual information from the surveillance phone's camera feed using a hybrid local/cloud approach.

Architecture
````text
ANDROID SURVEILLANCE PHONE
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Camera    │───▶│  Frame       │───▶│  YOLO Detector  │
│   Service   │    │  Sampler     │    │  (Ultralytics)  │
└─────────────┘    │  (1-5 FPS)   │    └────────┬────────┘
                   └──────────────┘             │
                                               ▼
              ┌─────────────────────────────────────────┐
              │              Scene Aggregator           │
              │  • Debounce rapid changes (500ms window) │
              │  • Track object persistence              │
              │  • Motion detection via diff             │
              └────────────────────────┬────────────────┘
                                       │
              ┌────────────────────────▼────────────────┐
              │           Offline Buffer                │
              │  • SQLite queue for scenes              │
              │  • Auto-sync when connectivity restored  │
              └────────────────────────┬────────────────┘
                                       │ HTTPS
                                       ▼
                              BACKEND SERVER
                    POST /api/v1/cameras/{id}/scenes
````

Android Tech Stack:
- Kotlin + Jetpack (CameraX for capture)
- Ultralytics YOLO for Android (PyTorch Mobile / TFLite)
- WorkManager for background processing
- Retrofit for API calls

Scene Upload Payload
````json
{
  "camera_id": "cam_abc123",
  "device_timestamp": 1706745600,
  "objects": [
    {"type": "person", "confidence": 0.82, "bbox": [120, 50, 340, 400]},
    {"type": "cat", "confidence": 0.91, "bbox": [400, 300, 480, 380]}
  ],
  "motion": true,
  "motion_score": 0.65,
  "frame_hash": "sha256:...",
  "has_snapshot": true
}
````

Scene Descriptor Schema
````python
class DetectedObject(BaseModel):
    type: str                    # "person", "cat", "dog", "package", etc.
    confidence: float            # 0.0 - 1.0
    bbox: tuple[int, int, int, int] | None  # [x1, y1, x2, y2]

class SceneDescriptor(BaseModel):
    camera_id: str
    timestamp: datetime
    objects: list[DetectedObject]
    motion: bool
    motion_score: float | None
    snapshot_url: str | None
    enhanced: bool = False      # Was cloud-enhanced
````

Cloud Enhancement (Online Mode)
````python
async def enhance_scene_with_gemini(scene: SceneDescriptor, snapshot_url: str) -> SceneDescriptor:
    """Use Gemini Vision for additional context"""
    prompt = """
    Analyze this home security camera image. Describe:
    1. What objects/people are present
    2. Any notable activity or state
    3. Time of day estimation from lighting

    Respond in JSON: {"description": "...", "additional_objects": [...], "scene_context": "..."}
    """

    response = await gemini.generate_content([prompt, snapshot_image])
    enhanced = scene.model_copy(update={
        "enhanced": True,
        "objects": scene.objects + parse_gemini_objects(response),
    })
    return enhanced
````

Mock Implementation (for backend-first development)
````python
class MockPerceptionAgent:
    def __init__(self):
        self.scenarios = [
            {"objects": [], "motion": False},  # Empty room
            {"objects": [{"type": "cat", "confidence": 0.92}], "motion": True},
            {"objects": [{"type": "person", "confidence": 0.85}], "motion": True},
        ]

    async def get_latest_scene(self, camera_id: str) -> SceneDescriptor:
        scenario = random.choice(self.scenarios)
        return SceneDescriptor(
            camera_id=camera_id,
            timestamp=datetime.now(),
            objects=[DetectedObject(**o) for o in scenario["objects"]],
            motion=scenario["motion"],
        )
````

API Endpoints:
- POST /api/v1/cameras/{id}/scenes - Upload scene descriptor
- POST /api/v1/cameras/{id}/snapshots - Upload image
- GET /api/v1/cameras/{id}/status - Camera heartbeat

---

### Event Agent

The Event Agent monitors perception outputs over time and detects noteworthy events using a rule-based alert system.

Alert Rules Engine
````python
class AlertTrigger(BaseModel):
    type: Literal["motion", "object_detected", "object_absent", "no_motion"]
    object_type: str | None      # For object triggers: "person", "cat", etc.
    confidence_threshold: float = 0.7

class AlertCondition(BaseModel):
    type: Literal["time_range", "user_status", "day_of_week"]
    value: str | dict            # "22:00-06:00" or {"status": "away"}

class AlertRule(BaseModel):
    id: str
    name: str
    enabled: bool = True
    trigger: AlertTrigger
    conditions: list[AlertCondition]
    cooldown_seconds: int = 300  # Prevent alert spam
    severity: Literal["low", "medium", "high"]
````

Default Rules
````python
DEFAULT_RULES = [
    AlertRule(
        id="motion_when_away",
        name="Motion while away",
        trigger=AlertTrigger(type="motion"),
        conditions=[AlertCondition(type="user_status", value={"status": "away"})],
        severity="medium"
    ),
    AlertRule(
        id="person_at_night",
        name="Person detected at night",
        trigger=AlertTrigger(type="object_detected", object_type="person"),
        conditions=[AlertCondition(type="time_range", value="22:00-06:00")],
        severity="high"
    ),
    AlertRule(
        id="package_detected",
        name="Package detected",
        trigger=AlertTrigger(type="object_detected", object_type="package"),
        conditions=[],
        severity="low"
    ),
]
````

Event Processing Flow:
1. Scene received from Perception Agent
2. Evaluate all enabled alert rules against scene
3. Check conditions (time, user status, etc.)
4. Check cooldown (prevent alert spam)
5. If match → Create Event → Send to Gatekeeper

Alert Message Format:
````text
⚠️ Motion detected at 02:14 AM
Objects: person (78%)
Reply VIEW or IGNORE
````

---

### Decision Gatekeeper

The Decision Gatekeeper enforces safety policies and validates all outgoing content before it reaches the user.

Safety Policies
````python
class SafetyPolicy:
    """Enforces ethical boundaries on all outgoing content"""

    BLOCKED_PATTERNS = [
        r"call.*police", r"call.*911", r"emergency services",
        r"looks (sad|angry|scared|anxious|depressed)",
        r"(your|the) (friend|family|wife|husband|child)",  # No identity inference
    ]

    async def validate_response(self, response: str, context: dict) -> ValidationResult:
        # Check for blocked patterns
        # Verify response is descriptive, not prescriptive
        # Ensure no PII leakage
        # Return validated response or redacted version

    async def check_escalation_safety(self, event: Event) -> bool:
        # Never allow automatic escalation to law enforcement
        # Require explicit user consent for high-severity actions
        return False  # Always require user confirmation
````

Escalation Flow:
````text
High-severity event detected
    ↓
Gatekeeper creates confirmation request:
    "⚠️ Person detected at 02:14 AM. Want me to continue monitoring? Reply YES or NO"
    ↓
User confirms YES → Log event, continue monitoring
User confirms NO → Dismiss, add to cooldown
No response in 5 min → Auto-dismiss, log
````

Database Schema
---------------

PostgreSQL is used with UUID primary keys and JSONB for flexible schema evolution.

Users
````sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100),
    status VARCHAR(20) DEFAULT 'home',  -- 'home', 'away', 'dnd'
    timezone VARCHAR(50) DEFAULT 'UTC',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_phone ON users(phone_number);
````

Cameras
````sql
CREATE TABLE cameras (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    device_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(100) DEFAULT 'Home Camera',
    is_active BOOLEAN DEFAULT true,
    last_heartbeat TIMESTAMPTZ,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_cameras_user ON cameras(user_id);
CREATE INDEX idx_cameras_device ON cameras(device_id);
````

Scenes
````sql
CREATE TABLE scenes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    camera_id UUID REFERENCES cameras(id) ON DELETE CASCADE,
    captured_at TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ DEFAULT NOW(),
    objects JSONB NOT NULL DEFAULT '[]',
    motion BOOLEAN DEFAULT false,
    motion_score FLOAT,
    snapshot_url VARCHAR(500),
    enhanced BOOLEAN DEFAULT false,
    enhancement_data JSONB,
    frame_hash VARCHAR(64)
);

CREATE INDEX idx_scenes_camera_time ON scenes(camera_id, captured_at DESC);
CREATE INDEX idx_scenes_motion ON scenes(camera_id, motion) WHERE motion = true;
CREATE INDEX idx_scenes_objects ON scenes USING GIN(objects);
````

Events
````sql
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    camera_id UUID REFERENCES cameras(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    scene_id UUID REFERENCES scenes(id),
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium',
    title VARCHAR(200),
    description TEXT,
    metadata JSONB DEFAULT '{}',
    acknowledged BOOLEAN DEFAULT false,
    acknowledged_at TIMESTAMPTZ,
    response VARCHAR(50),  -- 'viewed', 'ignored', 'escalated'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_events_user_time ON events(user_id, created_at DESC);
CREATE INDEX idx_events_unacknowledged ON events(user_id, acknowledged) WHERE acknowledged = false;
````

Alert Rules
````sql
CREATE TABLE alert_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    camera_id UUID REFERENCES cameras(id),
    name VARCHAR(100) NOT NULL,
    enabled BOOLEAN DEFAULT true,
    trigger_type VARCHAR(50) NOT NULL,
    trigger_config JSONB NOT NULL,
    conditions JSONB DEFAULT '[]',
    severity VARCHAR(20) DEFAULT 'medium',
    cooldown_seconds INT DEFAULT 300,
    last_triggered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alert_rules_user ON alert_rules(user_id, enabled) WHERE enabled = true;
````

Conversations
````sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    last_message_at TIMESTAMPTZ DEFAULT NOW(),
    context JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_conversations_user ON conversations(user_id, is_active) WHERE is_active = true;
````

Messages
````sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    direction VARCHAR(10) NOT NULL,  -- 'inbound', 'outbound'
    content TEXT NOT NULL,
    message_type VARCHAR(20) DEFAULT 'text',
    external_id VARCHAR(100),
    intent VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at DESC);
CREATE INDEX idx_messages_external ON messages(external_id);
````

Audit Log
````sql
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_user_time ON audit_log(user_id, created_at DESC);
````

Environment Configuration
--------------------------

```env
# App
APP_ENV=development
DEBUG=true
SECRET_KEY=your-secret-key-change-in-production

# Transport (mock or whatsapp)
TRANSPORT=mock

# WhatsApp (when TRANSPORT=whatsapp)
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_VERIFY_TOKEN=
WHATSAPP_APP_SECRET=

# Gemini
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-1.5-flash

# Database
DATABASE_URL=postgresql://homey:homey@localhost:5432/homeyai

# Redis (for task queue / caching)
REDIS_URL=redis://localhost:6379

# Media Storage (S3/R2 compatible)
STORAGE_TYPE=local
S3_BUCKET=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
```

Deployment Strategy
--------------------

Development Setup (Docker Compose)
````yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://homey:homey@db:5432/homeyai
      - REDIS_URL=redis://redis:6379
      - TRANSPORT=mock
    depends_on:
      - db
      - redis
    volumes:
      - ./app:/app/app  # Hot reload

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: homey
      POSTGRES_PASSWORD: homey
      POSTGRES_DB: homeyai
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  worker:
    build: .
    command: celery -A app.worker worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://homey:homey@db:5432/homeyai
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
````

Production Deployment Options:

| Option | Pros | Cons | Cost |
|--------|------|------|------|
| **Railway** | Easy deploy, managed Postgres | Limited customization | ~$5-20/mo |
| **Render** | Free tier, auto-deploy | Cold starts on free tier | Free-$25/mo |
| **Cloud Run** | Auto-scale, pay-per-use | Needs Cloud SQL setup | ~$10-50/mo |
| **DigitalOcean App Platform** | Simple, good pricing | Less flexible | ~$12/mo |
| **Self-hosted VPS** | Full control | More ops work | ~$5-10/mo |

Recommended: Railway or Render for MVP

CI/CD Pipeline (GitHub Actions)
````yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Railway
        uses: berviantoleo/railway-deploy@main
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
````

Implementation Checklist
-------------------------

| Phase | Task | Priority |
|-------|------|----------|
| **Setup** | Project scaffold (pyproject.toml, requirements) | P0 |
| **Setup** | Docker Compose (api, postgres, redis) | P0 |
| **Setup** | FastAPI app with health check | P0 |
| **Setup** | Alembic migrations setup | P0 |
| **Database** | Create all SQLAlchemy models | P0 |
| **Database** | Initial migration with all tables | P0 |
| **Agents** | Base agent interface/protocol | P1 |
| **Agents** | Communication Agent (mock transport) | P0 |
| **Agents** | Conversation Agent (Gemini integration) | P0 |
| **Agents** | Mock Perception Agent | P1 |
| **Agents** | Event Agent (rule engine) | P1 |
| **Agents** | Decision Gatekeeper | P2 |
| **API** | Webhook endpoints | P0 |
| **API** | Mock testing endpoints | P0 |
| **API** | Perception upload endpoints | P1 |
| **Tests** | Unit tests for agents | P1 |
| **Tests** | Integration tests | P2 |
| **Deploy** | Dockerfile | P1 |
| **Deploy** | GitHub Actions CI | P2 |

Testing Strategy
----------------

Unit Tests
- pytest for individual agent logic
- Mock all external dependencies (Gemini, WhatsApp, Database)

Integration Tests
- Test agent coordination with mock transport
- Test end-to-end conversation flows

E2E Tests
- Simulate full conversation flows via mock API
- Test real WhatsApp integration (in staging environment)

Load Tests
- Locust for concurrent message handling
- Test database query performance under load

Example Test Scenario
````python
async def test_status_check_flow():
    # 1. Mock perception returns scene with cat
    # 2. Simulate user message: "How are things at home?"
    # 3. Assert response mentions the cat and no unusual activity
    # 4. Assert message logged to DB
````

─────────────────────────────────────────────────────────────────
End of Implementation Plan
─────────────────────────────────────────────────────────────────