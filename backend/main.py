import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
from contextlib import asynccontextmanager

# Load .env from repo root (works for local dev; in production env vars are injected directly)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("✅ Multimodal Clinical Intelligence Platform API starting up with Groq...")
    yield
    print("🛑 Shutting down Multimodal Clinical Intelligence Platform API...")
    try:
        from backend.groq.provider import get_llm_provider
        provider = get_llm_provider()
        if hasattr(provider, 'close'):
            await provider.close()
    except Exception as e:
        print(f"Error closing provider: {e}")

app = FastAPI(title="Multimodal Clinical Intelligence Platform API", lifespan=lifespan)

# ---------------------------------------------------------------------------
# CORS
# In production, restrict to the known Vercel frontend domain.
# VERCEL_URL env var (e.g. "https://my-app.vercel.app") can be set in Render.
# Fallback to "*" preserves local dev behaviour.
# ---------------------------------------------------------------------------
_allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "*")
if _allowed_origins_raw == "*":
    _allowed_origins = ["*"]
else:
    _allowed_origins = [o.strip() for o in _allowed_origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=_allowed_origins != ["*"],  # credentials require explicit origins
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Multimodal Clinical Intelligence Platform is running on Groq.",
        "timestamp": datetime.utcnow().isoformat(),
    }

@app.get("/.well-known/appspecific/com.chrome.devtools.json")
def chrome_devtools():
    return {}

# ---------------------------------------------------------------------------
# Serve the compiled Vite frontend if it exists.
# Uses resolve() for an absolute path — safe regardless of CWD.
# On Render the frontend is NOT built (frontend is on Vercel), so this block
# is silently skipped. On local unified-mode it serves the built dist/.
# ---------------------------------------------------------------------------
_repo_root = Path(__file__).resolve().parent.parent
frontend_dist = _repo_root / "frontend" / "dist"

if frontend_dist.exists():
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

@app.get("/")
def serve_frontend():
    index_path = frontend_dist / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Multimodal Clinical Intelligence Platform API is running."}

from backend.api.routers import router as api_router
app.include_router(api_router, prefix="/api/v1")
