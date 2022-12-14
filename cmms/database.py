from __future__ import annotations
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from cmms.config import DATABASE_URL_WITH_SCHEMA

logger = logging.getLogger("backend")


log_started = False
if not log_started:
    logging.getLogger("sqlalchemy.engine").info("=" * 80)
    logging.getLogger("sqlalchemy.pool").info("=" * 80)
    logging.getLogger("sqlalchemy.dialects").info("=" * 80)
    logging.getLogger("sqlalchemy.orm").info("=" * 80)
    log_started = True


engine = create_engine(DATABASE_URL_WITH_SCHEMA, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
DeclarativeBase = declarative_base(bind=engine)


class DBContext:
    def __init__(self):
        self.db = SessionLocal()

    def __enter__(self) -> Session:
        return self.db

    def __exit__(self, exc_type, exc_value, traceback):
        self.db.close()


def get_session() -> Session:
    """ Returns the current db connection """
    with DBContext() as session:
        yield session