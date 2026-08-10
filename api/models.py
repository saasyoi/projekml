from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Boolean, Text, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship

from api.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(80), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    total_score = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    progress = relationship("QuizProgress", back_populates="user", cascade="all, delete-orphan")
    badges = relationship("Badge", back_populates="user", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")


class QuizProgress(Base):
    __tablename__ = "quiz_progress"
    __table_args__ = (UniqueConstraint("user_id", "topic", "level", name="uq_progress_user_topic_level"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    topic = Column(String(40), nullable=False)
    level = Column(String(20), nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    best_score = Column(Integer, default=0, nullable=False)
    passed = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="progress")


class Badge(Base):
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    earned_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    user = relationship("User", back_populates="badges")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    topic = Column(String(40), nullable=False)
    level = Column(String(20), nullable=False)
    score_percent = Column(Integer, nullable=False)
    passed = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    user = relationship("User", back_populates="quiz_attempts")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(10), nullable=False)  # "user" | "model"
    content = Column(Text, nullable=False)
    has_image = Column(Boolean, default=False, nullable=False)
    status = Column(String(20), nullable=True)  # "danger" | "uncertain" | "no_content" | None
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    user = relationship("User", back_populates="chat_messages")
