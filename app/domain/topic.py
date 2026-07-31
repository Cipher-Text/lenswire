from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Topic:
    key: str
    english_name: str
    bangla_name: str
    description: str | None = None
    enabled: bool = True
