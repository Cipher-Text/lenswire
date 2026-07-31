from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.domain.article import (
    Article,
    ArticleStatus,
    ArticleSummary,
    VerificationStatus,
)
from app.domain.source import CredibilityTier, Source, SourceType
from app.domain.topic import Topic
from app.domain.user import User, UserRole
from app.persistence.sqlite import sqlite_connection


def _dt(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).isoformat()


def stable_content_hash(text: str) -> str:
    normalized = " ".join(text.lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest() if normalized else ""


@dataclass(slots=True)
class Repository:
    database_path: Path | str

    def upsert_user(self, chat_id: int, role: UserRole = UserRole.EXTERNAL) -> None:
        with sqlite_connection(self.database_path) as conn:
            conn.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (chat_id,))
            conn.execute(
                """
                INSERT INTO lenswire_users (chat_id, role)
                VALUES (?, ?)
                ON CONFLICT(chat_id) DO UPDATE SET
                    role = CASE
                        WHEN lenswire_users.role = 'EDITORIAL' THEN lenswire_users.role
                        ELSE excluded.role
                    END,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (chat_id, role.value),
            )

    def set_legacy_interests(self, chat_id: int, interests: str) -> None:
        with sqlite_connection(self.database_path) as conn:
            conn.execute(
                """
                INSERT INTO users (chat_id, interests) VALUES (?, ?)
                ON CONFLICT(chat_id) DO UPDATE SET interests=excluded.interests
                """,
                (chat_id, interests),
            )
            conn.execute(
                """
                INSERT INTO lenswire_users (chat_id, legacy_interests)
                VALUES (?, ?)
                ON CONFLICT(chat_id) DO UPDATE SET legacy_interests=excluded.legacy_interests,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (chat_id, interests),
            )

    def get_legacy_interests(self, chat_id: int) -> str:
        with sqlite_connection(self.database_path) as conn:
            row = conn.execute(
                "SELECT legacy_interests FROM lenswire_users WHERE chat_id=?", (chat_id,)
            ).fetchone()
            if row:
                return str(row["legacy_interests"])
            old = conn.execute("SELECT interests FROM users WHERE chat_id=?", (chat_id,)).fetchone()
            return str(old["interests"]) if old else ""

    def get_users_with_legacy_interests(self) -> list[tuple[int, str]]:
        with sqlite_connection(self.database_path) as conn:
            return [
                (int(row["chat_id"]), str(row["legacy_interests"]))
                for row in conn.execute(
                    """
                    SELECT chat_id, legacy_interests
                    FROM lenswire_users
                    WHERE legacy_interests != '' AND stopped = 0
                    """
                ).fetchall()
            ]

    def get_user(self, chat_id: int) -> User | None:
        with sqlite_connection(self.database_path) as conn:
            row = conn.execute(
                "SELECT * FROM lenswire_users WHERE chat_id=?", (chat_id,)
            ).fetchone()
        if not row:
            return None
        return User(
            chat_id=int(row["chat_id"]),
            role=UserRole(str(row["role"])),
            language=str(row["language"]),
            quiet_start=row["quiet_start"],
            quiet_end=row["quiet_end"],
            stopped=bool(row["stopped"]),
            legacy_interests=str(row["legacy_interests"]),
        )

    def delete_user(self, chat_id: int) -> None:
        with sqlite_connection(self.database_path) as conn:
            conn.execute("DELETE FROM delivery_history WHERE chat_id=?", (chat_id,))
            conn.execute("DELETE FROM user_topic_subscriptions WHERE chat_id=?", (chat_id,))
            conn.execute("DELETE FROM lenswire_users WHERE chat_id=?", (chat_id,))
            conn.execute("DELETE FROM sent_articles WHERE chat_id=?", (chat_id,))
            conn.execute("DELETE FROM users WHERE chat_id=?", (chat_id,))

    def set_language(self, chat_id: int, language: str) -> None:
        with sqlite_connection(self.database_path) as conn:
            conn.execute(
                """
                UPDATE lenswire_users
                SET language=?, updated_at=CURRENT_TIMESTAMP
                WHERE chat_id=?
                """,
                (language, chat_id),
            )

    def set_stopped(self, chat_id: int, stopped: bool) -> None:
        with sqlite_connection(self.database_path) as conn:
            conn.execute(
                "UPDATE lenswire_users SET stopped=?, updated_at=CURRENT_TIMESTAMP WHERE chat_id=?",
                (1 if stopped else 0, chat_id),
            )

    def set_quiet_time(self, chat_id: int, start: str | None, end: str | None) -> None:
        with sqlite_connection(self.database_path) as conn:
            conn.execute(
                """
                UPDATE lenswire_users
                SET quiet_start=?, quiet_end=?, updated_at=CURRENT_TIMESTAMP
                WHERE chat_id=?
                """,
                (start, end, chat_id),
            )

    def list_topics(self, enabled_only: bool = True) -> list[Topic]:
        query = "SELECT * FROM topics"
        if enabled_only:
            query += " WHERE enabled = 1"
        query += " ORDER BY english_name"
        with sqlite_connection(self.database_path) as conn:
            rows = conn.execute(query).fetchall()
        return [
            Topic(
                key=str(row["key"]),
                english_name=str(row["english_name"]),
                bangla_name=str(row["bangla_name"]),
                description=row["description"],
                enabled=bool(row["enabled"]),
            )
            for row in rows
        ]

    def subscribe(self, chat_id: int, topic_key: str) -> bool:
        with sqlite_connection(self.database_path) as conn:
            topic = conn.execute(
                "SELECT 1 FROM topics WHERE key=? AND enabled=1", (topic_key,)
            ).fetchone()
            if not topic:
                return False
            conn.execute(
                "INSERT OR IGNORE INTO user_topic_subscriptions (chat_id, topic_key) VALUES (?, ?)",
                (chat_id, topic_key),
            )
            return True

    def unsubscribe(self, chat_id: int, topic_key: str) -> None:
        with sqlite_connection(self.database_path) as conn:
            conn.execute(
                "DELETE FROM user_topic_subscriptions WHERE chat_id=? AND topic_key=?",
                (chat_id, topic_key),
            )

    def user_topics(self, chat_id: int) -> list[Topic]:
        with sqlite_connection(self.database_path) as conn:
            rows = conn.execute(
                """
                SELECT t.* FROM topics t
                JOIN user_topic_subscriptions s ON s.topic_key = t.key
                WHERE s.chat_id=? AND t.enabled=1
                ORDER BY t.english_name
                """,
                (chat_id,),
            ).fetchall()
        return [
            Topic(
                str(r["key"]),
                str(r["english_name"]),
                str(r["bangla_name"]),
                r["description"],
                bool(r["enabled"]),
            )
            for r in rows
        ]

    def list_sources(self, enabled_only: bool = True) -> list[Source]:
        query = "SELECT * FROM sources"
        if enabled_only:
            query += " WHERE enabled = 1"
        query += " ORDER BY credibility_tier, name"
        with sqlite_connection(self.database_path) as conn:
            rows = conn.execute(query).fetchall()
        return [
            Source(
                id=int(row["id"]),
                name=str(row["name"]),
                domain=str(row["domain"]),
                source_type=SourceType(str(row["source_type"])),
                credibility_tier=CredibilityTier(str(row["credibility_tier"])),
                language=str(row["language"]),
                country_or_region=str(row["country_or_region"]),
                rss_url=row["rss_url"],
                enabled=bool(row["enabled"]),
            )
            for row in rows
        ]

    def find_source_by_domain(self, domain: str) -> Source | None:
        domain = domain.lower().removeprefix("www.")
        with sqlite_connection(self.database_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM sources
                WHERE ? = domain OR ? LIKE '%.' || domain
                ORDER BY length(domain) DESC
                LIMIT 1
                """,
                (domain, domain),
            ).fetchone()
        if not row:
            return None
        return Source(
            id=int(row["id"]),
            name=str(row["name"]),
            domain=str(row["domain"]),
            source_type=SourceType(str(row["source_type"])),
            credibility_tier=CredibilityTier(str(row["credibility_tier"])),
            language=str(row["language"]),
            country_or_region=str(row["country_or_region"]),
            rss_url=row["rss_url"],
            enabled=bool(row["enabled"]),
        )

    def upsert_article(self, article: Article) -> int:
        with sqlite_connection(self.database_path) as conn:
            conn.execute(
                """
                INSERT INTO articles (
                    original_headline, original_url, canonical_url, source_id, source_name,
                    discovery_source, author, publication_time, fetched_time, language,
                    raw_description, extracted_content, normalized_title, content_hash,
                    status, extraction_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(canonical_url) DO UPDATE SET
                    source_id=COALESCE(excluded.source_id, articles.source_id),
                    source_name=COALESCE(NULLIF(excluded.source_name, ''), articles.source_name),
                    extracted_content=COALESCE(
                        NULLIF(excluded.extracted_content, ''),
                        articles.extracted_content
                    ),
                    content_hash=COALESCE(NULLIF(excluded.content_hash, ''), articles.content_hash),
                    extraction_status=excluded.extraction_status
                """,
                (
                    article.original_headline,
                    article.original_url,
                    article.canonical_url,
                    article.source_id,
                    article.source_name,
                    article.discovery_source,
                    article.author,
                    _dt(article.publication_time),
                    _dt(article.fetched_time),
                    article.language,
                    article.raw_description,
                    article.extracted_content,
                    article.normalized_title,
                    article.content_hash,
                    article.status.value,
                    article.extraction_status.value,
                ),
            )
            row = conn.execute(
                "SELECT id FROM articles WHERE canonical_url=?", (article.canonical_url,)
            ).fetchone()
            return int(row["id"])

    def set_article_topics(
        self, article_id: int, topic_scores: Iterable[tuple[str, float]]
    ) -> None:
        with sqlite_connection(self.database_path) as conn:
            conn.execute("DELETE FROM article_topics WHERE article_id=?", (article_id,))
            conn.executemany(
                """
                INSERT OR REPLACE INTO article_topics (article_id, topic_key, score)
                VALUES (?, ?, ?)
                """,
                [(article_id, key, score) for key, score in topic_scores],
            )

    def save_summary(self, article_id: int, summary: ArticleSummary) -> None:
        with sqlite_connection(self.database_path) as conn:
            conn.execute(
                """
                INSERT INTO summaries (
                    article_id, summary, why_it_matters, editorial_angle,
                    verification_status, language, provider, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(article_id) DO UPDATE SET
                    summary=excluded.summary,
                    why_it_matters=excluded.why_it_matters,
                    editorial_angle=excluded.editorial_angle,
                    verification_status=excluded.verification_status,
                    language=excluded.language,
                    provider=excluded.provider,
                    status=excluded.status
                """,
                (
                    article_id,
                    summary.summary,
                    summary.why_it_matters,
                    summary.editorial_angle,
                    summary.verification_status.value,
                    summary.language,
                    summary.provider,
                    summary.status,
                ),
            )

    def review(
        self, article_id: int, reviewer_chat_id: int, action: str, note: str | None = None
    ) -> None:
        status = (
            ArticleStatus.APPROVED
            if action == "APPROVE"
            else ArticleStatus.REJECTED
            if action == "REJECT"
            else ArticleStatus.REVIEW_PENDING
        )
        verification = (
            VerificationStatus.EDITOR_APPROVED
            if action == "APPROVE"
            else VerificationStatus.REJECTED
            if action == "REJECT"
            else None
        )
        with sqlite_connection(self.database_path) as conn:
            conn.execute(
                """
                INSERT INTO editorial_reviews (article_id, reviewer_chat_id, action, note)
                VALUES (?, ?, ?, ?)
                """,
                (article_id, reviewer_chat_id, action, note),
            )
            conn.execute("UPDATE articles SET status=? WHERE id=?", (status.value, article_id))
            if verification is not None:
                conn.execute(
                    "UPDATE summaries SET verification_status=? WHERE article_id=?",
                    (verification.value, article_id),
                )

    def list_pending_articles(self, limit: int = 10) -> list[dict]:
        with sqlite_connection(self.database_path) as conn:
            rows = conn.execute(
                """
                SELECT a.*, s.summary, s.why_it_matters, s.editorial_angle, s.verification_status
                FROM articles a
                LEFT JOIN summaries s ON s.article_id = a.id
                WHERE a.status IN ('NEW', 'REVIEW_PENDING')
                ORDER BY COALESCE(a.publication_time, a.fetched_time) DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_article_detail(self, article_id: int) -> dict | None:
        with sqlite_connection(self.database_path) as conn:
            row = conn.execute(
                """
                SELECT a.*, s.summary, s.why_it_matters, s.editorial_angle, s.verification_status,
                       GROUP_CONCAT(t.english_name, ' · ') AS topics
                FROM articles a
                LEFT JOIN summaries s ON s.article_id = a.id
                LEFT JOIN article_topics at ON at.article_id = a.id
                LEFT JOIN topics t ON t.key = at.topic_key
                WHERE a.id=?
                GROUP BY a.id
                """,
                (article_id,),
            ).fetchone()
        return dict(row) if row else None

    def latest_for_topics(
        self, topic_keys: list[str], limit: int, approved_only: bool
    ) -> list[dict]:
        if not topic_keys:
            return []
        placeholders = ",".join("?" for _ in topic_keys)
        status_clause = "AND a.status IN ('APPROVED', 'PUBLISHED')" if approved_only else ""
        with sqlite_connection(self.database_path) as conn:
            rows = conn.execute(
                f"""
                SELECT a.*, s.summary, s.why_it_matters, s.editorial_angle, s.verification_status,
                       GROUP_CONCAT(DISTINCT t.english_name) AS topics
                FROM articles a
                JOIN article_topics at ON at.article_id = a.id
                JOIN topics t ON t.key = at.topic_key
                LEFT JOIN summaries s ON s.article_id = a.id
                WHERE at.topic_key IN ({placeholders}) {status_clause}
                GROUP BY a.id
                ORDER BY COALESCE(a.publication_time, a.fetched_time) DESC
                LIMIT ?
                """,
                (*topic_keys, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def was_delivered(self, chat_id: int, article_id: int) -> bool:
        with sqlite_connection(self.database_path) as conn:
            row = conn.execute(
                "SELECT 1 FROM delivery_history WHERE chat_id=? AND article_id=?",
                (chat_id, article_id),
            ).fetchone()
            return row is not None

    def record_delivery(
        self, chat_id: int, article_id: int, status: str = "SENT", error: str | None = None
    ) -> None:
        with sqlite_connection(self.database_path) as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO delivery_history (chat_id, article_id, status, error)
                VALUES (?, ?, ?, ?)
                """,
                (chat_id, article_id, status, error),
            )
            article = conn.execute(
                "SELECT original_url FROM articles WHERE id=?", (article_id,)
            ).fetchone()
            if article:
                conn.execute(
                    "INSERT OR IGNORE INTO sent_articles (chat_id, article_url) VALUES (?, ?)",
                    (chat_id, article["original_url"]),
                )
