# ORTA Intelligence Evaluation

Status: **Evaluation methodology designed; live execution pending target server, model credentials, and RAGFlow deployment.**

## A. Evaluation approach

ORTA evaluates generated answers against their source documents to ensure analytical integrity (no fabricated sources/evidence).

### Representative research questions
A fixed set of research questions with known source documents is used across evaluation runs. Questions are selected to exercise:
- Retrieval from indexed documents.
- Entity extraction.
- Claim extraction.
- Contradiction detection.
- Report generation with citations.

## B. Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| Retrieval relevance | Retrieved chunks contain the answer evidence | high precision@k |
| Citation correctness | Every cited chunk exists and supports the claim | 100% of citations verifiable |
| Extraction accuracy | Extracted entities/claims match source text | measured vs gold standard |
| Hallucination rate | Answer claims not supported by any source | 0% (any failure investigated) |
| Failure behavior | Invalid documents / timeouts handled gracefully | no silent success |

## C. Procedure

1. Index a known set of source documents into RAGFlow (dataset bound to a single embedding model).
2. Pose representative research questions via the investigation engine.
3. Retrieve chunks; verify each citation resolves to an indexed chunk with matching content.
4. Extract entities/claims; compare against gold-standard extractions.
5. Generate a report; verify every finding traces to evidence ids/document ids.
6. Record retrieval relevance, citation correctness, extraction accuracy, and failures.

## D. Distinctions maintained

- Source facts vs extracted statements vs model interpretations vs inferences vs unverified hypotheses.
- Citations + provenance throughout (document_id, chunk_id, dataset_id, retrieval query, similarity, model id, prompt version).

## E. Current state

No model credentials and no live RAGFlow instance in the build environment → evaluation is **pending target-server execution**. The Bridge client code and Core provenance model are ready to support it.
