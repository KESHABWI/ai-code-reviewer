"""Utilities for working with ordered collections."""

from __future__ import annotations


def deduplicate(items: list[str]) -> list[str]:
    """Return items with duplicates removed, preserving first-seen order."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def chunk(items: list[str], size: int) -> list[list[str]]:
    """Split items into consecutive chunks of at most `size` elements."""
    if size <= 0:
        raise ValueError("size must be a positive integer")
    return [items[i : i + size] for i in range(0, len(items), size)]
