from __future__ import annotations

from app.persistence.repositories import Repository


class DeliveryService:
    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    def latest_for_user(self, chat_id: int, limit: int, approved_only: bool = True) -> list[dict]:
        topics = self.repo.user_topics(chat_id)
        return self.repo.latest_for_topics([topic.key for topic in topics], limit, approved_only)

    def record_sent(self, chat_id: int, article_id: int) -> None:
        self.repo.record_delivery(chat_id, article_id)
