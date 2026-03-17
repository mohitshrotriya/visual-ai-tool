from PIL import Image, ImageChops, ImageDraw
import numpy as np

def compare_images(baseline_path: str, current_path: str):
    """
    Do images compare karo aur diff nikalo
    Returns: diff_percentage, diff_image, changed_regions
    """
    baseline = Image.open(baseline_path).convert("RGB")
    current = Image.open(current_path).convert("RGB")

    # Same size karo dono ko
    if baseline.size != current.size:
        current = current.resize(baseline.size)

    # Pixel difference nikalo
    diff = ImageChops.difference(baseline, current)
    diff_array = np.array(diff)

    # Kitne pixels change hue
    changed_pixels = np.any(diff_array > 10, axis=2).sum()
    total_pixels = diff_array.shape[0] * diff_array.shape[1]
    diff_percentage = (changed_pixels / total_pixels) * 100

    # Diff image banao - red highlight ke saath
    diff_highlighted = current.copy()
    draw = ImageDraw.Draw(diff_highlighted)
    diff_mask = np.any(diff_array > 10, axis=2)

    # Changed regions ko red se highlight karo
    highlight = Image.new("RGB", current.size, (0, 0, 0))
    highlight_array = np.array(highlight)
    highlight_array[diff_mask] = [255, 0, 0]
    highlight_img = Image.fromarray(highlight_array.astype(np.uint8))

    # Blend karo original ke saath
    diff_highlighted = Image.blend(
        diff_highlighted.convert("RGB"),
        highlight_img.convert("RGB"),
        alpha=0.5
    )

    return {
        "diff_percentage": round(diff_percentage, 2),
        "diff_image": diff_highlighted,
        "changed_pixels": int(changed_pixels),
        "total_pixels": int(total_pixels),
        "same_size": baseline.size == current.size
    }
