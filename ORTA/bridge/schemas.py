from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, HttpUrl, Field


class JobCreate(BaseModel):
    job_id: str
    job_type: str
    payload: Dict[str, Any] = {}
    max_retries: int = Field(default=3, ge=0, le=10)
    correlation_id: Optional[str] = None


class JobUpdate(BaseModel):
    status: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_class: Optional[str] = None


class JobOut(BaseModel):
    id: int
    job_id: str
    job_type: str
    status: str
    payload: Dict[str, Any]
    result: Dict[str, Any]
    error: Optional[str]
    error_class: Optional[str]
    retry_count: int
    max_retries: int
    dead_letter: bool
    correlation_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class NormalizeRequest(BaseModel):
    url: HttpUrl
    source_id: Optional[str] = None


class NormalizeOut(BaseModel):
    canonical_url: str
    content_hash: Optional[str] = None
    is_valid: bool
    validation_notes: Optional[str] = None


class DiscoveryRequest(BaseModel):
    query: Optional[str] = None
    source_type: Optional[str] = "search_engine"
    limit: int = Field(default=10, ge=1, le=100)


class SyncRequest(BaseModel):
    evidence_id: str
    ragflow_document_id: Optional[str] = None
    content_hash: str
    source_url: str


class HealthOut(BaseModel):
    status: str
    service: str
    database: str
    core_reachable: bool
