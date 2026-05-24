# =============================
# PixelStudio Pro - benchmark.py
# Tracks and compares E2B vs E4B performance metrics
# =============================

import time
from typing import Optional


def create_benchmark_entry(
    user_prompt: str,
    model: str,
    rewritten_prompt: dict,
    image_filename: str,
    image_gen_time: float
) -> dict:
    """
    Creates a structured benchmark entry for a single generation run.
    """
    return {
        "model_used": model,
        "user_prompt": user_prompt,
        "positive_prompt": rewritten_prompt.get("positive", ""),
        "negative_prompt": rewritten_prompt.get("negative", ""),
        "rewrite_latency_seconds": rewritten_prompt.get("latency_seconds", 0.0),
        "image_gen_latency_seconds": round(image_gen_time, 2),
        "total_latency_seconds": round(
            rewritten_prompt.get("latency_seconds", 0.0) + image_gen_time, 2
        ),
        "image_filename": image_filename
    }


def compare_benchmarks(e2b_entry: dict, e4b_entry: dict) -> dict:
    """
    Takes two benchmark entries (E2B and E4B) and returns a comparison summary.
    """
    return {
        "e2b": e2b_entry,
        "e4b": e4b_entry,
        "comparison": {
            "faster_rewrite": (
                "e2b" if e2b_entry["rewrite_latency_seconds"] < e4b_entry["rewrite_latency_seconds"]
                else "e4b"
            ),
            "faster_total": (
                "e2b" if e2b_entry["total_latency_seconds"] < e4b_entry["total_latency_seconds"]
                else "e4b"
            ),
            "rewrite_diff_seconds": round(
                abs(
                    e2b_entry["rewrite_latency_seconds"] -
                    e4b_entry["rewrite_latency_seconds"]
                ), 2
            ),
            "total_diff_seconds": round(
                abs(
                    e2b_entry["total_latency_seconds"] -
                    e4b_entry["total_latency_seconds"]
                ), 2
            )
        }
    }