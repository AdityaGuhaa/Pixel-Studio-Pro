# =============================
# PixelStudio Pro - compare.py
# E2B vs E4B side by side comparison endpoint
# =============================

import time
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.prompt_rewriter import rewrite_prompt
from backend.services.image_gen import generate_image
from backend.services.benchmark import create_benchmark_entry, compare_benchmarks

router = APIRouter()


class CompareRequest(BaseModel):
    prompt: str


class CompareResponse(BaseModel):
    user_prompt: str
    e2b: dict
    e4b: dict
    comparison: dict


@router.post("/", response_model=CompareResponse)
async def compare(request: CompareRequest):
    """
    Runs the full pipeline twice -- once with E2B, once with E4B.
    Returns both results and a comparison summary.
    """

    # --- Step 1: Rewrite prompt with both models concurrently ---
    try:
        e2b_rewritten, e4b_rewritten = await asyncio.gather(
            rewrite_prompt(request.prompt, model="e2b"),
            rewrite_prompt(request.prompt, model="e4b")
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Prompt rewriting failed. Are both llama.cpp servers running? Error: {str(e)}"
        )

    # --- Step 2: Generate images sequentially (VRAM constraint) ---
    e2b_gen_start = time.time()
    try:
        e2b_result = await generate_image(
            positive=e2b_rewritten["positive"],
            negative=e2b_rewritten["negative"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"E2B image generation failed. Error: {str(e)}"
        )
    e2b_gen_time = round(time.time() - e2b_gen_start, 2)

    e4b_gen_start = time.time()
    try:
        e4b_result = await generate_image(
            positive=e4b_rewritten["positive"],
            negative=e4b_rewritten["negative"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"E4B image generation failed. Error: {str(e)}"
        )
    e4b_gen_time = round(time.time() - e4b_gen_start, 2)

    # --- Step 3: Build benchmark entries ---
    e2b_entry = create_benchmark_entry(
        user_prompt=request.prompt,
        model="e2b",
        rewritten_prompt=e2b_rewritten,
        image_filename=e2b_result["image_filename"],
        image_gen_time=e2b_gen_time
    )

    e4b_entry = create_benchmark_entry(
        user_prompt=request.prompt,
        model="e4b",
        rewritten_prompt=e4b_rewritten,
        image_filename=e4b_result["image_filename"],
        image_gen_time=e4b_gen_time
    )

    # --- Step 4: Compare ---
    comparison = compare_benchmarks(e2b_entry, e4b_entry)

    return CompareResponse(
        user_prompt=request.prompt,
        e2b=e2b_entry,
        e4b=e4b_entry,
        comparison=comparison["comparison"]
    )