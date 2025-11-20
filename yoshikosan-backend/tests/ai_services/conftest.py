"""Test fixtures for AI services integration tests."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def lego_image_path() -> str:
    """Return path to LEGO test image."""
    # Path relative to project root
    image_path = Path(__file__).parent.parent.parent.parent / "data" / "photo" / "lego" / "LEGO_01_OK.JPEG"
    return str(image_path.absolute())


@pytest.fixture
def lego_sop_text() -> str:
    """Return LEGO SOP text content."""
    # Path relative to project root
    sop_path = Path(__file__).parent.parent.parent.parent / "data" / "SOP" / "lego" / "lego_sop.txt"

    if not sop_path.exists():
        # Return fallback text if file doesn't exist
        return "Please verify the assembly follows the standard operating procedure."

    with open(sop_path, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def results_dir() -> Path:
    """Create and return timestamped results directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_path = Path(__file__).parent / "results" / timestamp
    results_path.mkdir(parents=True, exist_ok=True)
    return results_path


def save_test_result(
    results_dir: Path,
    test_name: str,
    request_data: dict[str, Any] | None,
    response_data: Any,
    status: str,
    duration_ms: int,
) -> None:
    """
    Save test execution results to structured files.

    Args:
        results_dir: Directory to save results
        test_name: Name of the test
        request_data: Request payload (will be saved as JSON)
        response_data: Response data (str, dict, or bytes)
        status: Test status (passed/failed/skipped)
        duration_ms: Test duration in milliseconds
    """
    # Save metadata
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "test_name": test_name,
        "status": status,
        "duration_ms": duration_ms,
    }

    with open(results_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    # Save request if provided
    if request_data:
        # Redact API keys
        safe_request = request_data.copy()
        if "headers" in safe_request:
            headers = safe_request["headers"].copy()
            for key in headers:
                if "auth" in key.lower() or "key" in key.lower():
                    headers[key] = "***REDACTED***"
            safe_request["headers"] = headers

        request_file = results_dir / f"{test_name}_request.json"
        with open(request_file, "w") as f:
            json.dump(safe_request, f, indent=2)

    # Save response
    if isinstance(response_data, dict):
        response_file = results_dir / f"{test_name}_response.json"
        with open(response_file, "w") as f:
            json.dump(response_data, f, indent=2)
    elif isinstance(response_data, str):
        response_file = results_dir / f"{test_name}_response.txt"
        with open(response_file, "w") as f:
            f.write(response_data)
    elif isinstance(response_data, bytes):
        # Binary data (e.g., audio)
        response_file = results_dir / f"{test_name}_response.mp3"
        with open(response_file, "wb") as f:
            f.write(response_data)
