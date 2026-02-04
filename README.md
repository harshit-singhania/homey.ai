# Homey.ai

A Telegram-first conversational surveillance system that turns a smartphone camera into an intelligent safety monitor. Users interact entirely through natural language via Telegram. The system detects activity, summarizes scene state, and responds to user queries.

## Overview

Homey.ai is built with agentic components that perform distinct roles:

1. **Perception Agent** – Visual scene understanding on device
2. **Communication Agent** – Telegram message handling
3. **Conversation Agent** – Natural language interpretation & response
4. **Event Agent** – Incident detection & alert generation
5. **Decision Gatekeeper** – Safety checks & human-in-loop escalation

For detailed agent specifications, see [AGENTS.md](./AGENTS.md).

## Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Backend | Python 3.11+ / FastAPI | Async support, type hints, rapid development |
| LLM | Google Gemini | Strong multimodal capabilities, cost-effective |
| Database | PostgreSQL | Relational reliability, JSON support, time-series queries |
| Cache/Queue | Redis | Task queue, caching, pub/sub for real-time |
| Perception | Hybrid: Android (YOLO) + Cloud (Gemini Vision) | Offline capability + enhanced reasoning |
| Messaging | Telegram Bot API (python-telegram-bot) | Production bot framework, webhook & polling support |
| ORM | SQLAlchemy | Mature Python ORM with async support |
| Migrations | Alembic | Database version control |
| Deployment | Docker + Railway/Render | Containerized, managed services |

## Project Structure

```
homeyai/
├── app/
│   ├── main.py                    # FastAPI entry point
│   ├── config.py                  # Settings, environment variables
│   ├── agents/
│   │   ├── base.py                # Base agent interface
│   │   ├── communication.py       # Telegram message handling
│   │   ├── conversation.py        # LLM intent & response
│   │   ├── perception.py          # Scene descriptor interface
│   │   ├── event.py               # Alert detection logic
│   │   └── gatekeeper.py          # Safety validation
│   ├── models/
│   │   ├── scene.py               # Scene, Object, Motion schemas
│   │   ├── event.py               # Alert, EventType schemas
│   │   ├── user.py                # User, Conversation state
│   │   └── message.py             # Telegram message models
│   ├── services/
│   │   ├── telegram.py            # Telegram Bot API client
│   │   ├── gemini.py              # Gemini LLM integration
│   │   └── storage.py             # PostgreSQL operations
│   ├── api/
│   │   ├── webhooks.py            # Telegram webhook endpoints
│   │   ├── perception.py          # Phone → Server scene upload
│   │   ├── mock.py                # Mock testing interface
│   │   └── health.py              # Health checks
│   └── utils/
│       └── safety.py              # Safety policy enforcement
├── tests/
├── alembic/                       # Database migrations
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── AGENTS.md                      # Agent specifications
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Google Gemini API Key

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd homeyai
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

3. **Configure environment variables**
   ```bash
   # Edit .env file
   TRANSPORT=telegram
   TELEGRAM_BOT_TOKEN=your-bot-token-here
   GEMINI_API_KEY=your-gemini-api-key
   ```

4. **Start services**
   ```bash
   docker-compose up -d
   ```

5. **Run database migrations**
   ```bash
   docker-compose exec api alembic upgrade head
   ```

6. **Test the bot**
   - Send a message to your Telegram bot
   - Check logs: `docker-compose logs -f api`

## Development

### Local Development Setup

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start database**
   ```bash
   docker-compose up db redis -d
   ```

4. **Run migrations**
   ```bash
   alembic upgrade head
   ```

5. **Start development server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Testing with Mock Transport

For local development without Telegram:

```bash
# Set transport to mock
TRANSPORT=mock

# Start server
uvicorn app.main:app --reload

# Send mock message
curl -X POST http://localhost:8000/api/v1/mock/send \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_id": 123456789,
    "username": "testuser",
    "content": "How are things at home?"
  }'

# View responses
curl http://localhost:8000/api/v1/mock/messages
```

### Running Tests

```bash
pytest
pytest --cov=app tests/
pytest -v tests/unit/
```

## Database Migrations

### Create a new migration

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations

```bash
alembic upgrade head
```

### Rollback migration

```bash
alembic downgrade -1
```

## Telegram Bot Setup

### Create Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot`
3. Follow prompts to create bot
4. Copy the bot token

### Set Webhook (Production)

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-domain.com/webhooks/telegram",
    "secret_token": "your-webhook-secret"
  }'
```

### Use Long Polling (Development)

For local development, you can use long polling instead of webhooks. The telegram transport will automatically handle this.

## API Endpoints

### Health Checks
- `GET /health/` - Basic health check
- `GET /health/db` - Database health
- `GET /health/redis` - Redis health

### Telegram Webhooks
- `POST /webhooks/telegram` - Telegram webhook receiver

### Camera Endpoints (TODO)
- `POST /api/v1/cameras/{id}/scenes` - Upload scene descriptor
- `POST /api/v1/cameras/{id}/snapshots` - Upload snapshot image
- `GET /api/v1/cameras/{id}/status` - Camera heartbeat

### Mock Interface (Development)
- `POST /api/v1/mock/send` - Send mock message
- `GET /api/v1/mock/messages` - View sent messages
- `DELETE /api/v1/mock/messages` - Clear message queue

## Architecture

### Message Flow

```
User (Telegram) ──> Communication Agent
                     │
                     ▼
           Conversation Agent ──> Perception Agent
                     │               │
                     ▼               ▼
                 Decision Gatekeeper ◀─ Event Agent
                     │
                     ▼
            Communication Agent ──> User
```

### Agent Responsibilities

**Communication Agent**
- Parse Telegram Update objects
- Handle text, photo, callback queries, locations
- Send messages with inline keyboards
- Manage rate limiting

**Conversation Agent**
- Classify user intent (status check, object query, snapshot request, etc.)
- Generate responses using Gemini LLM
- Maintain conversation context
- Follow safety boundaries

**Perception Agent**
- Interface for scene descriptors from Android app
- Mock implementation for testing
- Cloud enhancement via Gemini Vision (planned)

**Event Agent**
- Rule-based alert detection
- Monitor scene changes over time
- Apply cooldown to prevent spam
- Trigger notifications

**Decision Gatekeeper**
- Validate all outgoing messages
- Enforce safety policies (no facial recognition, no emotional inference)
- Require human confirmation for escalations

## Safety & Ethics

Homey.ai follows strict ethical guidelines:

| Restriction | Reason |
|------------|--------|
| No facial recognition | Privacy, legal risks |
| No emotional inference | Safety, liability |
| No autonomous enforcement | Prevent misuse |
| No public space monitoring | Consent required |

All agents enforce these boundaries.

## Deployment

### Railway

1. Create new project on Railway
2. Add PostgreSQL and Redis services
3. Connect GitHub repository
4. Set environment variables
5. Deploy

### Render

1. Create new Web Service
2. Connect GitHub repository
3. Add PostgreSQL and Redis add-ons
4. Set environment variables
5. Deploy

### Manual (VPS)

```bash
# Build and run with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

[Add your license here]

## Support

For issues and questions:
- Open an issue on GitHub
- Check [AGENTS.md](./AGENTS.md) for detailed specifications
- Review the [Implementation Plan](./CLAUDE.md#implementation-plan)
