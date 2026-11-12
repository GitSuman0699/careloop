"""Tamper-evident event-chain hashing for CaseEvent audit trail."""

from __future__ import annotations

import hashlib
import json


def compute_event_hash(event_data: dict, prev_hash: str) -> str:
    """Return the SHA-256 hex digest for an event in the chain.

    The hash covers a canonical JSON encoding of *event_data* concatenated
    with the previous event's hash, forming a hash chain.
    """
    canonical = json.dumps(event_data, sort_keys=True, separators=(",", ":"))
    payload = f"{canonical}|{prev_hash}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verify_chain(events: list[dict]) -> tuple[bool, str | None]:
    """Walk *events* (ordered by ``seq``) and verify the hash chain.

    Each event dict must contain ``hash``, ``prev_hash``, and the remaining
    keys are the event data.  Returns ``(True, None)`` on success, or
    ``(False, reason)`` on the first broken link.
    """
    for idx, event in enumerate(events):
        stored_hash = event.get("hash", "")
        prev_hash = event.get("prev_hash", "")

        # Build event_data — everything except hash / prev_hash
        event_data = {k: v for k, v in event.items() if k not in ("hash", "prev_hash")}

        expected = compute_event_hash(event_data, prev_hash)
        if expected != stored_hash:
            return (
                False,
                f"Hash mismatch at event index {idx} (seq={event.get('seq')}): "
                f"expected {expected}, got {stored_hash}",
            )

        # For events after the first, prev_hash must equal the preceding
        # event's hash.
        if idx > 0:
            preceding_hash = events[idx - 1].get("hash", "")
            if prev_hash != preceding_hash:
                return (
                    False,
                    f"Chain break at event index {idx}: prev_hash={prev_hash} "
                    f"does not match preceding hash={preceding_hash}",
                )

    return (True, None)
