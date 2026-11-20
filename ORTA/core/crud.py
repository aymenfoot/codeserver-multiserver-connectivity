from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, text

import models, schemas


def get_or_create_source(db: Session, data: schemas.SourceCreate) -> models.Source:
    source = db.query(models.Source).filter(models.Source.source_id == data.source_id).first()
    if source:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(source, field, value)
        db.commit()
        db.refresh(source)
        return source
    source = models.Source(**data.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def get_source(db: Session, source_id: str) -> Optional[models.Source]:
    return db.query(models.Source).filter(models.Source.source_id == source_id).first()


def list_sources(db: Session, skip: int = 0, limit: int = 100) -> List[models.Source]:
    return db.query(models.Source).offset(skip).limit(limit).all()


def create_evidence(db: Session, data: schemas.EvidenceCreate) -> models.Evidence:
    # Idempotent: never duplicate evidence by content_hash within same source_url
    data_dict = data.model_dump()
    if "original_url" in data_dict and data_dict["original_url"] is not None:
        data_dict["original_url"] = str(data_dict["original_url"])
    existing = None
    if data.source_url_id:
        existing = db.query(models.Evidence).filter(
            models.Evidence.source_url_id == data.source_url_id,
            models.Evidence.content_hash == data.content_hash
        ).first()
    if not existing:
        existing = db.query(models.Evidence).filter(
            models.Evidence.content_hash == data.content_hash
        ).first()
    if existing:
        return existing
    evidence = models.Evidence(**data_dict)
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


def get_evidence(db: Session, evidence_id: str) -> Optional[models.Evidence]:
    return db.query(models.Evidence).filter(models.Evidence.evidence_id == evidence_id).first()


def list_evidence(db: Session, skip: int = 0, limit: int = 100) -> List[models.Evidence]:
    return db.query(models.Evidence).offset(skip).limit(limit).all()


def create_entity(db: Session, data: schemas.EntityCreate) -> models.Entity:
    entity = db.query(models.Entity).filter(models.Entity.entity_id == data.entity_id).first()
    if entity:
        return entity
    entity = models.Entity(**data.model_dump())
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


def get_entity(db: Session, entity_id: str) -> Optional[models.Entity]:
    return db.query(models.Entity).filter(models.Entity.entity_id == entity_id).first()


def list_entities(db: Session, skip: int = 0, limit: int = 100) -> List[models.Entity]:
    return db.query(models.Entity).offset(skip).limit(limit).all()


def create_entity_relationship(db: Session, data: schemas.EntityRelationshipCreate) -> models.EntityRelationship:
    rel = models.EntityRelationship(**data.model_dump())
    db.add(rel)
    db.commit()
    db.refresh(rel)
    return rel


def create_claim(db: Session, data: schemas.ClaimCreate) -> models.Claim:
    # Idempotent by claim_id
    claim = db.query(models.Claim).filter(models.Claim.claim_id == data.claim_id).first()
    if claim:
        return claim
    claim = models.Claim(**data.model_dump())
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return claim


def get_claim(db: Session, claim_id: str) -> Optional[models.Claim]:
    return db.query(models.Claim).filter(models.Claim.claim_id == claim_id).first()


def list_claims(db: Session, skip: int = 0, limit: int = 100) -> List[models.Claim]:
    return db.query(models.Claim).offset(skip).limit(limit).all()


def create_investigation(db: Session, data: schemas.InvestigationCreate) -> models.Investigation:
    inv = db.query(models.Investigation).filter(models.Investigation.investigation_id == data.investigation_id).first()
    if inv:
        return inv
    inv = models.Investigation(**data.model_dump())
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


def get_investigation(db: Session, investigation_id: str) -> Optional[models.Investigation]:
    return db.query(models.Investigation).filter(models.Investigation.investigation_id == investigation_id).first()


def list_investigations(db: Session, skip: int = 0, limit: int = 100) -> List[models.Investigation]:
    return db.query(models.Investigation).offset(skip).limit(limit).all()


def add_research_question(db: Session, investigation_id: int, question: str) -> models.ResearchQuestion:
    rq = models.ResearchQuestion(
        investigation_id=investigation_id, question=question)
    db.add(rq)
    db.commit()
    db.refresh(rq)
    return rq


def create_report(db: Session, investigation_id: int, data: schemas.ReportCreate) -> models.Report:
    report = db.query(models.Report).filter(models.Report.report_id == data.report_id).first()
    if report:
        return report
    report = models.Report(**data.model_dump(exclude={"investigation_id"}),
                          investigation_id=investigation_id)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_report(db: Session, report_id: str) -> Optional[models.Report]:
    return db.query(models.Report).filter(models.Report.report_id == report_id).first()


def create_job(db: Session, data: schemas.JobCreate) -> models.Job:
    # Idempotent by job_id
    job = db.query(models.Job).filter(models.Job.job_id == data.job_id).first()
    if job:
        return job
    job = models.Job(**data.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: str) -> Optional[models.Job]:
    return db.query(models.Job).filter(models.Job.job_id == job_id).first()


def list_jobs(db: Session, skip: int = 0, limit: int = 100) -> List[models.Job]:
    return db.query(models.Job).offset(skip).limit(limit).all()


def update_job_status(db: Session, job_id: str, status: str, result: Optional[Dict] = None,
                      error: Optional[str] = None) -> Optional[models.Job]:
    job = get_job(db, job_id)
    if not job:
        return None
    job.status = status
    if result is not None:
        job.result = result
    if error is not None:
        job.error = error
    if status in ("completed", "failed", "dead_letter"):
        from datetime import datetime
        job.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    return job


def increment_retry(db: Session, job_id: str) -> Optional[models.Job]:
    job = get_job(db, job_id)
    if not job:
        return None
    job.retry_count += 1
    if job.retry_count >= job.max_retries:
        job.status = models.Job.dead_letter.property.columns[0].type.python_type  # placeholder
        job.status = "dead_letter"
        job.dead_letter = True
    db.commit()
    db.refresh(job)
    return job
