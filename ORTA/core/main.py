import os
import sys
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database, models, schemas, crud

app = FastAPI(title="ORTA Intelligence Core", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/healthz", response_model=schemas.HealthOut)
def healthz(db: Session = Depends(get_db)):
    db_ok = "ok"
    try:
        db.execute(text("SELECT 1")).scalar()
    except Exception:
        db_ok = "unreachable"
    return schemas.HealthOut(status="ok", service="orta-core", database=db_ok)


# ---------- Sources ----------
@app.post("/api/v1/sources", response_model=schemas.SourceOut, status_code=status.HTTP_201_CREATED)
def create_source(payload: schemas.SourceCreate, db: Session = Depends(get_db)):
    return crud.get_or_create_source(db, payload)


@app.get("/api/v1/sources", response_model=List[schemas.SourceOut])
def list_sources(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
                 db: Session = Depends(get_db)):
    return crud.list_sources(db, skip=skip, limit=limit)


@app.get("/api/v1/sources/{source_id}", response_model=schemas.SourceOut)
def get_source(source_id: str, db: Session = Depends(get_db)):
    src = crud.get_source(db, source_id)
    if not src:
        raise HTTPException(status_code=404, detail="source not found")
    return src


@app.patch("/api/v1/sources/{source_id}", response_model=schemas.SourceOut)
def update_source(source_id: str, payload: schemas.SourceUpdate, db: Session = Depends(get_db)):
    src = crud.get_source(db, source_id)
    if not src:
        raise HTTPException(status_code=404, detail="source not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(src, field, value)
    db.commit()
    db.refresh(src)
    return src


# ---------- Evidence ----------
@app.post("/api/v1/evidence", response_model=schemas.EvidenceOut, status_code=status.HTTP_201_CREATED)
def create_evidence(payload: schemas.EvidenceCreate, db: Session = Depends(get_db)):
    return crud.create_evidence(db, payload)


@app.get("/api/v1/evidence", response_model=List[schemas.EvidenceOut])
def list_evidence(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
                  db: Session = Depends(get_db)):
    return crud.list_evidence(db, skip=skip, limit=limit)


@app.get("/api/v1/evidence/{evidence_id}", response_model=schemas.EvidenceOut)
def get_evidence(evidence_id: str, db: Session = Depends(get_db)):
    ev = crud.get_evidence(db, evidence_id)
    if not ev:
        raise HTTPException(status_code=404, detail="evidence not found")
    return ev


@app.get("/api/v1/evidence/{evidence_id}/claims", response_model=List[schemas.ClaimOut])
def evidence_claims(evidence_id: str, db: Session = Depends(get_db)):
    ev = crud.get_evidence(db, evidence_id)
    if not ev:
        raise HTTPException(status_code=404, detail="evidence not found")
    return ev.claims


# ---------- Entities ----------
@app.post("/api/v1/entities", response_model=schemas.EntityOut, status_code=status.HTTP_201_CREATED)
def create_entity(payload: schemas.EntityCreate, db: Session = Depends(get_db)):
    return crud.create_entity(db, payload)


@app.get("/api/v1/entities", response_model=List[schemas.EntityOut])
def list_entities(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
                  db: Session = Depends(get_db)):
    return crud.list_entities(db, skip=skip, limit=limit)


@app.get("/api/v1/entities/{entity_id}", response_model=schemas.EntityOut)
def get_entity(entity_id: str, db: Session = Depends(get_db)):
    ent = crud.get_entity(db, entity_id)
    if not ent:
        raise HTTPException(status_code=404, detail="entity not found")
    return ent


@app.post("/api/v1/entities/{entity_id}/relationships", response_model=schemas.EntityRelationshipOut,
          status_code=status.HTTP_201_CREATED)
def add_relationship(entity_id: str, payload: schemas.EntityRelationshipCreate, db: Session = Depends(get_db)):
    ent = crud.get_entity(db, entity_id)
    if not ent:
        raise HTTPException(status_code=404, detail="entity not found")
    return crud.create_entity_relationship(db, payload)


# ---------- Claims ----------
@app.post("/api/v1/claims", response_model=schemas.ClaimOut, status_code=status.HTTP_201_CREATED)
def create_claim(payload: schemas.ClaimCreate, db: Session = Depends(get_db)):
    return crud.create_claim(db, payload)


@app.get("/api/v1/claims", response_model=List[schemas.ClaimOut])
def list_claims(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
                db: Session = Depends(get_db)):
    return crud.list_claims(db, skip=skip, limit=limit)


@app.get("/api/v1/claims/{claim_id}", response_model=schemas.ClaimOut)
def get_claim(claim_id: str, db: Session = Depends(get_db)):
    cl = crud.get_claim(db, claim_id)
    if not cl:
        raise HTTPException(status_code=404, detail="claim not found")
    return cl


# ---------- Investigations ----------
@app.post("/api/v1/investigations", response_model=schemas.InvestigationOut, status_code=status.HTTP_201_CREATED)
def create_investigation(payload: schemas.InvestigationCreate, db: Session = Depends(get_db)):
    return crud.create_investigation(db, payload)


@app.get("/api/v1/investigations", response_model=List[schemas.InvestigationOut])
def list_investigations(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
                        db: Session = Depends(get_db)):
    return crud.list_investigations(db, skip=skip, limit=limit)


@app.get("/api/v1/investigations/{investigation_id}", response_model=schemas.InvestigationOut)
def get_investigation(investigation_id: str, db: Session = Depends(get_db)):
    inv = crud.get_investigation(db, investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail="investigation not found")
    return inv


@app.post("/api/v1/investigations/{investigation_id}/questions", status_code=status.HTTP_201_CREATED)
def add_question(investigation_id: str, payload: schemas.ResearchQuestionCreate,
                 db: Session = Depends(get_db)):
    inv = crud.get_investigation(db, investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail="investigation not found")
    rq = crud.add_research_question(db, inv.id, payload.question)
    return {"id": rq.id, "question": rq.question, "status": rq.status}


# ---------- Reports ----------
@app.post("/api/v1/reports", response_model=schemas.ReportOut, status_code=status.HTTP_201_CREATED)
def create_report(investigation_id: int, payload: schemas.ReportCreate, db: Session = Depends(get_db)):
    return crud.create_report(db, investigation_id, payload)


@app.get("/api/v1/reports/{report_id}", response_model=schemas.ReportOut)
def get_report(report_id: str, db: Session = Depends(get_db)):
    rep = crud.get_report(db, report_id)
    if not rep:
        raise HTTPException(status_code=404, detail="report not found")
    return rep


# ---------- Jobs ----------
@app.post("/api/v1/jobs", response_model=schemas.JobOut, status_code=status.HTTP_201_CREATED)
def create_job(payload: schemas.JobCreate, db: Session = Depends(get_db)):
    return crud.create_job(db, payload)


@app.get("/api/v1/jobs", response_model=List[schemas.JobOut])
def list_jobs(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
              db: Session = Depends(get_db)):
    return crud.list_jobs(db, skip=skip, limit=limit)


@app.get("/api/v1/jobs/{job_id}", response_model=schemas.JobOut)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = crud.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.patch("/api/v1/jobs/{job_id}/status", response_model=schemas.JobOut)
def update_job_status(job_id: str, status: str = Query(...), result: Optional[str] = None,
                      error: Optional[str] = None, db: Session = Depends(get_db)):
    import json
    result_dict = json.loads(result) if result else None
    job = crud.update_job_status(db, job_id, status, result=result_dict, error=error)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.post("/api/v1/jobs/{job_id}/retry", response_model=schemas.JobOut)
def retry_job(job_id: str, db: Session = Depends(get_db)):
    job = crud.increment_retry(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job
