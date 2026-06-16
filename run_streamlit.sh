#!/bin/bash

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running setup..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo ""
echo "═══════════════════════════════════════"
echo "  AICA — Starting Streamlit Frontend  "
echo "═══════════════════════════════════════"
echo ""
echo "  ⚠  Make sure FastAPI backend is running first:"
echo "     uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "  Open: http://localhost:8501"
echo ""

BACKEND_URL=${BACKEND_URL:-http://localhost:8000} \
streamlit run streamlit_app.py \
    --server.headless true \
    --server.port 8501 \
    --theme.base "light" \
    --logger.level=info
