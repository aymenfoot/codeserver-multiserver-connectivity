# ORTA Model Infrastructure

Status: **Provider abstraction designed; RAGFlow v1.0.0 model/embedding contract researched; live model integration pending target server and credentials.**

## A. Embeddings

ORTA uses a provider abstraction for embeddings so the indexing and query models stay consistent.

### Design (`EmbeddingProvider` interface)
- `EmbedTexts([]string) ([][]float32, error)`
- `Dimensions() int`
- `ModelID() string`

### Implementations (planned)
1. **RAGFlow-backed** via `POST /api/v1/command/embeddings` (EmbedText) — route verified in v1.0.0, schema to be confirmed live.
2. **Local fallback** — preserve any working local embedding service (e.g. sentence-transformers/ONNX) for offline/dev. Never removed to force RAGFlow adoption.

### Consistency
- A dataset binds exactly one `embedding_model` at creation (RAGFlow v1.0.0).
- ORTA records `dataset_id` + `embedding_model_id` used at index time and requires the same model id for query-time embedding to avoid cross-model vector mismatch.
- Dimensions recorded per model with the vector.

### Unverified (pending live instance)
- Exact `EmbedText` request/response schema.
- Model identity, dimensions, input/token limits, batch size.

## B. LLM capabilities

Provider abstraction (`LLMProvider` interface):
- `Complete(messages, options) (string, error)`
- Structured variants built on `Complete` with JSON-schema prompting:
  - Content understanding
  - Entity extraction
  - Claim extraction
  - Classification
  - Summarization
  - Investigation planning
  - Evidence analysis
  - Report generation

### Implementations (planned)
1. **RAGFlow-backed** via `POST /api/v1/command/chat/to-model` (ChatToModel).
2. **OpenAI-compatible endpoint** (configurable base URL + API key).

### Configuration
- Provider + model + base URL + credentials from deployment environment variables (`ORTA/secrets/`, gitignored).
- No credentials invented; no credentials hardcoded.
- If external credentials unavailable, affected functions reported as unverified and fall back to local/offline paths.

## C. Reranking

- RAGFlow supports `rerank_id` in `POST /api/v1/retrieval` and `POST /api/v1/command/rerank`.
- **Disabled by default.** Enabled only after retrieval-quality verification (see INTELLIGENCE-EVALUATION.md).
- `RerankerProvider` interface: `Rerank(query, candidates) (reranked, error)`.

## D. Provider flexibility

- Single abstraction layer; changing providers does not rewrite ORTA Core.
- Credentials via environment variables/secrets only.
- RAGFlow is the document index/retrieval backend; ORTA owns the intelligence model layer (not a fork of RAGFlow's model UI).

## E. Analytical integrity

Every statement classified into one of five tiers with citations/provenance:

| Tier | Definition | Provenance requirement |
|------|------------|------------------------|
| Source fact | Verbatim/near-verbatim from source document | Source URL + document ID + chunk ID + offset |
| Extracted statement | Produced by extraction model from source text | Model id + prompt version + source chunk(s) + confidence |
| Model interpretation | Model synthesis/summary/reasoning over retrieved chunks | Model id + retrieved chunk IDs + retrieval query + rerank id |
| Inference | Conclusion combining multiple extracted statements | Input statement IDs + inference rule/chain + confidence |
| Unverified hypothesis | Not backed by source/model evidence | Flagged; requires investigation task; not surfaced as fact |

ORTA persists `document_id`, `chunk_id`, `dataset_id`, retrieval query, similarity score, model id, prompt version for every extracted/interpreted statement. Reports cite chunk-level sources.

## F. Evaluation (prepared)

Methods (see INTELLIGENCE-EVALUATION.md):
- Retrieval relevance, citation correctness, extraction accuracy.
- Representative research questions compared against source documents.
- Failure behavior measurement.

Pending live model/credentials for execution.
