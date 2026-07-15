#!/bin/bash

# =============================
# PixelStudio Pro - install.sh
# One-command setup for Mac and Linux
# =============================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMFYUI_DIR="$PROJECT_DIR/comfyui"
MODELS_DIR="$PROJECT_DIR/models"
LLAMA_DIR="$PROJECT_DIR/llama-cpp"
COMFYUI_COMMIT="3af8643d90424b6d5ceddf60fd9a1cef5ad1a4e5"

echo -e "${BLUE}"
echo "  ██████╗ ██╗██╗  ██╗███████╗██╗     "
echo "  ██╔══██╗██║╚██╗██╔╝██╔════╝██║     "
echo "  ██████╔╝██║ ╚███╔╝ █████╗  ██║     "
echo "  ██╔═══╝ ██║ ██╔██╗ ██╔══╝  ██║     "
echo "  ██║     ██║██╔╝ ██╗███████╗███████╗"
echo "  ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝"
echo "  PixelStudio Pro -- Installer"
echo -e "${NC}"

OS="$(uname -s)"
ARCH="$(uname -m)"
echo -e "${YELLOW}Detected: $OS $ARCH${NC}"

# --- Check prerequisites ---
echo -e "\n${BLUE}[1/6] Checking prerequisites...${NC}"

if ! command -v conda &>/dev/null; then
    echo -e "${RED}ERROR: conda not found. Install Miniconda first.${NC}"
    echo "Download: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi
echo -e "${GREEN}✓ conda found${NC}"

if ! command -v git &>/dev/null; then
    echo -e "${RED}ERROR: git not found.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ git found${NC}"

# --- Create conda environment ---
echo -e "\n${BLUE}[2/6] Setting up conda environment...${NC}"
if conda env list | grep -q "pixelstudio"; then
    echo -e "${YELLOW}Environment 'pixelstudio' already exists, skipping...${NC}"
else
    conda create -n pixelstudio python=3.10 -y
    echo -e "${GREEN}✓ conda environment created${NC}"
fi

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate pixelstudio

# --- Install Python dependencies ---
echo -e "\n${BLUE}[3/6] Installing Python dependencies...${NC}"
cd "$PROJECT_DIR"
pip install -r requirements.txt --quiet
echo -e "${GREEN}✓ Python dependencies installed${NC}"

# --- Clone ComfyUI ---
echo -e "\n${BLUE}[4/6] Setting up ComfyUI...${NC}"
if [ -d "$COMFYUI_DIR" ]; then
    echo -e "${YELLOW}ComfyUI already exists, skipping...${NC}"
else
    git clone https://github.com/comfyanonymous/ComfyUI.git "$COMFYUI_DIR"
    cd "$COMFYUI_DIR"
    git checkout "$COMFYUI_COMMIT"
    pip install -r requirements.txt --quiet
    echo -e "${GREEN}✓ ComfyUI installed${NC}"
fi
cd "$PROJECT_DIR"

# --- Symlink checkpoint to ComfyUI ---
echo -e "\n${BLUE}Linking models to ComfyUI...${NC}"
CHECKPOINT="$MODELS_DIR/Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors"
COMFYUI_CHECKPOINTS="$COMFYUI_DIR/models/checkpoints"
if [ -f "$CHECKPOINT" ]; then
    ln -sf "$CHECKPOINT" "$COMFYUI_CHECKPOINTS/Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors"
    echo -e "${GREEN}✓ Checkpoint linked${NC}"
else
    echo -e "${YELLOW}WARNING: JuggernautXL not found in models/ -- add it before running${NC}"
fi

# --- Download llama.cpp binary ---
echo -e "\n${BLUE}[5/6] Setting up llama.cpp...${NC}"
mkdir -p "$LLAMA_DIR"

if [ -f "$LLAMA_DIR/llama-server" ]; then
    echo -e "${YELLOW}llama-server already exists, skipping...${NC}"
else
    if [ "$OS" = "Darwin" ]; then
        if [ "$ARCH" = "arm64" ]; then
            echo "Downloading llama.cpp for Apple Silicon..."
            curl -L -o "$LLAMA_DIR/llama-cpp.zip" \
                "https://github.com/ggml-org/llama.cpp/releases/download/b9354/llama-b9354-bin-macos-arm64.zip"
        else
            echo "Downloading llama.cpp for Intel Mac..."
            curl -L -o "$LLAMA_DIR/llama-cpp.zip" \
                "https://github.com/ggml-org/llama.cpp/releases/download/b9354/llama-b9354-bin-macos-x64.zip"
        fi
    elif [ "$OS" = "Linux" ]; then
        echo "Downloading llama.cpp for Linux..."
        curl -L -o "$LLAMA_DIR/llama-cpp.zip" \
            "https://github.com/ggml-org/llama.cpp/releases/download/b9354/llama-b9354-bin-ubuntu-x64.zip"
    fi

    cd "$LLAMA_DIR"
    unzip -q llama-cpp.zip
    rm llama-cpp.zip

    # Find llama-server regardless of extraction structure
    LLAMA_BIN=$(find "$LLAMA_DIR" -name "llama-server" -type f | head -1)
    if [ -n "$LLAMA_BIN" ] && [ "$LLAMA_BIN" != "$LLAMA_DIR/llama-server" ]; then
        mv "$LLAMA_BIN" "$LLAMA_DIR/llama-server"
    fi
    chmod +x "$LLAMA_DIR/llama-server"
    echo -e "${GREEN}✓ llama.cpp installed${NC}"
    cd "$PROJECT_DIR"
fi

# --- Verify models ---
echo -e "\n${BLUE}[6/6] Verifying models...${NC}"
E2B="$MODELS_DIR/gemma-4-E2B-it-Q4_K_M.gguf"
E4B="$MODELS_DIR/gemma-4-E4B-it-Q4_K_M.gguf"
XL="$MODELS_DIR/Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors"

[ -f "$E2B" ] && echo -e "${GREEN}✓ Gemma E2B found${NC}" || echo -e "${RED}✗ Gemma E2B missing -- add to models/${NC}"
[ -f "$E4B" ] && echo -e "${GREEN}✓ Gemma E4B found${NC}" || echo -e "${RED}✗ Gemma E4B missing -- add to models/${NC}"
[ -f "$XL" ]  && echo -e "${GREEN}✓ JuggernautXL found${NC}" || echo -e "${RED}✗ JuggernautXL missing -- add to models/${NC}"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Installation complete!${NC}"
echo -e "${GREEN}  Run: bash launch.sh to start${NC}"
echo -e "${GREEN}========================================${NC}"
