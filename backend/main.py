# =============================
# PixelStudio Pro - main.py
# FastAPI application entry point
# =============================

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
    comfyui_url = f"http://127.0.0.1:8188/view?filename={filename}&type=output"
    async with httpx.AsyncClient() as client:
        response = await client.get(comfyui_url)
        response.raise_for_status()
    return StreamingResponse(
        iter([response.content]),
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# --- Route registration ---
app.include_router(generate.router, prefix="/api/generate", tags=["Generate"])
app.include_router(compare.router, prefix="/api/compare", tags=["Compare"])

# --- Serve frontend static files (must be last) ---
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")