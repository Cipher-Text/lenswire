from __future__ import annotations

from app.editorial.workflow import EditorialAction
from app.persistence.repositories import Repository


class EditorialService:
    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    def pending(self, limit: int = 5) -> list[dict]:
        return self.repo.list_pending_articles(limit)

    def detail(self, article_id: int) -> dict | None:
        return self.repo.get_article_detail(article_id)

    def save(self, article_id: int, reviewer_chat_id: int) -> None:
        self.repo.review(article_id, reviewer_chat_id, EditorialAction.SAVE.value)

    def approve(self, article_id: int, reviewer_chat_id: int) -> None:
        self.repo.review(article_id, reviewer_chat_id, EditorialAction.APPROVE.value)

    def reject(self, article_id: int, reviewer_chat_id: int) -> None:
        self.repo.review(article_id, reviewer_chat_id, EditorialAction.REJECT.value)
