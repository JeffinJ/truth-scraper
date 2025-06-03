from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core import config
from functools import lru_cache
from app.core.config import settings


print("Database URL:", settings.database_url)

engine = create_async_engine(
    settings.database_url, 
    echo=True,
    future=True,
    connect_args={"ssl": False}
)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def init_db():
    async with engine.begin() as conn:
        from app.models import truths
        print(f"Models to create: {Base.metadata.tables.keys()}")
        await conn.run_sync(Base.metadata.create_all)
    print("Database initialization complete!") 

async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
            
            
DbSession = Annotated[AsyncSession, Depends(get_db)]