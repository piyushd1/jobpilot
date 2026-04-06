"""SQLAlchemy ORM base and session factory."""

from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config.settings import settings

engine = create_async_engine(settings.database_url, echo=settings.is_dev)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all ORM models."""

    pass
