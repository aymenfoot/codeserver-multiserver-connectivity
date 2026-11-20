import hashlib
import time
from typing import Any, Dict, List, Optional
import requests

from models import JobErrorClass


class BridgeError(Exception):
    def __init__(self, message: str, error_class: JobErrorClass = JobErrorClass.transient,
                 retryable: bool = True, status_code: Optional[int] = None):
        super().__init__(message)
        self.error_class = error_class
        self.retryable = retryable
        self.status_code = status_code


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class HttpClient:
    def __init__(self, base_url: str, timeout: float = 15.0, headers: Optional[Dict[str, str]] = None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(headers or {})

    def _classify(self, exc: Exception, status_code: Optional[int] = None) -> JobErrorClass:
        if status_code is not None:
            if status_code in (401, 403):
                return JobErrorClass.permanent
            if status_code in (429,):
                return JobErrorClass.policy
            if status_code in (400, 404, 409, 415, 422):
                return JobErrorClass.permanent
            if status_code >= 500:
                return JobErrorClass.transient
        if isinstance(exc, requests.exceptions.Timeout):
            return JobErrorClass.transient
        if isinstance(exc, requests.exceptions.ConnectionError):
            return JobErrorClass.transient
        return JobErrorClass.transient

    def get(self, path: str, params: Optional[Dict] = None,
            headers: Optional[Dict[str, str]] = None) -> requests.Response:
        try:
            return self.session.get(f"{self.base_url}{path}", params=params,
                                    headers=headers, timeout=self.timeout)
        except requests.exceptions.RequestException as exc:
            raise BridgeError(str(exc), error_class=self._classify(exc), retryable=True)

    def post(self, path: str, json: Optional[Dict] = None, data: Optional[Dict] = None,
             files: Optional[Dict] = None, headers: Optional[Dict[str, str]] = None) -> requests.Response:
        try:
            return self.session.post(f"{self.base_url}{path}", json=json, data=data,
                                     files=files, headers=headers, timeout=self.timeout)
        except requests.exceptions.RequestException as exc:
            raise BridgeError(str(exc), error_class=self._classify(exc), retryable=True)


class CoreClient(HttpClient):
    """Client to ORTA Intelligence Core for synchronizing evidence/entities/claims."""

    def create_evidence(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        r = self.post("/api/v1/evidence", json=evidence)
        if r.status_code in (409, 400):
            # Already exists (idempotent) — return existing
            return r.json()
        r.raise_for_status()
        return r.json()

    def create_claim(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        r = self.post("/api/v1/claims", json=claim)
        if r.status_code in (409, 400):
            return r.json()
        r.raise_for_status()
        return r.json()

    def create_entity(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        r = self.post("/api/v1/entities", json=entity)
        if r.status_code in (409, 400):
            return r.json()
        r.raise_for_status()
        return r.json()

    def create_investigation(self, inv: Dict[str, Any]) -> Dict[str, Any]:
        r = self.post("/api/v1/investigations", json=inv)
        if r.status_code in (409, 400):
            return r.json()
        r.raise_for_status()
        return r.json()

    def create_report(self, investigation_id: int, report: Dict[str, Any]) -> Dict[str, Any]:
        r = self.post(f"/api/v1/reports?investigation_id={investigation_id}", json=report)
        r.raise_for_status()
        return r.json()

    def health(self) -> bool:
        try:
            r = self.get("/healthz")
            return r.status_code == 200
        except Exception:
            return False


class SearXNGClient(HttpClient):
    """Client to SearXNG metasearch (JSON output via ?format=json)."""

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        r = self.get("/search", params={"q": query, "format": "json", "limit": limit})
        if r.status_code == 429:
            raise BridgeError("SearXNG rate limited", error_class=JobErrorClass.policy,
                              retryable=True, status_code=429)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        out = []
        for item in results[:limit]:
            out.append({
                "url": item.get("url"),
                "title": item.get("title"),
                "content": item.get("content"),
                "engine": item.get("engine"),
                "score": item.get("score"),
            })
        return out


class RAGFlowClient(HttpClient):
    """Client to RAGFlow v1.0.0 REST API (Bearer token auth, version-specific)."""

    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: float = 30.0,
                 headers: Optional[Dict[str, str]] = None):
        super().__init__(base_url, timeout=timeout, headers=headers)
        self.api_key = api_key
        self._token: Optional[str] = None

    def _auth_headers(self) -> Dict[str, str]:
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        elif self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def login(self, email: str, password: str) -> str:
        """RAGFlow v1.0.0 authenticates via /api/v1/auth/login returning a token."""
        r = self.post("/api/v1/auth/login", json={"email": email, "password": password})
        if r.status_code in (401, 403):
            raise BridgeError("RAGFlow authentication failed", error_class=JobErrorClass.permanent,
                              retryable=False, status_code=r.status_code)
        r.raise_for_status()
        data = r.json()
        token = data.get("token") or data.get("access_token")
        if not token:
            raise BridgeError("RAGFlow login returned no token", error_class=JobErrorClass.permanent)
        self._token = token
        return token

    def create_dataset(self, name: str, description: Optional[str] = None,
                       embedding_model: Optional[str] = None,
                       parser_id: str = "general") -> Dict[str, Any]:
        body = {
            "name": name,
            "parse_type": 1,
            "parser_id": parser_id,
            "permission": "me",
        }
        if description:
            body["description"] = description
        if embedding_model:
            body["embedding_model"] = embedding_model
        r = self.post("/api/v1/datasets", json=body,
                      headers=self._auth_headers())
        if r.status_code in (401, 403):
            raise BridgeError("RAGFlow auth failed", error_class=JobErrorClass.permanent,
                              retryable=False, status_code=r.status_code)
        if r.status_code == 409:
            return r.json()
        r.raise_for_status()
        return r.json()

    def upload_document(self, dataset_id: str, file_name: str, file_bytes: bytes,
                        content_type: str = "text/plain") -> Dict[str, Any]:
        """v1.0.0: POST /api/v1/datasets/{dataset_id}/documents, type=local, multipart file."""
        files = {"file": (file_name, file_bytes, content_type)}
        data = {"type": "local"}
        r = self.post(f"/api/v1/datasets/{dataset_id}/documents", data=data, files=files,
                      headers=self._auth_headers())
        if r.status_code in (401, 403):
            raise BridgeError("RAGFlow auth failed", error_class=JobErrorClass.permanent,
                              retryable=False, status_code=r.status_code)
        if r.status_code == 415:
            raise BridgeError("RAGFlow unsupported file type",
                              error_class=JobErrorClass.permanent, retryable=False,
                              status_code=415)
        r.raise_for_status()
        return r.json()

    def list_documents(self, dataset_id: str, run_status: Optional[str] = None) -> Dict[str, Any]:
        params = {}
        if run_status:
            params["run_status"] = run_status
        r = self.get(f"/api/v1/datasets/{dataset_id}/documents", params=params,
                     headers=self._auth_headers())
        r.raise_for_status()
        return r.json()

    def document_status(self, document_id: str) -> Dict[str, Any]:
        r = self.get(f"/api/v1/documents/{document_id}", headers=self._auth_headers())
        r.raise_for_status()
        return r.json()

    def start_ingestion(self, dataset_id: str, document_ids: Optional[List[str]] = None
                        ) -> Dict[str, Any]:
        r = self.post(f"/api/v1/datasets/{dataset_id}/documents/parse",
                      json={"document_ids": document_ids or []},
                      headers=self._auth_headers())
        r.raise_for_status()
        return r.json()

    def list_ingestion_tasks(self, dataset_id: Optional[str] = None) -> Dict[str, Any]:
        params = {"dataset_id": dataset_id} if dataset_id else {}
        r = self.get("/api/v1/ingestion/tasks", params=params,
                     headers=self._auth_headers())
        r.raise_for_status()
        return r.json()

    def retrieval(self, query: str, dataset_ids: Optional[List[str]] = None,
                  top_k: int = 10, similarity_threshold: float = 0.2,
                  rerank_id: Optional[str] = None) -> Dict[str, Any]:
        r = self.post("/api/v1/retrieval", json={
            "question": query,
            "dataset_ids": dataset_ids or [],
            "top_k": top_k,
            "similarity_threshold": similarity_threshold,
            "rerank_id": rerank_id,
        }, headers=self._auth_headers())
        r.raise_for_status()
        return r.json()

    def embed_text(self, texts: List[str], provider: Optional[str] = None,
                   model: Optional[str] = None) -> Dict[str, Any]:
        r = self.post("/api/v1/command/embeddings", json={
            "texts": texts, "provider": provider, "model": model,
        }, headers=self._auth_headers())
        r.raise_for_status()
        return r.json()

    def rerank(self, query: str, documents: List[str],
               model: Optional[str] = None) -> Dict[str, Any]:
        r = self.post("/api/v1/command/rerank", json={
            "query": query, "documents": documents, "model": model,
        }, headers=self._auth_headers())
        r.raise_for_status()
        return r.json()

    def health(self) -> bool:
        try:
            r = self.get("/api/v1/system/healthz", headers=self._auth_headers())
            return r.status_code == 200
        except Exception:
            return False
