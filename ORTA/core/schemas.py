from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, HttpUrl, Field, validator


class SourceBase(BaseModel):
    source_id: str
    source_type: str = "website"
    domain: Optional[str] = None
    language: str = "und"
    category: Optional[str] = None
    discovery_origin: Optional[str] = None
    access_method: Optional[str] = None
    crawl_policy: Dict[str, Any] = {}
    reliability: float = Field(default=1.0, ge=0.0, le=1.0)
    update_frequency: Optional[str] = None
    is_active: bool = True


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    source_type: Optional[str] = None
    domain: Optional[str] = None
    language: Optional[str] = None
    category: Optional[str] = None
    crawl_policy: Optional[Dict[str, Any]] = None
    reliability: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    is_active: Optional[bool] = None


class SourceOut(SourceBase):
    id: int
    last_successful_access: Optional[datetime] = None
    content_volume: int
    error_history: List[Any] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EvidenceBase(BaseModel):
    evidence_id: str
    original_url: HttpUrl
    content_hash: str
    publication_timestamp: Optional[datetime] = None
    provenance: Dict[str, Any] = {}
    confidence: str = "medium"
    verification_metadata: Dict[str, Any] = {}
    relationships: List[str] = []
    extracted_text: Optional[str] = None


class EvidenceCreate(EvidenceBase):
    source_id: Optional[int] = None
    source_url_id: Optional[int] = None
    document_id: Optional[str] = None


class EvidenceOut(EvidenceBase):
    id: int
    source_id: Optional[int]
    source_url_id: Optional[int]
    document_id: Optional[str]
    collection_timestamp: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EntityBase(BaseModel):
    entity_id: str
    name: str
    entity_type: str
    canonical_name: Optional[str] = None
    identity_confidence: str = "medium"
    alias_management: List[str] = []
    profile: Dict[str, Any] = {}
    duplicate_group_id: Optional[str] = None


class EntityCreate(EntityBase):
    pass


class EntityOut(EntityBase):
    id: int
    resolved_to_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EntityRelationshipBase(BaseModel):
    target_entity_id: int
    relationship_type: str
    confidence: str = "medium"
    evidence_ids: List[int] = []


class EntityRelationshipCreate(EntityRelationshipBase):
    source_entity_id: int


class EntityRelationshipOut(EntityRelationshipBase):
    id: int
    source_entity_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ClaimBase(BaseModel):
    claim_id: str
    statement: str
    statement_type: str = "source_fact"  # source_fact | model_interpretation | inference | hypothesis
    evidence_id: Optional[int] = None
    confidence: str = "medium"
    temporal_valid_from: Optional[datetime] = None
    temporal_valid_to: Optional[datetime] = None


class ClaimCreate(ClaimBase):
    pass


class ClaimOut(ClaimBase):
    id: int
    contradicted_by_claim_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvestigationBase(BaseModel):
    investigation_id: str
    title: str
    research_question: str


class InvestigationCreate(InvestigationBase):
    pass


class InvestigationOut(InvestigationBase):
    id: int
    status: str
    findings: Dict[str, Any]
    unanswered_questions: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResearchQuestionCreate(BaseModel):
    question: str


class ReportBase(BaseModel):
    report_id: str
    title: str
    content: str
    findings: Dict[str, Any] = {}
    sources: List[Any] = []
    evidence_ids: List[str] = []
    entity_ids: List[str] = []
    claim_ids: List[str] = []
    contradictions: List[Any] = []
    confidence_limitations: Optional[str] = None


class ReportCreate(ReportBase):
    pass


class ReportOut(ReportBase):
    id: int
    investigation_id: int
    investigation_history: List[Any]
    created_at: datetime

    class Config:
        from_attributes = True


class JobBase(BaseModel):
    job_id: str
    job_type: str
    payload: Dict[str, Any] = {}
    max_retries: int = 3
    correlation_id: Optional[str] = None


class JobCreate(JobBase):
    pass


class JobOut(JobBase):
    id: int
    status: str
    result: Dict[str, Any]
    error: Optional[str]
    retry_count: int
    dead_letter: bool
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class HealthOut(BaseModel):
    status: str
    service: str
    database: str
