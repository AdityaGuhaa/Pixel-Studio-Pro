# =============================
# PixelStudio Pro - image_gen.py
# Handles ComfyUI API orchestration
# =============================

import httpx
import json
import uuid
import asyncio
import random
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
    client_id = str(uuid.uuid4())
    seed = random.randint(0, 2**32 - 1)
    workflow = build_workflow(
        positive=positive,
        negative=negative,
        steps=DEFAULT_STEPS,
        cfg=DEFAULT_CFG,
        width=DEFAULT_WIDTH,
        height=DEFAULT_HEIGHT,
        sampler=DEFAULT_SAMPLER,
        scheduler=DEFAULT_SCHEDULER,
        seed=seed
    )

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{COMFYUI_URL}/prompt",
            json={"prompt": workflow, "client_id": client_id}
        )
        response.raise_for_status()
        prompt_id = response.json()["prompt_id"]

    await wait_for_completion(client_id, prompt_id)
    image_filename = await poll_history(prompt_id)

    return {
        "prompt_id": prompt_id,
        "image_filename": image_filename
    }


async def wait_for_completion(client_id: str, prompt_id: str):
    ws_url = f"{COMFYUI_WS_URL}/ws?clientId={client_id}"

    async with websockets.connect(ws_url) as ws:
        while True:
            try:
                message = await asyncio.wait_for(ws.recv(), timeout=120.0)
                data = json.loads(message)
                if data.get("type") == "executing":
                    node = data["data"].get("node")
                    if node is None and data["data"].get("prompt_id") == prompt_id:
                        break
            except asyncio.TimeoutError:
                raise TimeoutError("ComfyUI generation timed out after 120s")


async def poll_history(prompt_id: str, max_retries: int = 20) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(max_retries):
            await asyncio.sleep(5)
            response = await client.get(f"{COMFYUI_URL}/history/{prompt_id}")
            response.raise_for_status()
            history = response.json()

            if prompt_id not in history:
                continue

            outputs = history[prompt_id].get("outputs", {})
            for node_id, node_output in outputs.items():
                if "images" in node_output and node_output["images"]:
                    return node_output["images"][0]["filename"]

    raise TimeoutError(f"Image output not found after {max_retries} attempts")