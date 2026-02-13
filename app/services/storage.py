from prisma import Prisma
from app.config import settings

db = Prisma(
    datasource={
        "url": settings.database_url
    }
)

async def get_db():
    if not db.is_connected():
        await db.connect()
    return db
