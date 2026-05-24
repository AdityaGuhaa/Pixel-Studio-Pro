# =============================
# PixelStudio Pro - prompt_rewriter.py
# Handles LLM-based prompt rewriting via llama.cpp HTTP server
# =============================

import httpx
import time
from backend.config import LLAMACPP_HOST, LLAMACPP_PORT_E2B, LLAMACPP_PORT_E4B

SYSTEM_PROMPT = """You are an expert Stable Diffusion and Flux prompt engineer.
Your job is to convert casual user descriptions into detailed, high-quality image generation prompts.

Rules:
- Always include lighting, camera, and quality descriptors
- Add relevant style tags (cinematic, photorealistic, etc.)
- Include a strong negative prompt
- Keep the positive prompt under 150 words
- Respond in this exact JSON format:
{
    "positive": "your enhanced positive prompt here",
    "negative": "your negative prompt here"
}
- Return JSON only, no explanation, no markdown."""


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
            {"role": "user", "content": f"Rewrite this into a Flux image generation prompt: {user_prompt}"}
        ],
        "temperature": 0.7,
        "max_tokens": 300
    }

    start_time = time.time()

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()

    elapsed = round(time.time() - start_time, 2)
    result = response.json()
    content = result["choices"][0]["message"]["content"]

    # --- Parse JSON response from LLM ---
    import json
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        # Fallback if model doesn't return clean JSON
        parsed = {
            "positive": content,
            "negative": "blurry, low quality, distorted, bad anatomy, watermark"
        }

    parsed["latency_seconds"] = elapsed
    parsed["model_used"] = model
    return parsed