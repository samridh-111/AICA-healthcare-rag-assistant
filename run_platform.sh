#!/bin/bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}  AICA — Multimodal Clinical Intelligence   ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}\n"

# 1. Activate or create virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi
source venv/bin/activate
echo -e "${GREEN}✅ Virtualenv active${NC}\n"

# 2. Install / update dependencies quietly
pip install -q -r requirements.txt

# 3. Check FastAPI backend is reachable (optional: warn about missing .env)
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠  No .env file found. Backend may fail without API keys.${NC}\n"
fi

# 4. Start FastAPI backend in background
echo -e "${YELLOW}Starting FastAPI backend on http://localhost:8000 ...${NC}"
BACKEND_URL=http://localhost:8000 uvicorn backend.main:app \
    --host 0.0.0.0 --port 8000 --reload --log-level warning &
BACKEND_PID=$!
echo -e "${GREEN}✅ Backend started (PID $BACKEND_PID)${NC}\n"

# Give it a moment to boot
sleep 2

# 5. Start Streamlit frontend
echo -e "${YELLOW}Starting Streamlit frontend on http://localhost:8501 ...${NC}"
echo -e "${GREEN}══════════════════════════════════════${NC}"
echo -e "${GREEN}  Open:  http://localhost:8501         ${NC}"
echo -e "${GREEN}  API:   http://localhost:8000/docs    ${NC}"
echo -e "${GREEN}══════════════════════════════════════${NC}\n"

BACKEND_URL=http://localhost:8000 streamlit run streamlit_app.py \
    --server.headless true \
    --server.port 8501 \
    --theme.base "light"

# On exit, kill backend too
kill $BACKEND_PID 2>/dev/null
