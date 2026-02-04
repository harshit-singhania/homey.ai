from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Boolean, DateTime, JSON, Integer, Float, ForeignKey, Text, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.services.storage import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    status = Column(String(20), default="home")  # 'home', 'away', 'dnd'
    timezone = Column(String(50), default="UTC")
    settings = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    cameras = relationship("Camera", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="user", cascade="all, delete-orphan")
    alert_rules = relationship("AlertRule", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")


class Camera(Base):
    __tablename__ = "cameras"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(100), default="Home Camera")
    is_active = Column(Boolean, default=True)
    last_heartbeat = Column(DateTime(timezone=True))
    settings = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="cameras")
    scenes = relationship("Scene", back_populates="camera", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="camera", cascade="all, delete-orphan")
    alert_rules = relationship("AlertRule", back_populates="camera", cascade="all, delete-orphan")


class Scene(Base):
    __tablename__ = "scenes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camera_id = Column(UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False, index=True)
    captured_at = Column(DateTime(timezone=True), nullable=False)
    received_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    objects = Column(JSON, default=[])
    motion = Column(Boolean, default=False, index=True)
    motion_score = Column(Float)
    snapshot_url = Column(String(500))
    enhanced = Column(Boolean, default=False)
    enhancement_data = Column(JSON)
    frame_hash = Column(String(64))

    camera = relationship("Camera", back_populates="scenes")
    events = relationship("Event", back_populates="scene", cascade="all, delete-orphan")


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camera_id = Column(UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    scene_id = Column(UUID(as_uuid=True), ForeignKey("scenes.id", ondelete="SET NULL"))
    event_type = Column(String(50), nullable=False)
    severity = Column(String(20), default="medium")  # 'low', 'medium', 'high'
    title = Column(String(200))
    description = Column(Text)
    metadata = Column(JSON, default={})
    acknowledged = Column(Boolean, default=False, index=True)
    acknowledged_at = Column(DateTime(timezone=True))
    response = Column(String(50))  # 'viewed', 'ignored', 'escalated'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    camera = relationship("Camera", back_populates="events")
    user = relationship("User", back_populates="events")
    scene = relationship("Scene", back_populates="events")


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    camera_id = Column(UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="CASCADE"))
    name = Column(String(100), nullable=False)
    enabled = Column(Boolean, default=True, index=True)
    trigger_type = Column(String(50), nullable=False)
    trigger_config = Column(JSON, nullable=False)
    conditions = Column(JSON, default=[])
    severity = Column(String(20), default="medium")
    cooldown_seconds = Column(Integer, default=300)
    last_triggered_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="alert_rules")
    camera = relationship("Camera", back_populates="alert_rules")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_message_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    context = Column(JSON, default={})
    is_active = Column(Boolean, default=True, index=True)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    direction = Column(String(10), nullable=False)  # 'inbound', 'outbound'
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")  # 'text', 'image', 'interactive'
    external_id = Column(String(100), index=True)
    intent = Column(String(50))
    metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(UUID(as_uuid=True))
    details = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")
