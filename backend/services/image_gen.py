# =============================
# PixelStudio Pro - image_gen.py
# Handles ComfyUI API orchestration
# =============================

import httpx
import json
import uuid
import asyncio
import websockets
from backend.config import (
    COMFYUI_URL,
    COMFYUI_WS_URL,
    DEFAULT_STEPS,
    DEFAULT_CFG,
    DEFAULT_WIDTH,
    DEFAULT_HEIGHT,
    DEFAULT_SAMPLER,
    DEFAULT_SCHEDULER
)
from backend.utils.comfyui_workflow import build_workflow


async def generate_image(positive: str, negative: str) -> dict:
    """
    Submits a generation job to ComfyUI and waits for completion.
    Returns image filename and generation metadata.
    """

    client_id = str(uuid.uuid4())
    workflow = build_workflow(
        positive=positive,
        negative=negative,
        steps=DEFAULT_STEPS,
        cfg=DEFAULT_CFG,
        width=DEFAULT_WIDTH,
        height=DEFAULT_HEIGHT,
        sampler=DEFAULT_SAMPLER,
        scheduler=DEFAULT_SCHEDULER
    )

    # --- Submit job to ComfyUI queue ---
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{COMFYUI_URL}/prompt",
            json={"prompt": workflow, "client_id": client_id}
        )
        response.raise_for_status()
        prompt_id = response.json()["prompt_id"]

    # --- Wait for job completion via WebSocket ---
    image_filename = await wait_for_completion(client_id, prompt_id)

    return {
        "prompt_id": prompt_id,
        "image_filename": image_filename
    }


async def wait_for_completion(client_id: str, prompt_id: str) -> str:
    """
    Connects to ComfyUI WebSocket and waits for the job to finish.
    Returns the output image filename.
    """
    ws_url = f"{COMFYUI_WS_URL}/ws?clientId={client_id}"

    async with websockets.connect(ws_url) as ws:
        while True:
            message = await ws.recv()
            data = json.loads(message)

            if data.get("type") == "executing":
                node = data["data"].get("node")
                if node is None and data["data"].get("prompt_id") == prompt_id:
                    # Job complete
                    break

    # --- Fetch output image filename from ComfyUI history ---
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{COMFYUI_URL}/history/{prompt_id}")
        response.raise_for_status()
        history = response.json()

    outputs = history[prompt_id]["outputs"]
    for node_id, node_output in outputs.items():
        if "images" in node_output:
            return node_output["images"][0]["filename"]

    return "unknown.png"