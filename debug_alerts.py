import asyncio
import sys
import os
from sqlalchemy import select
from app.models.user import User, AlertRule, Event
from app.services.storage import AsyncSessionLocal

# Add app to path
sys.path.append(os.getcwd())


async def debug_alerts():
    print("Checking Alert Configuration...")
    async with AsyncSessionLocal() as session:
        # 1. Check Users
        stmt = select(User)
        result = await session.execute(stmt)
        users = result.scalars().all()
        print(f"Users found: {len(users)}")
        for u in users:
            print(f" - User: {u.username} (ID: {u.id}, Telegram: {u.telegram_id})")

            # 2. Check Rules for User
            stmt = select(AlertRule).where(AlertRule.user_id == u.id)
            result = await session.execute(stmt)
            rules = result.scalars().all()
            print(f"   Rules: {len(rules)}")
            for r in rules:
                print(
                    f"    - {r.name} (Enabled: {r.enabled}, Last Triggered: {r.last_triggered_at})"
                )

            # 3. Check Recent Events
            stmt = (
                select(Event)
                .where(Event.user_id == u.id)
                .order_by(Event.created_at.desc())
                .limit(5)
            )
            result = await session.execute(stmt)
            events = result.scalars().all()
            print(f"   Recent Events: {len(events)}")
            for e in events:
                print(f"    - {e.title} at {e.created_at}")


if __name__ == "__main__":
    asyncio.run(debug_alerts())
