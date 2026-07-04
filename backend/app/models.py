from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from .database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    api_key = Column(String, unique=True, nullable=False)
    tier = Column(String, default="free")  # free, pro, team
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class LolbinEntry(Base):
    __tablename__ = "lolbin_entries"

    id = Column(String, primary_key=True)  # slug, e.g. "certutil"
    name = Column(String, nullable=False)
    os = Column(String, nullable=False)  # windows / linux / macos
    category = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    example_command = Column(Text, nullable=False)
    alt_commands = Column(JSON, default=list)
    detection_notes = Column(Text, nullable=True)
    references = Column(JSON, default=list)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                         onupdate=lambda: datetime.now(timezone.utc))


class CustomEntry(Base):
    """Org-private entries — Pro/Team tier feature."""
    __tablename__ = "custom_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    name = Column(String, nullable=False)
    os = Column(String, nullable=False)
    category = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    example_command = Column(Text, nullable=False)
    detection_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
