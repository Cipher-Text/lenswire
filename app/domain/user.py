from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class UserRole(StrEnum):
    EXTERNAL = "EXTERNAL"
    EDITORIAL = "EDITORIAL"


@dataclass(slots=True)
class User:
    chat_id: int
    role: UserRole = UserRole.EXTERNAL
    language: str = "en"
    quiet_start: str | None = None
    quiet_end: str | None = None
    stopped: bool = False
    legacy_interests: str = ""
