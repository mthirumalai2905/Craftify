from __future__ import annotations

import itertools
import random

_ticket_counter = itertools.count(1024)


def infer_priority(message: str) -> str:
    text = message.lower()
    if any(word in text for word in ("low priority", "no rush", "whenever", "not urgent")):
        return "low"
    if any(
        word in text
        for word in (
            "urgent",
            "urgently",
            "blocking",
            "blocked",
            "can't work",
            "cannot work",
            "cant work",
            "asap",
            "production down",
        )
    ):
        return "high"
    return "medium"


def create_support_ticket(summary: str, priority: str = "medium") -> dict:
    suffix = next(_ticket_counter) + random.randint(0, 7)
    ticket_id = f"TKT-{suffix}"
    return {"ticket_id": ticket_id, "status": "created"}
