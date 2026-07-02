from __future__ import annotations

from typing import Iterable


DEFAULT_QUERY = "is:unread older_than:6m"


def chunks(values: list[str], size: int) -> Iterable[list[str]]:
    """Yield list slices no larger than size."""
    for index in range(0, len(values), size):
        yield values[index : index + size]
