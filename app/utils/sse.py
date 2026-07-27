import json
from typing import Any

def sse_event(
    *,
    event: str,
    data: dict[str, Any],
) -> str:
    """Generate a Server-Sent Event (SSE) message."""
    return (
        f"event: {event}\n"
        f"data: {json.dumps(data, default=str, ensure_ascii=False)}\n\n"
    )