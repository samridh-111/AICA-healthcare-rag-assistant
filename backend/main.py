import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path

_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)

from contextlib import asynccontextmanager

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Replaced on_event("startup") with lifespan

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Multimodal Clinical Intelligence Platform is running on Groq."
    }

@app.get("/.well-known/appspecific/com.chrome.devtools.json")
def chrome_devtools():
    return {}

frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")

if os.path.exists(frontend_dist):
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

@app.get("/")
def serve_frontend():
    index_path = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Multimodal Clinical Intelligence Platform API is running."}

from backend.api.routers import router as api_router
app.include_router(api_router, prefix="/api/v1")
