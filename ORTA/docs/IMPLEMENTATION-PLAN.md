# ORTA Implementation Plan

Phased plan to deliver ORTA. Phases are ordered by dependency. This plan is the single
shared implementation reference; all specialized Agent Manager workstreams map to phases.

## Phase 0 — Foundation (this environment)

- [x] Inspect server (OS, CPU, RAM, disk, Docker, ports, network)
- [x] Record infrastructure constraints (no Docker/root/usns; 6.2 GB disk)
- [x] Create ORTA directory structure at `/home/coder/workspace/ORTA/`
- [x] Upstream research (UPSTREAM-RESEARCH.md)
- [x] Architecture (ARCHITECTURE.md)
- [x] Resource plan (RESOURCE-PLAN.md)
- [x] Implementation plan (this document)

## Phase 1 — ORTA Intelligence Core (native, buildable now)

Owns the intelligence data model and workflows. Buildable without Docker.

- [ ] Python service (FastAPI) with PostgreSQL
- [ ] Schema: evidence, sources, entities, claims, investigations, reports, jobs, provenance
- [ ] Migrations (Alembic)
- [ ] Evidence records: URL, source id, content hash, doc id, timestamps, provenance,
  confidence, relationships
- [ ] Entity profiles, relationships, resolution, duplicate detection, alias mgmt (no
  auto-merge without evidence)
- [ ] Claims: sources, supporting/contradicting evidence, temporal changes, confidence
- [ ] Investigation engine: questions, source discovery, search indexed docs, entities,
  evidence collection, unanswered tracking, findings
- [ ] Reporting: traceable reports (findings, sources, evidence, entities, claims,
  contradictions, confidence, history)
- [ ] API validation, idempotency, transactional integrity
- [ ] Automated tests
- [ ] Docs: INTELLIGENCE-CORE.md

## Phase 2 — ORTA Bridge & pipeline (native, buildable now)

Integration layer between upstream systems and ORTA Core.

- [ ] Job management (create, claim, ack, complete, fail, retry)
- [ ] Normalization, content validation, upload staging
- [ ] Retry + dead-letter handling
- [ ] Reconciliation (restart recovery)
- [ ] Idempotency (content-hash dedupe)
- [ ] Error classification
- [ ] Persistent job state
- [ ] SearXNG HTTP JSON client (when SearXNG available)
- [ ] RAGFlow REST client (auth, upload, parse, index, status) — client code written now,
  live integration when RAGFlow available
- [ ] Core synchronization (evidence, RAGFlow doc IDs, hashes, timestamps)
- [ ] Docs: DATA-PIPELINE.md, INTEGRATION-ARCHITECTURE.md

## Phase 3 — ORTA Unified UI (native, buildable now)

Full frontend operating the platform against real backend APIs.

- [ ] 15 sections: Overview, Source Discovery, Source Registry, Crawling, Search,
  Documents, Knowledge Base, Evidence Explorer, Entities, Claims, Investigations, Reports,
  Processing Jobs, System Health, Configuration
- [ ] Investigation workspace (start, question, progress, sources, evidence, entities,
  claims, contradictions, reports)
- [ ] Evidence exploration (source, document, extraction, claims, entities, provenance,
  status)
- [ ] Operational dashboard (real system data only — no invented statistics)
- [ ] Responsive, consistent visual system
- [ ] Docs: UI-IMPLEMENTATION.md

## Phase 4 — Model infrastructure (buildable now; live verify when models available)

- [ ] Embedding provider abstraction (configurable, local fallback preserved)
- [ ] LLM provider abstraction (content understanding, extraction, classification,
  summarization, planning, analysis, report gen)
- [ ] Reranking (optional, quality-verified before production)
- [ ] Secure credentials (no invented credentials; report unverified functions)
- [ ] Evaluation vs source documents (retrieval relevance, citation correctness,
  extraction accuracy)
- [ ] Docs: MODEL-INFRASTRUCTURE.md, INTELLIGENCE-EVALUATION.md

## Phase 5 — Global discovery & scalability (design now; live when crawler available)

- [ ] Source registry (identity, type, origin, domain, language, category, access,
  crawl policy, reliability, frequency, volume, error history)
- [ ] Discovery categories (websites, search engines, RSS, datasets, open indexes,
  sitemaps, docs, research, forums, company info, APIs, documents, directories)
- [ ] Continuous discovery (scheduled, refresh, incremental, change detection, priority
  queues, dedupe, retry/backoff)
- [ ] Scaling (worker scaling, distributed workloads, prioritization, rate limiting,
  resource-aware concurrency, storage lifecycle, index growth)
- [ ] Compliance: robots.txt, ToS, API limits, rate limits, copyright, privacy, auth
  boundaries
- [ ] Discovery measurement (discovered, new domains, URLs, documents, unique content,
  indexed, failed, throughput, freshness)
- [ ] Docs: GLOBAL-DISCOVERY-STRATEGY.md, SCALABILITY.md

## Phase 6 — Upstream deployment (BLOCKED in this env)

Deploy SearXNG, RAGFlow, CROWler. **Blocked:** Docker unavailable; no root; user
namespaces blocked; RAGFlow is Docker-only; SearXNG official distribution is Docker;
CROWler official repo unresolved.

- Mitigation: write target-state compose files (compose/) and integration clients now;
  execute deployment when Docker/root becomes available.
- Report exact blocker in KNOWN-LIMITATIONS.md; do not pretend resolved.

## Phase 7 — Integration & end-to-end (when upstreams available)

- [ ] CROWler + SearXNG → Bridge → RAGFlow → Core → UI pipeline
- [ ] Real-data integration tests
- [ ] Discovery → collect → normalize → upload → parse → index → sync → entities/claims
  → investigation → report → UI

## Phase 8 — Acceptance, security, backup, observability, delivery

- [ ] Full acceptance suite (infrastructure, health, API, discovery, search, bridge,
  RAGFlow, Core, UI, retry, dead-letter, idempotency, reconciliation, restart recovery,
  dedupe, persistence)
- [ ] Security review (secrets, auth, authz, network, DB, API, deps, container, file
  handling, logging, input validation)
- [ ] Backup + isolated restore test (never overwrite production)
- [ ] Observability (health, queues, errors, storage, alerting)
- [ ] Final e2e scenario
- [ ] Docs: FINAL-DELIVERY-REPORT.md, ACCEPTANCE-REPORT.md, SECURITY-REPORT.md,
  BACKUP-RESTORE-REPORT.md, UPSTREAM-VERSION-MATRIX.md, KNOWN-LIMITATIONS.md

## 9. Agent workstream mapping

| Agent (per mission) | Phases | Status |
|---------------------|--------|--------|
| Architecture & upstream analysis | 0, 1 design | assigned to principal |
| Infrastructure & deployment | 0, 6 | BLOCKED (no Docker/root) |
| CROWler & SearXNG | 5, 6 | CROWler unresolved; SearXNG client in Phase 2 |
| RAGFlow & model integration | 4, 6 | client in Phase 2; model infra Phase 4 |
| ORTA Intelligence Core | 1 | buildable now |
| Integration & data engineering | 2, 7 | buildable now; live when upstreams up |
| Unified UI | 3 | buildable now |
| QA, security, reliability | 8 | acceptance phase |

## 10. Completion statuses (per component, never conflated)

Each final deliverable reports separate statuses: Implemented / Installed / Configured /
Deployed / Operational / Integration tested / Acceptance tested / Production ready.

## 11. Honest constraint note

Full upstream deployment (SearXNG, RAGFlow, CROWler) cannot be completed in this
environment due to the Docker/root/userns blocker. All Core/Bridge/UI/model code and
target-state configs are being built so deployment is immediate once the blocker is
lifted. This is reported as a genuine blocker, not concealed.
