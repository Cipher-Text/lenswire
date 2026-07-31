from app.persistence.migrations import migrate
from app.persistence.repositories import Repository
from app.settings import settings


def _repo() -> Repository:
    return Repository(settings.database_path)


def init_db():
    migrate(settings.database_path, settings.source_config_path)


def upsert_user(chat_id):
    _repo().upsert_user(chat_id)


def set_interests(chat_id, interests_str):
    _repo().set_legacy_interests(chat_id, interests_str)


def get_interests(chat_id):
    return _repo().get_legacy_interests(chat_id)


def get_all_users():
    return _repo().get_users_with_legacy_interests()


def was_sent(chat_id, url):
    # Legacy URL-only checks are kept for compatibility with older callers.
    return False


def mark_sent(chat_id, url):
    return None
