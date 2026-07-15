#!/bin/bash

# =============================
# PixelStudio Pro - launch.sh
# One-command launcher for Mac and Linux
# =============================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMFYUI_DIR="$PROJECT_DIR/comfyui"
MODELS_DIR="$PROJECT_DIR/models"
LLAMA_DIR="$PROJECT_DIR/llama-cpp"
LOG_DIR="$PROJECT_DIR/logs"

E2B_MODEL="$MODELS_DIR/gemma-4-E2B-it-Q4_K_M.gguf"
E4B_MODEL="$MODELS_DIR/gemma-4-E4B-it-Q4_K_M.gguf"

# Initialize all PIDs
LLAMA_E2B_PID=""
LLAMA_E4B_PID=""
COMFYUI_PID=""
FASTAPI_PID=""

mkdir -p "$LOG_DIR"

echo -e "${BLUE}"
echo "  ██████╗ ██╗██╗  ██╗███████╗██╗     "
echo "  ██╔══██╗██║╚██╗██╔╝██╔════╝██║     "
echo "  ██████╔╝██║ ╚███╔╝ █████╗  ██║     "
echo "  ██╔═══╝ ██║ ██╔██╗ ██╔══╝  ██║     "
echo "  ██║     ██║██╔╝ ██╗███████╗███████╗"
echo "  ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝"
echo "  PixelStudio Pro -- Launcher"
echo -e "${NC}"

# --- Cleanup on exit ---
cleanup() {
    echo -e "\n${YELLOW}Shutting down all services...${NC}"
    [ -n "$LLAMA_E2B_PID" ] && kill "$LLAMA_E2B_PID" 2>/dev/null || true
    [ -n "$LLAMA_E4B_PID" ] && kill "$LLAMA_E4B_PID" 2>/dev/null || true
    [ -n "$COMFYUI_PID" ]   && kill "$COMFYUI_PID"   2>/dev/null || true
    [ -n "$FASTAPI_PID" ]   && kill "$FASTAPI_PID"   2>/dev/null || true
    echo -e "${GREEN}All services stopped.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# --- Activate conda env ---
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate pixelstudio

OS="$(uname -s)"
ARCH="$(uname -m)"

# --- Check models ---
echo -e "${BLUE}Checking models...${NC}"
[ ! -f "$E2B_MODEL" ] && echo -e "${RED}ERROR: Gemma E2B not found in models/${NC}" && exit 1
echo -e "${GREEN}✓ Models found${NC}"

# --- Determine GPU layers ---
if [ "$OS" = "Darwin" ] && [ "$ARCH" = "arm64" ]; then
    NGL_E2B=99
else
    NGL_E2B=43
fi

# --- Start llama.cpp E2B only (memory constraint) ---
echo -e "\n${BLUE}Starting llama.cpp E2B server...${NC}"
"$LLAMA_DIR/llama-server" \
    -m "$E2B_MODEL" \
    --host 127.0.0.1 \
    --port 8080 \
    -ngl $NGL_E2B \
    -c 2048 \
    --alias gemma-e2b \
    > "$LOG_DIR/llama-e2b.log" 2>&1 &
LLAMA_E2B_PID=$!
echo -e "${GREEN}✓ E2B server started (PID $LLAMA_E2B_PID)${NC}"
echo -e "${YELLOW}  NOTE: E4B disabled by default to prevent memory pressure${NC}"
echo -e "${YELLOW}  To enable E4B, start it manually on port 8081${NC}"

# --- Start ComfyUI ---
echo -e "\n${BLUE}Starting ComfyUI...${NC}"
(cd "$COMFYUI_DIR" && exec python main.py --listen 127.0.0.1 --port 8188 \
    > "$LOG_DIR/comfyui.log" 2>&1) &
COMFYUI_PID=$!
echo -e "${GREEN}✓ ComfyUI started (PID $COMFYUI_PID)${NC}"

# --- Wait for llama.cpp E2B ---
echo -e "\n${BLUE}Waiting for llama.cpp to be ready...${NC}"
set +e
for i in $(seq 1 30); do
    curl -s http://127.0.0.1:8080/health > /dev/null 2>&1 && break
    sleep 1
done
if ! curl -s http://127.0.0.1:8080/health > /dev/null 2>&1; then
    echo -e "${RED}ERROR: llama.cpp E2B failed to start. Check logs/llama-e2b.log${NC}"
    cleanup
fi
set -e
echo -e "${GREEN}✓ llama.cpp ready${NC}"

# --- Wait for ComfyUI ---
echo -e "${BLUE}Waiting for ComfyUI to be ready...${NC}"
set +e
for i in $(seq 1 300); do
    curl -s http://127.0.0.1:8188/system_stats > /dev/null 2>&1 && break
    sleep 1
done
if ! curl -s http://127.0.0.1:8188/system_stats > /dev/null 2>&1; then
    echo -e "${RED}ERROR: ComfyUI failed to start. Check logs/comfyui.log${NC}"
    cleanup
fi
set -e
echo -e "${GREEN}✓ ComfyUI ready${NC}"

# --- Start FastAPI ---
echo -e "\n${BLUE}Starting FastAPI backend...${NC}"
cd "$PROJECT_DIR"
uvicorn backend.main:app --host 0.0.0.0 --port 8001 \
    > "$LOG_DIR/fastapi.log" 2>&1 &
FASTAPI_PID=$!
echo -e "${GREEN}✓ FastAPI started (PID $FASTAPI_PID)${NC}"

sleep 2

# --- Open browser ---
if [ "$OS" = "Darwin" ]; then
    open http://127.0.0.1:8001
elif [ "$OS" = "Linux" ]; then
    xdg-open http://127.0.0.1:8001 2>/dev/null || true
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  PixelStudio Pro is running!${NC}"
echo -e "${GREEN}  URL: http://127.0.0.1:8001${NC}"
echo -e "${GREEN}  Logs: $LOG_DIR/${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}\n"

wait
