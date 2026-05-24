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
DEFAULT_STEPS = 25
DEFAULT_CFG = 7.0               # SDXL works best at 7-8
DEFAULT_WIDTH = 832
DEFAULT_HEIGHT = 1216           # JuggernautXL recommended portrait resolution
DEFAULT_SAMPLER = "dpmpp_2m"
DEFAULT_SCHEDULER = "karras"

# --- Model settings ---
CHECKPOINT_NAME = "Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors"

# --- Output settings ---
OUTPUT_DIR = "outputs"