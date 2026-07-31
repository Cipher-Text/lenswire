# mypy: disable-error-code="union-attr,arg-type,index"
from __future__ import annotations

import asyncio
import time

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.bot.keyboards import topic_keyboard
from app.bot.messages import WELCOME
from app.delivery.formatter import format_external_message
from app.delivery.service import DeliveryService
from app.ingestion.pipeline import IngestionPipeline
from app.persistence.repositories import Repository
from app.settings import Settings

_last_refresh_by_chat: dict[int, float] = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    repo: Repository = context.application.bot_data["repo"]
    chat_id = update.effective_chat.id
    await asyncio.to_thread(repo.upsert_user, chat_id)
    await update.effective_message.reply_text(WELCOME)


async def set_interests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    repo: Repository = context.application.bot_data["repo"]
    chat_id = update.effective_chat.id
    text = " ".join(context.args)
    if not text:
        await update.effective_message.reply_text("Usage: /setinterests India, diplomacy, trade")
        return
    await asyncio.to_thread(repo.upsert_user, chat_id)
    await asyncio.to_thread(repo.set_legacy_interests, chat_id, text)
    await update.effective_message.reply_text(f"Saved legacy interests: {text}")


async def my_interests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    repo: Repository = context.application.bot_data["repo"]
    chat_id = update.effective_chat.id
    interests = await asyncio.to_thread(repo.get_legacy_interests, chat_id)
    topics = await asyncio.to_thread(repo.user_topics, chat_id)
    lines = []
    if topics:
        lines.append("Topics: " + ", ".join(topic.english_name for topic in topics))
    if interests:
        lines.append("Legacy interests: " + interests)
    await update.effective_message.reply_text(
        "\n".join(lines) if lines else "No subscriptions yet. Use /topics."
    )


async def topics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    repo: Repository = context.application.bot_data["repo"]
    rows = await asyncio.to_thread(repo.list_topics)
    await update.effective_message.reply_text(
        "Choose topics:",
        reply_markup=topic_keyboard(rows, "sub"),
    )


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    repo: Repository = context.application.bot_data["repo"]
    chat_id = update.effective_chat.id
    if not context.args:
        await update.effective_message.reply_text("Usage: /subscribe <topic-key>")
        return
    await asyncio.to_thread(repo.upsert_user, chat_id)
    ok = await asyncio.to_thread(repo.subscribe, chat_id, context.args[0])
    await update.effective_message.reply_text("Subscribed." if ok else "Unknown topic key.")


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    repo: Repository = context.application.bot_data["repo"]
    if not context.args:
        await update.effective_message.reply_text("Usage: /unsubscribe <topic-key>")
        return
    await asyncio.to_thread(repo.unsubscribe, update.effective_chat.id, context.args[0])
    await update.effective_message.reply_text("Unsubscribed.")


async def mysubscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    repo: Repository = context.application.bot_data["repo"]
    rows = await asyncio.to_thread(repo.user_topics, update.effective_chat.id)
    if not rows:
        await update.effective_message.reply_text("No topic subscriptions yet. Use /topics.")
        return
    await update.effective_message.reply_text(
        "\n".join(f"{t.key} — {t.english_name}" for t in rows)
    )


async def latest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    repo: Repository = context.application.bot_data["repo"]
    settings: Settings = context.application.bot_data["settings"]
    delivery = DeliveryService(repo)
    articles = await asyncio.to_thread(
        delivery.latest_for_user,
        update.effective_chat.id,
        settings.max_articles_per_delivery,
        settings.external_delivery_approval_required,
    )
    if not articles:
        await update.effective_message.reply_text("No approved stories for your subscriptions yet.")
        return
    for article in articles:
        await update.effective_message.reply_text(
            format_external_message(article),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=False,
        )


async def news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    chat_id = update.effective_chat.id
    now = time.monotonic()
    if now - _last_refresh_by_chat.get(chat_id, 0) < settings.manual_refresh_cooldown_seconds:
        await update.effective_message.reply_text(
            "Manual refresh is cooling down. Try again shortly."
        )
        return
    _last_refresh_by_chat[chat_id] = now
    pipeline: IngestionPipeline = context.application.bot_data["pipeline"]
    await update.effective_message.reply_text("Checking latest sources...")
    count = await pipeline.run(extract_content=False)
    await update.effective_message.reply_text(
        f"Checked sources and stored {count} discovered articles."
    )


async def language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    repo: Repository = context.application.bot_data["repo"]
    lang = context.args[0].lower() if context.args else "en"
    if lang not in {"en", "bn"}:
        await update.effective_message.reply_text("Use /language en or /language bn")
        return
    await asyncio.to_thread(repo.set_language, update.effective_chat.id, lang)
    await update.effective_message.reply_text(f"Language set to {lang}.")


async def quiettime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    repo: Repository = context.application.bot_data["repo"]
    if len(context.args) != 2:
        await update.effective_message.reply_text("Usage: /quiettime 22:00 07:00")
        return
    await asyncio.to_thread(
        repo.set_quiet_time, update.effective_chat.id, context.args[0], context.args[1]
    )
    await update.effective_message.reply_text("Quiet time updated.")


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    repo: Repository = context.application.bot_data["repo"]
    await asyncio.to_thread(repo.set_stopped, update.effective_chat.id, True)
    await update.effective_message.reply_text("Delivery stopped. Use /start to resume.")


async def deleteaccount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    repo: Repository = context.application.bot_data["repo"]
    await asyncio.to_thread(repo.delete_user, update.effective_chat.id)
    await update.effective_message.reply_text("Your Lenswire subscription data has been deleted.")


async def topic_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    repo: Repository = context.application.bot_data["repo"]
    action, topic_key = query.data.split(":", 1)
    if action == "sub":
        await asyncio.to_thread(repo.upsert_user, query.message.chat_id)
        ok = await asyncio.to_thread(repo.subscribe, query.message.chat_id, topic_key)
        await query.edit_message_text("Subscribed." if ok else "Unknown topic.")
