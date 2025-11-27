"""Initialize database tables"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.db.base import Base
from app.db.models import Document, DocumentChunk
from app.core.config import settings

async def init_db():
    """Create all database tables"""
    engine = create_async_engine(settings.database_url, echo=True)

    async with engine.begin() as conn:
        # Create pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()
    print("Database tables created successfully!")

if __name__ == "__main__":
    from sqlalchemy import text
    asyncio.run(init_db())
