# =============================
# PixelStudio Pro - generate.py
# Single image generation endpoint
# =============================

import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.prompt_rewriter import rewrite_prompt
from backend.services.image_gen import generate_image
from backend.services.benchmark import create_benchmark_entry

router = APIRouter()


class GenerateRequest(BaseModel):
    prompt: str
    model: str = "e2b"          # default to E2B


class GenerateResponse(BaseModel):
    user_prompt: str
    positive_prompt: str
    negative_prompt: str
    image_filename: str
    rewrite_latency_seconds: float
    image_gen_latency_seconds: float
    total_latency_seconds: float
    model_used: str


@router.post("/", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """
    Full pipeline:
    1. Rewrite user prompt via LLM
    2. Generate image via ComfyUI
    3. Return image + benchmark data
    """

    # --- Validate model choice ---
    if request.model not in ["e2b", "e4b"]:
        raise HTTPException(
            status_code=400,
            detail="model must be 'e2b' or 'e4b'"
        )

    # --- Step 1: Rewrite prompt ---
    try:
        rewritten = await rewrite_prompt(request.prompt, model=request.model)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Prompt rewriting failed. Is llama.cpp server running? Error: {str(e)}"
        )

    # --- Step 2: Generate image ---
    image_gen_start = time.time()
    try:
        result = await generate_image(
            positive=rewritten.get("positive") or "photorealistic image, high quality, detailed",
            negative=rewritten.get("negative") or "blurry, low quality, distorted, bad anatomy"
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Image generation failed. Is ComfyUI running? Error: {str(e)}"
        )
    image_gen_time = round(time.time() - image_gen_start, 2)

    # --- Step 3: Build benchmark entry ---
    entry = create_benchmark_entry(
        user_prompt=request.prompt,
        model=request.model,
        rewritten_prompt=rewritten,
        image_filename=result["image_filename"],
        image_gen_time=image_gen_time
    )

    return GenerateResponse(**entry)