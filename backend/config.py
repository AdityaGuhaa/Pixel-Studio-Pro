# =============================
# PixelStudio Pro - config.py
# Central configuration for all services
# =============================

# --- llama.cpp server settings ---
LLAMACPP_HOST = "http://127.0.0.1"
LLAMACPP_PORT_E2B = 8080        # E2B model server port
LLAMACPP_PORT_E4B = 8081        # E4B model server port

# --- ComfyUI settings ---
COMFYUI_HOST = "127.0.0.1"
COMFYUI_PORT = 8188
COMFYUI_URL = f"http://{COMFYUI_HOST}:{COMFYUI_PORT}"
COMFYUI_WS_URL = f"ws://{COMFYUI_HOST}:{COMFYUI_PORT}"

# --- Model paths ---
E2B_MODEL_PATH = "/home/adityaguha/gemma-4-E2B-it-Q4_K_M.gguf"
E4B_MODEL_PATH = "/home/adityaguha/gemma-4-E4B-it-Q4_K_M.gguf"

# --- Generation defaults ---
DEFAULT_STEPS = 20
DEFAULT_CFG = 1.0               # Flux uses low CFG (1.0 - 3.5)
DEFAULT_WIDTH = 768
DEFAULT_HEIGHT = 768
DEFAULT_SAMPLER = "euler"
DEFAULT_SCHEDULER = "simple"

# --- Output settings ---
OUTPUT_DIR = "outputs"