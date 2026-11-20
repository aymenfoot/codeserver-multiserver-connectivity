import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Index
from database import Base


class JobStatus(enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    dead_letter = "dead_letter"


class JobErrorClass(enum.Enum):
    transient = "transient"      # network timeout, temporary provider failure
    permanent = "permanent"      # invalid document, auth failure, unsupported type
    policy = "policy"            # robots.txt, rate limit, terms of service


class BridgeJob(Base):
    __tablename__ = "bridge_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True, nullable=False)
    job_type = Column(String, nullable=False, index=True)  # discover, crawl, normalize, validate, upload, parse, index, sync, reconcile
    status = Column(String, default=JobStatus.pending.value, index=True)
    payload = Column(JSON, default=dict)
    result = Column(JSON, default=dict)
    error = Column(Text, nullable=True)
    error_class = Column(String, nullable=True)  # transient/permanent/policy
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    dead_letter = Column(Boolean, default=False, index=True)
    correlation_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (Index("ix_bridge_jobs_status_type", "status", "job_type"),)


class NormalizedContent(Base):
    __tablename__ = "normalized_content"

    id = Column(Integer, primary_key=True, index=True)
    content_hash = Column(String, unique=True, index=True, nullable=False)  # dedupe key
    canonical_url = Column(String, nullable=False, index=True)
    source_url = Column(String, nullable=False)
    title = Column(String, nullable=True)
    content_type = Column(String, nullable=True)
    byte_size = Column(Integer, nullable=True)
    language = Column(String, default="und")
    extracted_text = Column(Text, nullable=True)
    is_valid = Column(Boolean, default=True)
    validation_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
