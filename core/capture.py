import os
from pathlib import Path
from config import BASELINES_DIR

def save_baseline(test_name: str, image_bytes: bytes) -> str:
    """Baseline image save karo"""
    folder = Path(BASELINES_DIR) / test_name
    folder.mkdir(parents=True, exist_ok=True)
    path = str(folder / "baseline.png")
    with open(path, "wb") as f:
        f.write(image_bytes)
    return path

def save_current(test_name: str, image_bytes: bytes) -> str:
    """Current screenshot save karo"""
    folder = Path(BASELINES_DIR) / test_name
    folder.mkdir(parents=True, exist_ok=True)
    path = str(folder / "current.png")
    with open(path, "wb") as f:
        f.write(image_bytes)
    return path

def get_baseline_path(test_name: str) -> str:
    """Baseline path return karo"""
    return str(Path(BASELINES_DIR) / test_name / "baseline.png")

def get_current_path(test_name: str) -> str:
    """Current path return karo"""
    return str(Path(BASELINES_DIR) / test_name / "current.png")

def baseline_exists(test_name: str) -> bool:
    """Check karo baseline exist karta hai ya nahi"""
    return Path(get_baseline_path(test_name)).exists()
