from __future__ import annotations

from app.domain.user import UserRole
from app.persistence.repositories import Repository
from app.settings import Settings


def is_editorial_user(chat_id: int, settings: Settings, repo: Repository) -> bool:
    if chat_id in settings.editorial_telegram_ids:
        return True
    user = repo.get_user(chat_id)
    return bool(user and user.role == UserRole.EDITORIAL)
