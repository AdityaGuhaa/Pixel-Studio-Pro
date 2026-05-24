# =============================
# PixelStudio Pro - main.py
# FastAPI application entry point
# =============================

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
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

# --- Health check (must be before static mount) ---
@app.get("/health")
async def health_check():
    return {"status": "PixelStudio Pro is running"}

# --- Route registration ---
app.include_router(generate.router, prefix="/api/generate", tags=["Generate"])
app.include_router(compare.router, prefix="/api/compare", tags=["Compare"])

# --- Serve frontend static files (must be last) ---
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")