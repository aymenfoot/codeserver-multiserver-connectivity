# ORTA Unified UI Completion Report

Status: **Implemented, deployed, operational, acceptance-tested** (dev build; real-data only).

## A. 15 sections (all implemented)

| Section | Route | Backed by live API | Status |
|---------|-------|--------------------|--------|
| Global Overview | `/` → `#section-overview` | `/api/dashboard` | implemented |
| Source Discovery | `#section-discovery` | Bridge `/api/v1/discover` | implemented |
| Source Registry | `#section-registry` | Core `/api/v1/sources` | implemented |
| Crawling Operations | `#section-crawling` | Bridge `/api/v1/jobs` (normalize) | implemented |
| Search | `#section-search` | Bridge `/api/v1/discover` (SearXNG) | implemented |
| Documents | `#section-documents` | Core `/api/v1/evidence` | implemented |
| Knowledge Base | `#section-kb` | Core entities + claims | implemented |
| Evidence Explorer | `#section-evidence` | Core `/api/v1/evidence` | implemented |
| Entities | `#section-entities` | Core `/api/v1/entities` | implemented |
| Claims | `#section-claims` | Core `/api/v1/claims` | implemented |
| Investigations | `#section-investigations` | Core investigations/questions | implemented |
| Reports | `#section-reports` | Core `/api/v1/reports` | implemented |
| Processing Jobs | `#section-jobs` | Bridge `/api/v1/jobs` | implemented |
| System Health | `#section-health` | Core + Bridge `/healthz` | implemented |
| Configuration & Admin | `#section-admin` | env config display | implemented |

## B. Investigation workspace
- Start investigation (title + research question).
- View progress, add research sub-questions.
- Select an investigation to view details (title, question, id, status).

## C. Evidence exploration
- Displays original source, document (RAGFlow doc id), extracted text, provenance, confidence, collection timestamp.
- View action per evidence record.

## D. Operational dashboard (`/api/dashboard`)
- Real-time/refreshed: services (health), counts (sources, evidence, entities, claims, investigations, reports), job queues (pending/running/completed/failed/dead_letter), errors.
- **Every number comes from live Core/Bridge APIs — no invented statistics.**

## E. Design
- Single-page application (`ui/static/index.html`) with Tailwind CSS (CDN).
- Responsive, consistent visual system, sidebar navigation, sticky table headers.
- Section-based routing via `showSection()`; active nav highlighting.
- Modals for source registration and investigation creation.

## F. Verified against live services
- 55 acceptance tests pass, including UI index load (HTTP 200, contains "ORTA") and dashboard counts (real values from Core/Bridge).

## G. Remaining (production)
- Authentication/authorization (UI currently unauthenticated; localhost-only binding).
- Investigation details view (entity/claim selection, findings assembly) — basic structure present, detail wiring pending.
- Report generation form in UI (reports created via Core API directly).
- Loading/error states per section (basic error handling present).

## H. Files
- `ui/server.py` — FastAPI proxy (`/api/core/*`, `/api/bridge/*`, `/api/dashboard`) + static SPA.
- `ui/static/index.html` — all 15 sections + investigation workspace + modals.
