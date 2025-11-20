"""Utility functions for AI service operations."""

import base64
from pathlib import Path


def encode_image_to_base64(image_path: str) -> str:
    """
    Encode an image file to base64 data URL format.

    Args:
        image_path: Path to the image file

    Returns:
        Data URL string in format: data:image/{mime};base64,{encoded}

    Raises:
        FileNotFoundError: If image file doesn't exist
        ValueError: If file extension is not supported
    """
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    # Detect MIME type from file extension
    extension = path.suffix.lower()
    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }

    mime_type = mime_types.get(extension)
    if not mime_type:
        raise ValueError(
            f"Unsupported image format: {extension}. "
            f"Supported formats: {', '.join(mime_types.keys())}"
        )

    # Read and encode image
    with open(path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"
