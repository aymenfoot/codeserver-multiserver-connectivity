"""ORTA acceptance suite.

Runs against live, already-running services:
  ORTA Core   http://127.0.0.1:8100
  ORTA Bridge http://127.0.0.1:8101
  ORTA UI     http://127.0.0.1:3000 (proxy /api/core/*, /api/bridge/*)

These are real integration tests against deployed services — no mocks.
Upstream (SearXNG / RAGFlow / CROWler) integration is documented in
docs/INTEGRATION-ARCHITECTURE.md and docs/DATA-PIPELINE.md but is not
executable here (no Docker/root — see docs/RESOURCE-PLAN.md §1).
"""

import sys
import time
import requests

CORE = "http://127.0.0.1:8100/api/v1"
BRIDGE = "http://127.0.0.1:8101/api/v1"
UI = "http://127.0.0.1:3000"

PASS = 0
FAIL = 0
RESULTS = []


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        RESULTS.append(f"PASS  {name}")
    else:
        FAIL += 1
        RESULTS.append(f"FAIL  {name} :: {detail}")
    print(("PASS" if cond else "FAIL"), name, detail)


def get(path, base=CORE):
    return requests.get(f"{base}{path}", timeout=10)


def post(path, payload, base=CORE):
    return requests.post(f"{base}{path}", json=payload, timeout=10)


def patch(path, payload, base=CORE):
    return requests.patch(f"{base}{path}", json=payload, timeout=10)


# ---------------------------------------------------------------- infrastructure
def test_infrastructure():
    print("\n== Infrastructure deployment ==")
    r = get("/healthz", base="http://127.0.0.1:8100")
    check("Core service starts", r.status_code == 200, f"HTTP {r.status_code}")
    r = get("/healthz", base="http://127.0.0.1:8101")
    check("Bridge service starts", r.status_code == 200, f"HTTP {r.status_code}")
    r = get("/", base=UI)
    check("UI service starts", r.status_code == 200, f"HTTP {r.status_code}")
    r = get("/api/dashboard", base=UI)
    check("UI dashboard reachable", r.status_code == 200, f"HTTP {r.status_code}")


def test_service_health():
    print("\n== Service health ==")
    r = get("/healthz", base="http://127.0.0.1:8100")
    d = r.json()
    check("Core health ok", d.get("status") == "ok" and d.get("database") == "ok", str(d))
    r = get("/healthz", base="http://127.0.0.1:8101")
    d = r.json()
    check("Bridge health ok", d.get("status") == "ok" and d.get("database") == "ok", str(d))
    check("Bridge sees Core reachable", d.get("core_reachable") is True, str(d))


def test_api_connectivity():
    print("\n== API connectivity ==")
    r = requests.get(f"{UI}/api/core/sources", timeout=10)
    check("UI→Core proxy (sources)", r.status_code == 200, f"HTTP {r.status_code}")
    r = requests.get(f"{UI}/api/bridge/jobs", timeout=10)
    check("UI→Bridge proxy (jobs)", r.status_code == 200, f"HTTP {r.status_code}")


# ---------------------------------------------------------------- CROWler/SearXNG
def test_source_registration():
    print("\n== Source registration ==")
    payload = {"source_id": "acc-src-1", "source_type": "website",
               "domain": "example.org", "category": "news", "reliability": 0.9}
    r = post("/sources", payload)
    check("Create source", r.status_code == 201, f"HTTP {r.status_code} {r.text[:120]}")
    d = r.json()
    check("Source id echoed", d.get("source_id") == "acc-src-1", str(d))
    # Idempotency: re-create same source_id returns existing, no duplicate
    r2 = post("/sources", payload)
    check("Source idempotent (no duplicate)", r2.status_code == 201
          and r2.json().get("id") == d.get("id"), f"HTTP {r2.status_code} ids {d.get('id')} vs {r2.json().get('id')}")
    r = get("/sources/acc-src-1")
    check("Get source by id", r.status_code == 200, f"HTTP {r.status_code}")
    r = get("/sources?limit=10")
    check("List sources", r.status_code == 200 and len(r.json()) >= 1, f"HTTP {r.status_code}")


def test_url_normalization():
    print("\n== URL normalization ==")
    r = post("/normalize", {"url": "https://Example.Org/Page?utm=x&foo=bar"}, base=BRIDGE)
    check("Normalize URL", r.status_code == 200, f"HTTP {r.status_code} {r.text[:120]}")
    d = r.json()
    check("Canonical host lowercased", d.get("canonical_url") == "https://example.org/Page", str(d))
    check("Content hash present", bool(d.get("content_hash")), str(d))


# ---------------------------------------------------------------- Bridge
def test_bridge_job_creation():
    print("\n== Bridge job creation ==")
    payload = {"job_id": "acc-job-1", "job_type": "normalize",
               "payload": {"url": "https://example.org/page"},
               "max_retries": 3}
    r = post("/jobs", payload, base=BRIDGE)
    check("Create bridge job", r.status_code == 201, f"HTTP {r.status_code} {r.text[:120]}")
    jid = r.json().get("job_id")
    check("Job id echoed", jid == "acc-job-1", str(r.json()))
    # Auto-processed to completed (normalize is local)
    for _ in range(20):
        rr = get(f"/jobs/{jid}", base=BRIDGE)
        if rr.status_code == 200 and rr.json().get("status") == "completed":
            break
        time.sleep(0.5)
    rr = get(f"/jobs/{jid}", base=BRIDGE)
    check("Job auto-completed", rr.status_code == 200
          and rr.json().get("status") == "completed", f"status={rr.json().get('status') if rr.status_code==200 else rr.status_code}")
    d = rr.json()
    check("Job has result", bool(d.get("result")), str(d))
    check("Result has canonical_url", "canonical_url" in (d.get("result") or {}), str(d))


def test_file_validation_dead_letter():
    print("\n== Retry / dead-letter handling ==")
    # A discover job calls SearXNG (not deployed) -> transient -> retry -> dead_letter
    payload = {"job_id": "acc-dl-1", "job_type": "discover",
               "payload": {"query": "x", "limit": 5}, "max_retries": 2}
    r = post("/jobs", payload, base=BRIDGE)
    check("Create discover job", r.status_code in (200, 201), f"HTTP {r.status_code}")
    jid = r.json().get("job_id")
    # Wait for retries to exhaust and reach dead_letter/failed
    final = None
    for _ in range(40):
        rr = get(f"/jobs/{jid}", base=BRIDGE)
        if rr.status_code == 200:
            st = rr.json().get("status")
            if st in ("dead_letter", "failed"):
                final = rr.json(); break
        time.sleep(0.5)
    check("Job reaches dead_letter/failed", final is not None
          and final.get("status") in ("dead_letter", "failed"),
          f"status={final.get('status') if final else 'none'} error={final.get('error') if final else ''}")
    check("Error class recorded", bool(final and final.get("error_class")), str(final))
    # Retry a dead-letter job moves it back to pending
    rr = requests.post(f"{BRIDGE}/jobs/{jid}/retry", timeout=10)
    check("Retry dead-letter job", rr.status_code in (200, 201), f"HTTP {rr.status_code}")


# ---------------------------------------------------------------- Core sync
def test_evidence_persistence():
    print("\n== Evidence persistence ==")
    payload = {"evidence_id": "acc-ev-1", "original_url": "https://example.org/a",
               "content_hash": "sha256acc1", "source_id": 1,
               "confidence": "high",
               "provenance": {"tool": "acceptance-test", "job": "acc-job-1"}}
    r = post("/evidence", payload)
    check("Create evidence", r.status_code == 201, f"HTTP {r.status_code} {r.text[:120]}")
    d = r.json()
    check("Evidence id echoed", d.get("evidence_id") == "acc-ev-1", str(d))
    check("Content hash stored", d.get("content_hash") == "sha256acc1", str(d))
    check("Provenance stored", d.get("provenance", {}).get("tool") == "acceptance-test", str(d))
    # Dedupe: re-create same content_hash returns existing
    r2 = post("/evidence", payload)
    check("Evidence idempotent (no dup)", r2.status_code == 201
          and r2.json().get("id") == d.get("id"), f"HTTP {r2.status_code}")
    r = get(f"/evidence/{d.get('evidence_id')}")
    check("Get evidence by id", r.status_code == 200, f"HTTP {r.status_code}")
    r = get("/evidence?limit=10")
    check("List evidence", r.status_code == 200 and len(r.json()) >= 1, f"HTTP {r.status_code}")


def test_entity_extraction_resolution():
    print("\n== Entity extraction & resolution ==")
    payload = {"entity_id": "acc-ent-1", "name": "Acme Corp",
               "entity_type": "organization", "identity_confidence": "high",
               "alias_management": ["Acme", "ACME"], "duplicate_group_id": None}
    r = post("/entities", payload)
    check("Create entity", r.status_code == 201, f"HTTP {r.status_code} {r.text[:120]}")
    d = r.json()
    check("Entity id echoed", d.get("entity_id") == "acc-ent-1", str(d))
    # Idempotent
    r2 = post("/entities", payload)
    check("Entity idempotent", r2.status_code == 201
          and r2.json().get("id") == d.get("id"), f"HTTP {r2.status_code}")
    r = get("/entities?limit=10")
    check("List entities", r.status_code == 200 and len(r.json()) >= 1, f"HTTP {r.status_code}")


def test_claim_creation():
    print("\n== Claim creation ==")
    payload = {"claim_id": "acc-cl-1", "statement": "Acme launched in 2024",
               "statement_type": "source_fact", "evidence_id": 1, "confidence": "high"}
    r = post("/claims", payload)
    check("Create claim", r.status_code == 201, f"HTTP {r.status_code} {r.text[:120]}")
    d = r.json()
    check("Claim id echoed", d.get("claim_id") == "acc-cl-1", str(d))
    check("Statement type source_fact", d.get("statement_type") == "source_fact", str(d))
    r = get("/claims?limit=10")
    check("List claims", r.status_code == 200 and len(r.json()) >= 1, f"HTTP {r.status_code}")


# ---------------------------------------------------------------- Investigation
def test_investigation_workflow():
    print("\n== Investigation workflow ==")
    payload = {"investigation_id": "acc-inv-1", "title": "Acceptance Inquiry",
               "research_question": "What did Acme do?"}
    r = post("/investigations", payload)
    check("Create investigation", r.status_code == 201, f"HTTP {r.status_code} {r.text[:120]}")
    d = r.json()
    check("Investigation id echoed", d.get("investigation_id") == "acc-inv-1", str(d))
    inv_stable_id = d.get("investigation_id")
    # Add research question (path uses stable investigation_id)
    r = requests.post(f"{CORE}/investigations/{inv_stable_id}/questions",
                      json={"question": "When did it launch?"}, timeout=10)
    check("Add research question", r.status_code in (200, 201), f"HTTP {r.status_code} {r.text[:120]}")
    r = get(f"/investigations/{d.get('investigation_id')}")
    check("Get investigation", r.status_code == 200, f"HTTP {r.status_code}")
    r = get("/investigations?limit=10")
    check("List investigations", r.status_code == 200 and len(r.json()) >= 1, f"HTTP {r.status_code}")


def test_report_generation():
    print("\n== Report generation ==")
    payload = {"report_id": "acc-rep-1", "title": "Acceptance Report",
               "content": "Traceable findings from evidence ev-1.",
               "findings": {"summary": "ok"}, "evidence_ids": ["acc-ev-1"],
               "entity_ids": ["acc-ent-1"], "claim_ids": ["acc-cl-1"],
               "contradictions": [], "confidence_limitations": "single source"}
    # Need investigation_id; use the investigation created above (id 1)
    r = requests.post(f"{CORE}/reports?investigation_id=1", json=payload, timeout=10)
    check("Create report", r.status_code == 201, f"HTTP {r.status_code} {r.text[:120]}")
    d = r.json()
    check("Report id echoed", d.get("report_id") == "acc-rep-1", str(d))
    check("Report cites evidence", "acc-ev-1" in (d.get("evidence_ids") or []), str(d))
    r = get(f"/reports/{d.get('report_id')}")
    check("Get report by id", r.status_code == 200, f"HTTP {r.status_code}")


# ---------------------------------------------------------------- UI workflows
def test_ui_workflows():
    print("\n== UI workflows ==")
    r = get("/", base=UI)
    check("UI index loads", r.status_code == 200 and b"ORTA" in r.content, f"HTTP {r.status_code}")
    # Dashboard aggregates real counts
    r = get("/api/dashboard", base=UI)
    d = r.json()
    check("Dashboard counts real", isinstance(d.get("counts"), dict)
          and d["counts"].get("sources", 0) >= 1, str(d.get("counts")))
    check("Dashboard services present", "core" in d.get("services", {})
          and "bridge" in d.get("services", {}), str(d.get("services")))


# ---------------------------------------------------------------- storage persistence
def test_storage_persistence():
    print("\n== Storage persistence ==")
    import os
    db = "/home/coder/workspace/ORTA/storage/orta.db"
    check("Core DB file exists", os.path.exists(db) and os.path.getsize(db) > 0, db)
    r = get("/sources?limit=1")
    check("Sources persist across requests", r.status_code == 200, f"HTTP {r.status_code}")


def main():
    test_infrastructure()
    test_service_health()
    test_api_connectivity()
    test_source_registration()
    test_url_normalization()
    test_bridge_job_creation()
    test_file_validation_dead_letter()
    test_evidence_persistence()
    test_entity_extraction_resolution()
    test_claim_creation()
    test_investigation_workflow()
    test_report_generation()
    test_ui_workflows()
    test_storage_persistence()
    print("\n" + "=" * 60)
    print(f"RESULTS: {PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    for line in RESULTS:
        if line.startswith("FAIL"):
            print(line)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
