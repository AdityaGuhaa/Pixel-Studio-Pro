# =============================
# PixelStudio Pro - prompt_rewriter.py
# Handles LLM-based prompt rewriting via llama.cpp HTTP server
# =============================

import httpx
import time
import json
import re
from backend.config import LLAMACPP_HOST, LLAMACPP_PORT_E2B, LLAMACPP_PORT_E4B

SYSTEM_PROMPT = """You are an expert Stable Diffusion prompt engineer.
Convert the user's description into a high-quality image generation prompt.
You MUST respond with ONLY a JSON object, no markdown, no explanation, no code fences.
The JSON must have exactly two keys: "positive" and "negative".
Example response:
{"positive": "ultra realistic portrait, cinematic lighting, sharp focus, 85mm lens, detailed skin texture, golden hour", "negative": "blurry, low quality, distorted face, bad anatomy, extra fingers, watermark"}"""


async def rewrite_prompt(user_prompt: str, model: str = "e2b") -> dict:
    """
    Sends user prompt to llama.cpp server and returns rewritten prompt.
    model: "e2b" or "e4b"
    """
    port = LLAMACPP_PORT_E2B if model == "e2b" else LLAMACPP_PORT_E4B
    url = f"{LLAMACPP_HOST}:{port}/v1/chat/completions"

    payload = {
        "model": "gemma",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Convert this to an image prompt: {user_prompt}"}
        ],
        "temperature": 0.7,
        "max_tokens": 1024
    }

    start_time = time.time()

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()

    elapsed = round(time.time() - start_time, 2)
    result = response.json()

    # --- Extract content ---
    message = result["choices"][0]["message"]
    content = message.get("content", "").strip()

    # Gemma 4 thinking models may put output in reasoning_content
    if not content:
        content = message.get("reasoning_content", "").strip()

    print(f"DEBUG raw content: {repr(content[:200])}")

    # --- Parse JSON from content ---
    parsed = None

    # Attempt 1: direct JSON parse
    try:
        parsed = json.loads(content)
    except (json.JSONDecodeError, ValueError):
        pass

    # Attempt 2: extract JSON block from markdown or mixed text
    if not parsed:
        try:
            json_match = re.search(r'\{[^{}]*"positive"[^{}]*"negative"[^{}]*\}', content, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
        except (json.JSONDecodeError, ValueError):
            pass

    # Attempt 3: extract from reasoning_content directly
    if not parsed:
        try:
            reasoning = message.get("reasoning_content", "")
            json_match = re.search(r'\{[^{}]*"positive"[^{}]*"negative"[^{}]*\}', reasoning, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
        except (json.JSONDecodeError, ValueError):
            pass

    # Final fallback: use user prompt directly
    if not parsed or "positive" not in parsed:
        parsed = {
            "positive": f"{user_prompt}, photorealistic, cinematic lighting, high quality, detailed, sharp focus",
            "negative": "blurry, low quality, distorted, bad anatomy, watermark, text, logo"
        }

    parsed["latency_seconds"] = elapsed
    parsed["model_used"] = model
    return parsed