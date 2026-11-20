import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Boolean,
    Float, JSON, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database import Base


class EvidenceConfidence(enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    verified = "verified"


class SourceType(enum.Enum):
    website = "website"
    search_engine = "search_engine"
    rss = "rss"
    sitemap = "sitemap"
    commoncrawl = "commoncrawl"
    public_dataset = "public_dataset"
    open_index = "open_index"
    documentation = "documentation"
    research_publication = "research_publication"
    forum = "forum"
    company_info = "company_info"
    public_api = "public_api"
    document = "document"
    directory = "directory"
    other = "other"


class JobStatus(enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    dead_letter = "dead_letter"


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String, unique=True, index=True, nullable=False)  # stable source identifier
    source_type = Column(String, nullable=False, default=SourceType.website.value)
    domain = Column(String, index=True)
    language = Column(String, default="und")
    category = Column(String, index=True)
    discovery_origin = Column(String)  # how this source was discovered
    access_method = Column(String)  # http, rss, api, etc.
    crawl_policy = Column(JSON)  # rate limit, robots respect, depth, etc.
    last_successful_access = Column(DateTime, nullable=True)
    reliability = Column(Float, default=1.0)  # 0..1
    update_frequency = Column(String, nullable=True)  # e.g. "daily"
    content_volume = Column(Integer, default=0)  # number of documents/urls
    error_history = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    urls = relationship("SourceURL", back_populates="source", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="source", cascade="all, delete-orphan")


class SourceURL(Base):
    __tablename__ = "source_urls"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    url = Column(String, nullable=False)
    normalized_url = Column(String, nullable=False, index=True)
    content_hash = Column(String, index=True)  # sha256 of fetched content
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, nullable=True)
    status = Column(String, default="discovered")  # discovered, fetched, failed

    source = relationship("Source", back_populates="urls")
    evidence = relationship("Evidence", back_populates="source_url", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("source_id", "normalized_url", name="uq_source_normalized_url"),)


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(String, unique=True, index=True, nullable=False)  # stable evidence identifier
    source_url_id = Column(Integer, ForeignKey("source_urls.id", ondelete="SET NULL"), nullable=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="SET NULL"), nullable=True)
    document_id = Column(String, nullable=True, index=True)  # RAGFlow document id if indexed
    original_url = Column(String, nullable=False)
    content_hash = Column(String, nullable=False, index=True)  # sha256
    collection_timestamp = Column(DateTime, default=datetime.utcnow)
    publication_timestamp = Column(DateTime, nullable=True)
    provenance = Column(JSON, default=dict)  # who/what collected it, method, tool
    confidence = Column(String, default=EvidenceConfidence.medium.value)
    verification_metadata = Column(JSON, default=dict)
    relationships = Column(JSON, default=list)  # related evidence ids
    raw_content = Column(Text, nullable=True)
    extracted_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    source_url = relationship("SourceURL", back_populates="evidence")
    source = relationship("Source", back_populates="evidence")
    claims = relationship("Claim", back_populates="evidence", cascade="all, delete-orphan")
    entities = relationship("EntityMention", back_populates="evidence", cascade="all, delete-orphan")


class Entity(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(String, unique=True, index=True, nullable=False)  # stable entity identifier
    name = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=False, index=True)  # person, organization, location, etc.
    canonical_name = Column(String, nullable=True)  # after resolution
    resolved_to_id = Column(Integer, ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)  # canonical cluster
    identity_confidence = Column(String, default="medium")  # low/medium/high
    alias_management = Column(JSON, default=list)  # known aliases
    historical_changes = Column(JSON, default=list)
    profile = Column(JSON, default=dict)
    duplicate_group_id = Column(String, nullable=True, index=True)  # potential duplicate cluster
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    mentions = relationship("EntityMention", back_populates="entity", cascade="all, delete-orphan")
    relationships = relationship(
        "EntityRelationship", foreign_keys="EntityRelationship.source_entity_id",
        back_populates="source_entity", cascade="all, delete-orphan")
    reverse_relationships = relationship(
        "EntityRelationship", foreign_keys="EntityRelationship.target_entity_id",
        back_populates="target_entity")


class EntityMention(Base):
    __tablename__ = "entity_mentions"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id", ondelete="CASCADE"), nullable=False)
    entity_id = Column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    mention_text = Column(String, nullable=False)
    start_offset = Column(Integer, nullable=True)
    end_offset = Column(Integer, nullable=True)
    confidence = Column(String, default="medium")
    created_at = Column(DateTime, default=datetime.utcnow)

    evidence = relationship("Evidence", back_populates="entities")
    entity = relationship("Entity", back_populates="mentions")


class EntityRelationship(Base):
    __tablename__ = "entity_relationships"

    id = Column(Integer, primary_key=True, index=True)
    source_entity_id = Column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    target_entity_id = Column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    relationship_type = Column(String, nullable=False)  # works_for, located_in, etc.
    confidence = Column(String, default="medium")
    evidence_ids = Column(JSON, default=list)  # supporting evidence ids
    created_at = Column(DateTime, default=datetime.utcnow)

    source_entity = relationship("Entity", foreign_keys=[source_entity_id], back_populates="relationships")
    target_entity = relationship("Entity", foreign_keys=[target_entity_id], back_populates="reverse_relationships")


class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(String, unique=True, index=True, nullable=False)  # stable claim identifier
    statement = Column(Text, nullable=False)
    statement_type = Column(String, nullable=False)  # source_fact, model_interpretation, inference, hypothesis
    evidence_id = Column(Integer, ForeignKey("evidence.id", ondelete="SET NULL"), nullable=True)
    confidence = Column(String, default="medium")
    temporal_valid_from = Column(DateTime, nullable=True)
    temporal_valid_to = Column(DateTime, nullable=True)
    contradicted_by_claim_id = Column(Integer, ForeignKey("claims.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    evidence = relationship("Evidence", back_populates="claims")
    contradiction = relationship("Claim", remote_side=[id])


class Investigation(Base):
    __tablename__ = "investigations"

    id = Column(Integer, primary_key=True, index=True)
    investigation_id = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    research_question = Column(Text, nullable=False)
    status = Column(String, default="active")  # active, paused, completed, archived
    findings = Column(JSON, default=dict)
    unanswered_questions = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    research_questions = relationship("ResearchQuestion", back_populates="investigation", cascade="all, delete-orphan")
    sources = relationship("InvestigationSource", back_populates="investigation", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="investigation", cascade="all, delete-orphan")


class ResearchQuestion(Base):
    __tablename__ = "research_questions"

    id = Column(Integer, primary_key=True, index=True)
    investigation_id = Column(Integer, ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False)
    question = Column(Text, nullable=False)
    status = Column(String, default="open")  # open, answered, unanswered
    answer = Column(Text, nullable=True)
    confidence = Column(String, default="medium")
    created_at = Column(DateTime, default=datetime.utcnow)

    investigation = relationship("Investigation", back_populates="research_questions")


class InvestigationSource(Base):
    __tablename__ = "investigation_sources"

    id = Column(Integer, primary_key=True, index=True)
    investigation_id = Column(Integer, ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False)
    evidence_id = Column(Integer, ForeignKey("evidence.id", ondelete="CASCADE"), nullable=False)
    relevance = Column(String, default="medium")
    created_at = Column(DateTime, default=datetime.utcnow)

    investigation = relationship("Investigation", back_populates="sources")
    evidence = relationship("Evidence")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String, unique=True, index=True, nullable=False)
    investigation_id = Column(Integer, ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)  # traceable report content
    findings = Column(JSON, default=dict)
    sources = Column(JSON, default=list)
    evidence_ids = Column(JSON, default=list)
    entity_ids = Column(JSON, default=list)
    claim_ids = Column(JSON, default=list)
    contradictions = Column(JSON, default=list)
    confidence_limitations = Column(Text, nullable=True)
    investigation_history = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    investigation = relationship("Investigation", back_populates="reports")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True, nullable=False)
    job_type = Column(String, nullable=False)  # crawl, normalize, upload, parse, index, sync, reconcile
    status = Column(String, default=JobStatus.pending.value)
    payload = Column(JSON, default=dict)
    result = Column(JSON, default=dict)
    error = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    dead_letter = Column(Boolean, default=False)
    correlation_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (Index("ix_jobs_status_type", "status", "job_type"),)


Index("ix_claims_statement_type", Claim.statement_type)
