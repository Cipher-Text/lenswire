from __future__ import annotations

from enum import StrEnum


class EditorialAction(StrEnum):
    SAVE = "SAVE"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
