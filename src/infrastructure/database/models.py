import os
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from .base import Base


def get_json_type():
    """Return JSON type based on database backend."""
    if os.getenv("TESTING", "false").lower() == "true":
        # Use standard JSON for SQLite
        return JSON
    else:
        # Use JSONB for PostgreSQL
        return JSONB


def get_uuid_type():
    """Return UUID type based on database backend."""
    if os.getenv("TESTING", "false").lower() == "true":
        # SQLite doesn't have native UUID, use custom type that converts
        from sqlalchemy import CHAR, TypeDecorator

        class UUIDAsString(TypeDecorator):
            """Store UUID as string in SQLite."""

            impl = CHAR(36)
            cache_ok = True

            def process_bind_param(self, value, dialect):
                if value is not None:
                    # Convert UUID to string for storage
                    return str(value)
                return value

            def process_result_value(self, value, dialect):
                if value is not None:
                    # Convert string back to UUID
                    return uuid.UUID(value)
                return value

        return UUIDAsString()
    else:
        # PostgreSQL has native UUID support
        return UUID(as_uuid=True)


def get_uuid_default():
    """Return UUID default function based on database backend."""
    # Always return UUID object, the TypeDecorator will handle conversion
    return uuid.uuid4


class ChatThreadModel(Base):
    __tablename__ = "chat_thread"

    thread_id = Column(get_uuid_type(), primary_key=True, default=get_uuid_default())
    user_id = Column(get_uuid_type(), nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    status = Column(String(50), nullable=False, default="active")
    title = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    metadata_json = Column("metadata", get_json_type(), nullable=True)

    messages = relationship(
        "ChatMessageModel", back_populates="thread", cascade="all, delete-orphan"
    )
    attachments = relationship(
        "ChatAttachmentModel", back_populates="thread", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_chat_thread_user", "user_id"),)


class ChatMessageModel(Base):
    __tablename__ = "chat_message"

    message_id = Column(get_uuid_type(), primary_key=True, default=get_uuid_default())
    thread_id = Column(
        get_uuid_type(),
        ForeignKey("chat_thread.thread_id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(get_uuid_type(), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    type = Column(String(50), nullable=False, default="text")
    metadata_json = Column("metadata", get_json_type(), nullable=True)
    client_msg_id = Column(String(255), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    thread = relationship("ChatThreadModel", back_populates="messages")
    attachments = relationship(
        "ChatAttachmentModel", back_populates="message", cascade="all, delete-orphan"
    )

    if os.getenv("TESTING", "false").lower() == "true":
        # SQLite doesn't support partial indexes with WHERE clause
        __table_args__ = (Index("idx_chat_message_thread", "thread_id", "created_at"),)
    else:
        # PostgreSQL supports partial unique indexes
        __table_args__ = (
            Index("idx_chat_message_thread", "thread_id", "created_at"),
            Index(
                "idx_chat_message_client_msg_id_unique",
                "client_msg_id",
                unique=True,
                postgresql_where=text("client_msg_id IS NOT NULL"),
            ),
        )


class ChatAttachmentModel(Base):
    __tablename__ = "chat_attachment"

    attachment_id = Column(get_uuid_type(), primary_key=True, default=uuid.uuid4)
    message_id = Column(
        get_uuid_type(),
        ForeignKey("chat_message.message_id", ondelete="CASCADE"),
        nullable=False,
    )
    thread_id = Column(
        get_uuid_type(),
        ForeignKey("chat_thread.thread_id", ondelete="CASCADE"),
        nullable=False,
    )
    url = Column(Text, nullable=False)
    file_type = Column(String(100), nullable=True)
    metadata_json = Column("metadata", get_json_type(), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    message = relationship("ChatMessageModel", back_populates="attachments")
    thread = relationship("ChatThreadModel", back_populates="attachments")

    __table_args__ = (Index("idx_chat_attachment_thread", "thread_id"),)
