"""UUIDv7 IDs for sortable business identifiers."""
from __future__ import annotations

import secrets
import time
import uuid


def new_id() -> str:
    unix_ms = time.time_ns() // 1_000_000
    if unix_ms >= 1 << 48:
        raise OverflowError("UUIDv7 timestamp overflow")
    rand_a = secrets.randbits(12)
    rand_b = secrets.randbits(62)
    value = (unix_ms << 80) | (0x7 << 76) | (rand_a << 64) | (0b10 << 62) | rand_b
    return str(uuid.UUID(int=value))
