"""SQLite-backed history of analyzed repos/zips/files.

One table: analysis_history, keyed by (source_type, identifier).
- source_type="github" -> identifier is the resolved commit SHA
- source_type="zip"    -> identifier is a sha256 of the uploaded zip's bytes
- source_type="file"   -> identifier is a sha256 of the uploaded file's bytes

This is deliberately one small table with SQLAlchemy's create_all, no Alembic —
if the schema grows past this, migrating to Alembic-managed migrations is the
natural next step (see README future-work section).
"""

import datetime
from pathlib import Path

from sqlalchemy import DateTime, String, Text, UniqueConstraint, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import get_settings


class Base(DeclarativeBase):
    pass


class AnalysisHistory(Base):
    __tablename__ = "analysis_history"
    __table_args__ = (UniqueConstraint("source_type", "identifier", name="uq_source_identifier"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source_type: Mapped[str] = mapped_column(String(16))
    identifier: Mapped[str] = mapped_column(String(64), index=True)
    source_label: Mapped[str] = mapped_column(String(500))
    project_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    analyzed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
    review_json: Mapped[str] = mapped_column(Text)


_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_engine():
    global _engine, _session_factory
    if _engine is None:
        settings = get_settings()
        Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
        _engine = create_async_engine(f"sqlite+aiosqlite:///{settings.db_path}")
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


async def init_db() -> None:
    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def get_session() -> AsyncSession:
    _get_engine()
    assert _session_factory is not None
    return _session_factory()


async def find_existing(source_type: str, identifier: str) -> AnalysisHistory | None:
    async with get_session() as session:
        result = await session.execute(
            select(AnalysisHistory).where(
                AnalysisHistory.source_type == source_type,
                AnalysisHistory.identifier == identifier,
            )
        )
        return result.scalar_one_or_none()


async def save_result(
    source_type: str,
    identifier: str,
    source_label: str,
    review_json: str,
    project_id: str | None = None,
) -> AnalysisHistory:
    async with get_session() as session:
        record = AnalysisHistory(
            source_type=source_type,
            identifier=identifier,
            source_label=source_label,
            project_id=project_id,
            review_json=review_json,
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return record


async def list_history(limit: int = 50) -> list[AnalysisHistory]:
    async with get_session() as session:
        result = await session.execute(
            select(AnalysisHistory).order_by(AnalysisHistory.analyzed_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
