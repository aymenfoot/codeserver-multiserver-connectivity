import os
import sys
import threading
import time
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database, models, schemas, clients, normalization
from database import engine, SessionLocal, Base

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="ORTA Bridge", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

CORE_URL = os.environ.get("ORTA_CORE_URL", "http://127.0.0.1:8100")
SEARXNG_URL = os.environ.get("ORTA_SEARXNG_URL", "http://127.0.0.1:18080")
RAGFLOW_URL = os.environ.get("ORTA_RAGFLOW_URL", "http://127.0.0.1:80")
RAGFLOW_API_KEY = os.environ.get("ORTA_RAGFLOW_API_KEY", "")
RAGFLOW_DATASET_ID = os.environ.get("ORTA_RAGFLOW_DATASET_ID", "orta-default")

core_client = clients.CoreClient(CORE_URL)
searxng_client = clients.SearXNGClient(SEARXNG_URL)
ragflow_client = clients.RAGFlowClient(RAGFLOW_URL, api_key=RAGFLOW_API_KEY)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- Health ----------
@app.get("/healthz", response_model=schemas.HealthOut)
def healthz(db: Session = Depends(get_db)):
    db_ok = "ok"
    try:
        db.execute(text("SELECT 1")).scalar()
    except Exception:
        db_ok = "unreachable"
    core_reachable = core_client.health()
    return schemas.HealthOut(status="ok", service="orta-bridge", database=db_ok,
                             core_reachable=core_reachable)


# ---------- Jobs ----------
@app.post("/api/v1/jobs", response_model=schemas.JobOut, status_code=status.HTTP_201_CREATED)
def create_job(payload: schemas.JobCreate, db: Session = Depends(get_db)):
    existing = db.execute(text("SELECT 1 FROM bridge_jobs WHERE job_id=:jid"),
                          {"jid": payload.job_id}).fetchone()
    if existing:
        job = db.query(models.BridgeJob).filter(models.BridgeJob.job_id == payload.job_id).first()
        return job
    job = models.BridgeJob(**payload.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    _schedule_job(job.job_id)
    return job


@app.get("/api/v1/jobs", response_model=List[schemas.JobOut])
def list_jobs(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
              db: Session = Depends(get_db)):
    return db.query(models.BridgeJob).offset(skip).limit(limit).all()


@app.get("/api/v1/jobs/{job_id}", response_model=schemas.JobOut)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(models.BridgeJob).filter(models.BridgeJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.patch("/api/v1/jobs/{job_id}", response_model=schemas.JobOut)
def update_job(job_id: str, payload: schemas.JobUpdate, db: Session = Depends(get_db)):
    job = db.query(models.BridgeJob).filter(models.BridgeJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(job, field, value)
    if data.get("status") in ("completed", "failed", "dead_letter"):
        import datetime
        job.completed_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(job)
    return job


@app.post("/api/v1/jobs/{job_id}/retry", response_model=schemas.JobOut)
def retry_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(models.BridgeJob).filter(models.BridgeJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    job.retry_count += 1
    if job.retry_count >= job.max_retries:
        job.status = "dead_letter"
        job.dead_letter = True
    else:
        job.status = "pending"
    db.commit()
    db.refresh(job)
    _schedule_job(job.job_id)
    return job


# ---------- Normalize ----------
@app.post("/api/v1/normalize", response_model=schemas.NormalizeOut)
def normalize(payload: schemas.NormalizeRequest, db: Session = Depends(get_db)):
    canonical = normalization.normalize_url(str(payload.url))
    ch = normalization.content_hash(canonical)
    valid = True
    notes = None
    existing = db.query(models.NormalizedContent).filter(
        models.NormalizedContent.canonical_url == canonical).first()
    if existing:
        return schemas.NormalizeOut(canonical_url=existing.canonical_url,
                                    content_hash=existing.content_hash,
                                    is_valid=existing.is_valid,
                                    validation_notes=existing.validation_notes)
    rec = models.NormalizedContent(canonical_url=canonical, source_url=str(payload.url),
                                   content_hash=ch, is_valid=valid, validation_notes=notes)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return schemas.NormalizeOut(canonical_url=rec.canonical_url, content_hash=rec.content_hash,
                                is_valid=rec.is_valid, validation_notes=rec.validation_notes)


# ---------- Discovery (SearXNG) ----------
@app.post("/api/v1/discover", status_code=status.HTTP_202_ACCEPTED)
def discover(payload: schemas.DiscoveryRequest, db: Session = Depends(get_db)):
    query = payload.query or ""
    job_id = f"discover-{int(time.time()*1000)}"
    job = models.BridgeJob(job_id=job_id, job_type="discover",
                           payload={"query": query, "limit": payload.limit})
    db.add(job)
    db.commit()
    db.refresh(job)
    _schedule_job(job_id)
    return {"job_id": job_id, "status": "pending"}


# ---------- Sync to Core ----------
@app.post("/api/v1/sync", status_code=status.HTTP_202_ACCEPTED)
def sync(payload: schemas.SyncRequest, db: Session = Depends(get_db)):
    job_id = f"sync-{int(time.time()*1000)}"
    job = models.BridgeJob(job_id=job_id, job_type="sync",
                           payload=payload.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    _schedule_job(job_id)
    return {"job_id": job_id, "status": "pending"}


# ---------- Background job worker ----------
_job_thread = None
_thread_lock = threading.Lock()


def _schedule_job(job_id: str):
    global _job_thread
    with _thread_lock:
        if _job_thread is None or not _job_thread.is_alive():
            _job_thread = threading.Thread(target=_worker_loop, daemon=True)
            _job_thread.start()


def _worker_loop():
    while True:
        try:
            _process_pending_once()
        except Exception:
            pass
        time.sleep(2)


# ---------- Integration helpers ----------

def _register_discovered_source(url: str, title: Optional[str] = None,
                                engine: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Register a discovered URL as a Core source (idempotent)."""
    canonical = normalization.normalize_url(url)
    try:
        parsed = __import__("urllib.parse").urlparse(canonical)
        domain = parsed.hostname or ""
    except Exception:
        domain = ""
    payload = {
        "source_id": f"src:{normalization.content_hash(canonical)}",
        "source_type": "website",
        "domain": domain or None,
        "category": None,
        "discovery_origin": "searxng",
        "access_method": "http",
        "crawl_policy": {},
        "reliability": 0.5,
    }
    if title:
        payload["profile_hint"] = title
    if engine:
        payload["discovery_engine"] = engine
    try:
        return core_client.create_source(payload)
    except clients.BridgeError:
        return None


def _poll_ragflow_indexing(dataset_id: str, document_ids: List[str],
                           timeout_s: int = 120) -> Dict[str, Any]:
    """Upload is not indexing. Poll RAGFlow until documents reach a terminal
    ingestion state (COMPLETED or FAILED). Returns per-document status."""
    import time as _time
    deadline = _time.time() + timeout_s
    statuses: Dict[str, str] = {}
    while _time.time() < deadline:
        try:
            tasks = ragflow_client.list_ingestion_tasks(dataset_id)
        except clients.BridgeError:
            tasks = {}
        docs = (tasks or {}).get("docs", []) or (tasks or {}).get("data", []) or []
        all_terminal = True
        for d in docs:
            did = d.get("id") or d.get("document_id")
            run = d.get("run") or d.get("ingestion_status") or d.get("status")
            if did in document_ids:
                statuses[did] = run
                if run not in ("COMPLETED", "FAILED", "CANCEL", "STOPPED"):
                    all_terminal = False
        if all_terminal and statuses:
            return {"terminal": True, "statuses": statuses}
        _time.sleep(3)
    return {"terminal": False, "statuses": statuses}


def _process_pending_once():
    db = SessionLocal()
    try:
        job = db.query(models.BridgeJob).filter(
            models.BridgeJob.status == "pending",
            models.BridgeJob.dead_letter == False,
        ).order_by(models.BridgeJob.created_at.asc()).first()
        if not job:
            return
        job.status = "running"
        db.commit()
        try:
            result = _run_job(job)
            job.status = "completed"
            job.result = result
            job.completed_at = __import__("datetime").datetime.utcnow()
        except clients.BridgeError as exc:
            job.error = str(exc)
            job.error_class = exc.error_class.value
            if exc.retryable and job.retry_count < job.max_retries:
                job.status = "pending"
                job.retry_count += 1
            else:
                job.status = "failed"
                if not exc.retryable:
                    job.dead_letter = True
                job.completed_at = __import__("datetime").datetime.utcnow()
        except Exception as exc:
            job.error = str(exc)
            job.error_class = clients.JobErrorClass.transient.value
            if job.retry_count < job.max_retries:
                job.status = "pending"
                job.retry_count += 1
            else:
                job.status = "failed"
                job.dead_letter = True
                job.completed_at = __import__("datetime").datetime.utcnow()
        db.commit()
    finally:
        db.close()


def _run_job(job: models.BridgeJob) -> Dict[str, Any]:
    jt = job.job_type
    p = job.payload or {}
    if jt == "discover":
        return _run_discover(job)
    if jt == "normalize":
        return _run_normalize(job)
    if jt == "upload":
        return _run_upload(job)
    if jt == "sync":
        return _run_sync(job)
    if jt == "reconcile":
        return _run_reconcile(job)
    raise ValueError(f"unknown job type: {jt}")


def _run_discover(job: models.BridgeJob) -> Dict[str, Any]:
    p = job.payload or {}
    query = p.get("query", "")
    limit = int(p.get("limit", 10))
    results = searxng_client.search(query, limit=limit)
    registered = []
    for item in results:
        url = item.get("url")
        if not url:
            continue
        reg = _register_discovered_source(url, title=item.get("title"), engine=item.get("engine"))
        registered.append({"url": url, "registered": reg is not None})
    return {
        "source": "searxng", "query": query,
        "result_count": len(results), "results": results,
        "sources_registered": registered,
    }


def _run_normalize(job: models.BridgeJob) -> Dict[str, Any]:
    p = job.payload or {}
    url = p.get("url", "")
    canonical = normalization.normalize_url(url)
    return {"url": url, "canonical_url": canonical,
            "content_hash": normalization.content_hash(canonical)}


def _run_upload(job: models.BridgeJob) -> Dict[str, Any]:
    """Upload to RAGFlow and verify parsing/indexing completion before
    reporting success. Upload != indexed."""
    p = job.payload or {}
    file_name = p.get("file_name", "document.bin")
    content = p.get("content", "")
    dataset_id = p.get("dataset_id", RAGFLOW_DATASET_ID)
    content_type = p.get("content_type", "text/plain")

    upload_result = ragflow_client.upload_document(
        dataset_id, file_name, content.encode("utf-8"), content_type)

    # Extract RAGFlow document id from upload response (v1.0.0 data shape).
    doc_id = None
    if isinstance(upload_result, dict):
        data = upload_result.get("data") or upload_result
        if isinstance(data, list):
            data = data[0] if data else {}
        if isinstance(data, dict):
            doc_id = data.get("id") or data.get("document_id")

    indexing = {"uploaded": True, "document_id": doc_id, "indexed": False}
    if doc_id:
        try:
            ragflow_client.start_ingestion(dataset_id, [doc_id])
            poll = _poll_ragflow_indexing(dataset_id, [doc_id])
            indexing["indexed"] = bool(poll.get("terminal"))
            indexing["indexing_statuses"] = poll.get("statuses", {})
        except clients.BridgeError as exc:
            indexing["indexing_error"] = str(exc)
            indexing["indexed"] = False
    return {"dataset_id": dataset_id, "file_name": file_name, **indexing}


def _run_sync(job: models.BridgeJob) -> Dict[str, Any]:
    """Synchronize indexed document into ORTA Core as evidence, preserving
    RAGFlow document id, content hash, source url and provenance."""
    p = job.payload or {}
    evidence = {
        "evidence_id": p.get("evidence_id"),
        "original_url": p.get("source_url"),
        "content_hash": p.get("content_hash"),
        "document_id": p.get("document_id"),   # RAGFlow document id
        "provenance": {
            "tool": "ORTA-Bridge",
            "job_id": job.job_id,
            "ragflow_dataset": p.get("dataset_id", RAGFLOW_DATASET_ID),
        },
        "confidence": p.get("confidence", "medium"),
    }
    core_client.create_evidence(evidence)
    return {"synced": True, "evidence_id": p.get("evidence_id"),
            "document_id": p.get("document_id")}


def _run_reconcile(job: models.BridgeJob) -> Dict[str, Any]:
    # Reclaim unacknowledged/interrupted jobs and mark stale pending jobs for retry
    db = SessionLocal()
    try:
        stale = db.query(models.BridgeJob).filter(
            models.BridgeJob.status == "running",
            models.BridgeJob.dead_letter == False,
        ).all()
        count = 0
        for j in stale:
            j.status = "pending"
            count += 1
        db.commit()
        return {"reconciled": count}
    finally:
        db.close()
