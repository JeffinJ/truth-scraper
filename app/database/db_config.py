from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "postgresql+asyncpg://neondb_owner:npg_pn6SyDoG7csz@ep-square-bird-a50azatk-pooler.us-east-2.aws.neon.tech/neondb"

engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
    future=True,
    connect_args={"ssl": True}
)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def init_db():
    async with engine.begin() as conn:
        from app.models import truths
        from app.models import scraping_metadata
        # Uncomment this line if you want to drop all tables and recreate them (CAREFUL in production!)
        # await conn.run_sync(Base.metadata.drop_all)
        print(f"Models to create: {Base.metadata.tables.keys()}")
        # Create all tables defined in imported models
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