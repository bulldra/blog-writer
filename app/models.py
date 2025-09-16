"""データベースモデル定義"""

from datetime import datetime
from typing import TYPE_CHECKING, Generator

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

if TYPE_CHECKING:
    from sqlalchemy.ext.declarative import DeclarativeMeta

    BaseClass = DeclarativeMeta
else:
    BaseClass = object


class Base(DeclarativeBase):
    pass


class EpubHighlight(Base):
    """EPUBハイライトモデル"""

    __tablename__ = "epub_highlights"

    id = Column(Integer, primary_key=True, index=True)
    book_title = Column(String(500), nullable=False, index=True)
    chapter_title = Column(String(500), nullable=False)
    highlighted_text = Column(Text, nullable=False)
    context_before = Column(Text, default="")
    context_after = Column(Text, default="")
    position_start = Column(Integer, nullable=False)
    position_end = Column(Integer, nullable=False)
    selected_for_context = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# データベース設定
engine = create_engine("sqlite:///cache/epub_highlights.db", echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """データベースセッションを取得"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """データベースを初期化"""
    import os

    os.makedirs("cache", exist_ok=True)
    Base.metadata.create_all(bind=engine)
