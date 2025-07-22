import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"Using database URL: {DATABASE_URL}")
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # set to False in production
    future=True,
    pool_pre_ping=True,
)

async_session_factory = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()


async def get_async_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session
