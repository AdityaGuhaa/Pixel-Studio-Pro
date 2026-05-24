# =============================
# PixelStudio Pro - comfyui_workflow.py
# Builds ComfyUI workflow JSON programmatically
# =============================

def build_workflow(
    positive: str,
    negative: str,
    steps: int,
    cfg: float,
    width: int,
    height: int,
    sampler: str,
    scheduler: str
) -> dict:
    """
    Builds a Flux.1 Schnell compatible ComfyUI workflow JSON.
    Node structure mirrors the standard Flux GGUF workflow.
    """

    workflow = {
        "1": {
            "class_type": "UnetLoaderGGUF",
            "inputs": {
                "unet_name": "flux1-schnell-q4_k_m.gguf"
            }
        },
        "2": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name1": "t5xxl_fp16.safetensors",
                "clip_name2": "clip_l.safetensors",
                "type": "flux"
            }
        },
        "3": {
            "class_type": "VAELoader",
            "inputs": {
                "vae_name": "ae.safetensors"
            }
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": positive,
                "clip": ["2", 0]
            }
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": negative,
                "clip": ["2", 0]
            }
        },
        "6": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": width,
                "height": height,
                "batch_size": 1
            }
        },
        "7": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["4", 0],
                "negative": ["5", 0],
                "latent_image": ["6", 0],
                "seed": 0,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": sampler,
                "scheduler": scheduler,
                "denoise": 1.0
            }
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["7", 0],
                "vae": ["3", 0]
            }
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["8", 0],
                "filename_prefix": "pixelstudio_pro"
            }
        }
    }

    return workflow