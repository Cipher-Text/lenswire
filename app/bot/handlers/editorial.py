from __future__ import annotations

import asyncio

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.bot.keyboards import editorial_keyboard
from app.bot.permissions import is_editorial_user
from app.delivery.formatter import format_editorial_message
from app.editorial.service import EditorialService
from app.persistence.repositories import Repository
from app.settings import Settings


async def _require_editor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if update.effective_chat is None or update.effective_message is None:
        return False
    repo: Repository = context.application.bot_data["repo"]
    settings: Settings = context.application.bot_data["settings"]
    if not is_editorial_user(update.effective_chat.id, settings, repo):
        await update.effective_message.reply_text(
            "This command is available to authorized editorial users only."
        )
        return False
    return True


async def review(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_editor(update, context):
        return
    message = update.effective_message
    if message is None:
        return
    service = EditorialService(context.application.bot_data["repo"])
    rows = await asyncio.to_thread(service.pending, 5)
    if not rows:
        await message.reply_text("No pending stories.")
        return
    for row in rows:
        await message.reply_text(
            format_editorial_message(row),
            parse_mode=ParseMode.HTML,
            reply_markup=editorial_keyboard(int(row["id"])),
        )


async def sources(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_editor(update, context):
        return
    message = update.effective_message
    if message is None:
        return
    repo: Repository = context.application.bot_data["repo"]
    rows = await asyncio.to_thread(repo.list_sources, False)
    await message.reply_text(
        "\n".join(f"{s.name} — {s.source_type.value} — {s.credibility_tier.value}" for s in rows)
    )


async def article_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_editor(update, context):
        return
    message = update.effective_message
    if message is None:
        return
    if not context.args or not context.args[0].isdigit():
        await message.reply_text("Usage: /context <article_id>")
        return
    service = EditorialService(context.application.bot_data["repo"])
    row = await asyncio.to_thread(service.detail, int(context.args[0]))
    await message.reply_text(
        format_editorial_message(row) if row else "Article not found.",
        parse_mode=ParseMode.HTML,
    )


async def _action(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> None:
    if not await _require_editor(update, context):
        return
    message = update.effective_message
    chat = update.effective_chat
    if message is None or chat is None:
        return
    if not context.args or not context.args[0].isdigit():
        await message.reply_text(f"Usage: /{action.lower()} <article_id>")
        return
    service = EditorialService(context.application.bot_data["repo"])
    article_id = int(context.args[0])
    if action == "APPROVE":
        await asyncio.to_thread(service.approve, article_id, chat.id)
    elif action == "REJECT":
        await asyncio.to_thread(service.reject, article_id, chat.id)
    else:
        await asyncio.to_thread(service.save, article_id, chat.id)
    await message.reply_text(f"{action.title()} recorded for article {article_id}.")


async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _action(update, context, "APPROVE")


async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _action(update, context, "REJECT")


async def save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _action(update, context, "SAVE")


async def breaking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await review(update, context)


async def angle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await article_detail(update, context)


async def editorial_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    repo: Repository = context.application.bot_data["repo"]
    settings: Settings = context.application.bot_data["settings"]
    user = query.from_user
    chat_id = user.id
    if not is_editorial_user(chat_id, settings, repo):
        await query.edit_message_text(
            "This action is available to authorized editorial users only."
        )
        return
    if query.data is None:
        return
    try:
        _, action, article_id_raw = query.data.split(":", 2)
        article_id = int(article_id_raw)
    except ValueError:
        await query.edit_message_text("Invalid action data.")
        return
    service = EditorialService(repo)
    if action == "approve":
        await asyncio.to_thread(service.approve, article_id, chat_id)
    elif action == "reject":
        await asyncio.to_thread(service.reject, article_id, chat_id)
    else:
        await asyncio.to_thread(service.save, article_id, chat_id)
    await query.edit_message_reply_markup(reply_markup=None)
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"{action.title()} recorded for article {article_id}.",
    )
