from __future__ import annotations

import re
from typing import Iterable, Set

from movement_tags import MOVEMENT_KEYWORDS, MOVEMENT_BUCKETS


def normalize_text(text: str) -> str:
    if text is None:
        return ""
    return str(text).strip().lower()


def tag_movements(text: str) -> Set[str]:
    text = normalize_text(text)
    tags = set()
    for movement, keywords in MOVEMENT_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                tags.add(movement)
                break
    return tags


def tag_buckets(movements: Iterable[str]) -> Set[str]:
    movement_set = set(movements)
    buckets = set()
    for bucket, members in MOVEMENT_BUCKETS.items():
        if movement_set.intersection(members):
            buckets.add(bucket)
    return buckets


def coverage_score(training_movements: set[str], event_movements: set[str]) -> float:
    if not event_movements:
        return 0.0
    return len(training_movements.intersection(event_movements)) / len(event_movements)
