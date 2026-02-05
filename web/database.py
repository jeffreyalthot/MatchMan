from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker


BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = f"sqlite:///{BASE_DIR / 'matchman.db'}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    username: Mapped[str] = mapped_column(String(64), nullable=False)


class MaleProfileModel(Base):
    __tablename__ = "male_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    city: Mapped[str] = mapped_column(String(64), nullable=False)
    region: Mapped[str] = mapped_column(String(64), nullable=False)
    bio: Mapped[str] = mapped_column(Text, nullable=False)
    tastes: Mapped[str] = mapped_column(String(255), nullable=False)


class MatchModel(Base):
    __tablename__ = "matches"
    __table_args__ = (UniqueConstraint("woman_id", "man_id", name="uq_woman_man_match"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    woman_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    man_id: Mapped[int] = mapped_column(ForeignKey("male_profiles.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    conversation: Mapped["ConversationModel"] = relationship(back_populates="match", uselist=False)


class ConversationModel(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), unique=True, nullable=False)
    woman_name: Mapped[str] = mapped_column(String(64), nullable=False)
    man_name: Mapped[str] = mapped_column(String(64), nullable=False)

    match: Mapped[MatchModel] = relationship(back_populates="conversation")
    messages: Mapped[list["MessageModel"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")


class MessageModel(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    conversation: Mapped[ConversationModel] = relationship(back_populates="messages")


def init_database() -> None:
    Base.metadata.create_all(bind=engine)
