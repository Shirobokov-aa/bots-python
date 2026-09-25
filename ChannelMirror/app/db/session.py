from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(get_settings().database_url, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@event.listens_for(engine.sync_engine, "connect")
def _sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


async def init_db() -> None:
    from app.db import models  # noqa: F401
    from sqlalchemy import text

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Lightweight migrate for existing sqlite DBs
        def _migrate(sync_conn) -> None:
            rows = sync_conn.execute(text("PRAGMA table_info(sources)")).fetchall()
            cols = {r[1] for r in rows}
            if "chat_id" not in cols:
                sync_conn.execute(text("ALTER TABLE sources ADD COLUMN chat_id BIGINT"))

        await conn.run_sync(_migrate)
