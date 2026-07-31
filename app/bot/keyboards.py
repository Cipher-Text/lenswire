from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app.domain.topic import Topic


def topic_keyboard(topics: list[Topic], action: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(topic.english_name, callback_data=f"{action}:{topic.key}")]
        for topic in topics
    ]
    return InlineKeyboardMarkup(rows)


def editorial_keyboard(article_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Save", callback_data=f"ed:save:{article_id}"),
                InlineKeyboardButton("Approve", callback_data=f"ed:approve:{article_id}"),
                InlineKeyboardButton("Reject", callback_data=f"ed:reject:{article_id}"),
            ]
        ]
    )
