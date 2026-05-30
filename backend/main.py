# =============================
# PixelStudio Pro - main.py
# FastAPI application entry point
# =============================
import platform
import subprocess
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import httpx
from backend.routes import generate, compare

app = FastAPI(
    title="PixelStudio Pro",
    description="Local AI image generation with LLM prompt intelligence",
    version="1.0.0"
)

# --- CORS settings ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Health check ---
@app.get("/health")
async def health_check():
    return {"status": "PixelStudio Pro is running"}

# --- Image proxy (for same-origin downloads) ---
@app.get("/api/image/{filename}")
async def proxy_image(filename: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://127.0.0.1:8188/view",
            params={"filename": filename, "type": "output"}
        )
        response.raise_for_status()
    return StreamingResponse(
        iter([response.content]),
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# --- System info (auto hardware detection) ---
@app.get("/api/system")
async def system_info():
    os_name = platform.system()

    # --- Detect GPU ---
    gpu = "CPU"
    try:
        if os_name == "Darwin":
            result = subprocess.run(
                ["system_profiler", "SPHardwareDataType"],
                capture_output=True, text=True
            )
            for line in result.stdout.splitlines():
                if "Chip" in line or "Processor Name" in line:
                    gpu = line.split(":")[-1].strip()
                    break
        else:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                gpu = result.stdout.strip().split("\n")[0]
    except Exception:
        gpu = "Unknown GPU"

    # --- Detect RAM ---
    try:
        import psutil
        ram_gb = round(psutil.virtual_memory().total / (1024 ** 3))
        ram = f"{ram_gb}GB RAM"
    except ImportError:
        ram = ""

    # --- OS label ---
    os_labels = {"Darwin": "MACOS", "Linux": "LINUX", "Windows": "WINDOWS"}
    os_label = os_labels.get(os_name, os_name.upper())

    return {
        "gpu": gpu.upper(),
        "os": os_label,
        "platform": f"{gpu.upper()} · {os_label}"
    }

# --- Route registration ---
app.include_router(generate.router, prefix="/api/generate", tags=["Generate"])
app.include_router(compare.router, prefix="/api/compare", tags=["Compare"])

# --- Serve frontend static files (must be last) ---
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")