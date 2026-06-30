from dotenv import load_dotenv
from pathlib import Path

# Load repository-level .env (safe if it contains only placeholders in repo)
_env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=_env_path)

# Re-export the FastAPI app defined in backend.main so Render/Vercel auto-detects it
try:
    from backend.main import app  # exposes `app` for ASGI servers
except Exception as e:
    # Fail early with a clear error if the backend app cannot be imported
    raise

if __name__ == "__main__":
    import os
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), reload=False)
