from dataclasses import replace

from app.bot.permissions import is_editorial_user
from app.persistence.migrations import migrate
from app.persistence.repositories import Repository
from app.settings import Settings


def test_editorial_authorization_from_settings(tmp_path):
    db = tmp_path / "test.sqlite3"
    migrate(db)
    repo = Repository(db)
    settings = Settings.from_env()
    settings = replace(settings, database_path=db, editorial_telegram_ids={42})
    assert is_editorial_user(42, settings, repo)
    assert not is_editorial_user(43, settings, repo)
