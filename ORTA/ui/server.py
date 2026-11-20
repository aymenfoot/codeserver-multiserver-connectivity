import os
import httpx
from fastapi import FastAPI, Request, Query
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

CORE_URL = os.environ.get("ORTA_CORE_URL", "http://127.0.0.1:8100")
BRIDGE_URL = os.environ.get("ORTA_BRIDGE_URL", "http://127.0.0.1:8101")

UI_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(UI_DIR, "static")

app = FastAPI(title="ORTA Unified UI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


# ---------- API proxy to Core ----------
@app.api_route("/api/core/{path:path}", methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
async def core_proxy(request: Request, path: str):
    return await _proxy(CORE_URL, request, path)


# ---------- API proxy to Bridge ----------
@app.api_route("/api/bridge/{path:path}", methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
async def bridge_proxy(request: Request, path: str):
    return await _proxy(BRIDGE_URL, request, path)


async def _proxy(base: str, request: Request, path: str):
    body = await request.body()
    headers = {k: v for k, v in request.headers.items()
               if k.lower() not in ("host", "content-length")}
    params = dict(request.query_params)
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.request(
                request.method, f"{base}/api/v1/{path}",
                params=params, content=body, headers=headers)
        try:
            content = resp.json()
        except Exception:
            content = {"text": resp.text}
        return JSONResponse(content=content, status_code=resp.status_code)
    except httpx.RequestError as exc:
        return JSONResponse(content={"error": f"upstream unreachable: {base} ({exc})"},
                            status_code=502)


# ---------- Aggregated dashboard ----------
@app.get("/api/dashboard")
async def dashboard():
    data = {"services": {}, "counts": {}, "jobs": {}, "errors": []}
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Core health
        try:
            r = await client.get(f"{CORE_URL}/healthz")
            data["services"]["core"] = r.json() if r.status_code == 200 else {"status": "unhealthy"}
        except Exception as exc:
            data["services"]["core"] = {"status": "unreachable", "error": str(exc)}
        # Bridge health
        try:
            r = await client.get(f"{BRIDGE_URL}/healthz")
            data["services"]["bridge"] = r.json() if r.status_code == 200 else {"status": "unhealthy"}
        except Exception as exc:
            data["services"]["bridge"] = {"status": "unreachable", "error": str(exc)}
        # Counts
        try:
            r = await client.get(f"{CORE_URL}/api/v1/sources?limit=1")
            data["counts"]["sources"] = len(r.json())
        except Exception:
            data["counts"]["sources"] = 0
        try:
            r = await client.get(f"{CORE_URL}/api/v1/evidence?limit=1")
            data["counts"]["evidence"] = len(r.json())
        except Exception:
            data["counts"]["evidence"] = 0
        try:
            r = await client.get(f"{CORE_URL}/api/v1/entities?limit=1")
            data["counts"]["entities"] = len(r.json())
        except Exception:
            data["counts"]["entities"] = 0
        try:
            r = await client.get(f"{CORE_URL}/api/v1/claims?limit=1")
            data["counts"]["claims"] = len(r.json())
        except Exception:
            data["counts"]["claims"] = 0
        try:
            r = await client.get(f"{CORE_URL}/api/v1/investigations?limit=1")
            data["counts"]["investigations"] = len(r.json())
        except Exception:
            data["counts"]["investigations"] = 0
        try:
            r = await client.get(f"{CORE_URL}/api/v1/reports?limit=1")
            data["counts"]["reports"] = len(r.json())
        except Exception:
            data["counts"]["reports"] = 0
        # Jobs
        try:
            r = await client.get(f"{BRIDGE_URL}/api/v1/jobs?limit=100")
            jobs = r.json()
            data["jobs"]["all"] = jobs
            data["jobs"]["pending"] = [j for j in jobs if j.get("status") == "pending"]
            data["jobs"]["running"] = [j for j in jobs if j.get("status") == "running"]
            data["jobs"]["completed"] = [j for j in jobs if j.get("status") == "completed"]
            data["jobs"]["failed"] = [j for j in jobs if j.get("status") == "failed"]
            data["jobs"]["dead_letter"] = [j for j in jobs if j.get("dead_letter")]
        except Exception:
            data["jobs"]["all"] = []
            data["jobs"]["pending"] = []
            data["jobs"]["running"] = []
            data["jobs"]["failed"] = []
            data["jobs"]["dead_letter"] = []
    return data
