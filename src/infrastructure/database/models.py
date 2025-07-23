from datetime import datetime
from typing import Dict, Any

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .base import Base


class ChatThreadModel(Base):
    __tablename__ = "chat_thread"
    
    thread_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    status = Column(String(50), nullable=False, default="active")
    title = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    metadata_json = Column("metadata", JSONB, nullable=True)
    
    messages = relationship("ChatMessageModel", back_populates="thread", cascade="all, delete-orphan")
    attachments = relationship("ChatAttachmentModel", back_populates="thread", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_chat_thread_user", "user_id"),
    )


class ChatMessageModel(Base):
    __tablename__ = "chat_message"
    
    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("chat_thread.thread_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    type = Column(String(50), nullable=False, default="text")
    metadata_json = Column("metadata", JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    thread = relationship("ChatThreadModel", back_populates="messages")
    attachments = relationship("ChatAttachmentModel", back_populates="message", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_chat_message_thread", "thread_id", "created_at"),
    )


class ChatAttachmentModel(Base):
    __tablename__ = "chat_attachment"
    
    attachment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("chat_message.message_id", ondelete="CASCADE"), nullable=False)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("chat_thread.thread_id", ondelete="CASCADE"), nullable=False)
    url = Column(Text, nullable=False)
    file_type = Column(String(100), nullable=True)
    metadata_json = Column("metadata", JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    message = relationship("ChatMessageModel", back_populates="attachments")
    thread = relationship("ChatThreadModel", back_populates="attachments")
    
    __table_args__ = (
        Index("idx_chat_attachment_thread", "thread_id"),
    )