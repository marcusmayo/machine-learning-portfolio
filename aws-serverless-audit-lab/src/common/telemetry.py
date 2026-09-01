from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any


def emit(event_name: str, **fields: Any) -> None:
    """Emit structured metadata only; callers must not pass templates or upload URLs."""
    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event": event_name,
        **fields,
    }
    print(json.dumps(payload, separators=(",", ":"), sort_keys=True, default=str))
