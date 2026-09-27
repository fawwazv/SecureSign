"""Pagination ?page=1&limit=20 (prd.md §19)."""

from __future__ import annotations


def parse_pagination(page: int = 1, limit: int = 20) -> tuple[int, int]:
    page = max(page, 1)
    limit = min(max(limit, 1), 100)
    return page, limit
