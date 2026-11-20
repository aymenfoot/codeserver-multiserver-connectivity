import hashlib
import re
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.hostname.lower() if parsed.hostname else ""
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    path = parsed.path or "/"
    if not path.startswith("/"):
        path = "/" + path
    # Drop tracking/query params that do not change identity
    keep = {"q", "query", "page", "format"}
    qs = [(k, v) for k, v in parse_qsl(parsed.query) if k.lower() in keep]
    query = urlencode(sorted(qs))
    return urlunparse((scheme, netloc, path, "", query, ""))


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate_content(url: str, content_type: Optional[str], byte_size: Optional[int],
                     text: Optional[str]) -> dict:
    notes = []
    is_valid = True
    if byte_size is not None and byte_size == 0:
        is_valid = False
        notes.append("empty body")
    if byte_size is not None and byte_size > 50 * 1024 * 1024:
        is_valid = False
        notes.append("document too large (>50MB)")
    allowed = ("text/html", "text/plain", "application/pdf", "application/xml",
               "application/json", "text/xml", "application/msword",
               "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    if content_type and content_type.split(";")[0].strip() not in allowed:
        notes.append(f"content type {content_type} may not be indexed")
    if text is None or len(text.strip()) == 0:
        is_valid = False
        notes.append("no extractable text")
    return {"is_valid": is_valid, "validation_notes": "; ".join(notes) if notes else None}
