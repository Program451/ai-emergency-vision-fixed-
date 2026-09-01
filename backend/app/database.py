

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # нужно для SQLite + FastAPI (несколько потоков)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db():
    """Создаёт все таблицы, если их ещё нет. Вызывается один раз при старте main.py."""
    from app.models import incident  # noqa: F401 — регистрирует модели в Base.metadata
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency — выдаёт сессию БД и гарантированно закрывает её после запроса."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
