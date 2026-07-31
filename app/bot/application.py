from __future__ import annotations

import logging

from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from app.bot.handlers import editorial, public
from app.ingestion.pipeline import IngestionPipeline
from app.matching.embeddings import cached_provider
from app.persistence.migrations import migrate
from app.persistence.repositories import Repository
from app.settings import Settings

logger = logging.getLogger(__name__)


async def scheduled_ingestion(context: ContextTypes.DEFAULT_TYPE) -> None:
    pipeline: IngestionPipeline = context.application.bot_data["pipeline"]
    try:
        await pipeline.run()
    except Exception:
        logger.exception("scheduled ingestion failed")


def build_application(settings: Settings) -> Application:
    settings.validate_for_bot()
    migrate(settings.database_path, settings.source_config_path)
    repo = Repository(settings.database_path)
    embedding_provider = cached_provider(settings.embedding_model_name)
    pipeline = IngestionPipeline(settings, repo, embedding_provider)

    app = Application.builder().token(settings.telegram_bot_token).build()
    app.bot_data["settings"] = settings
    app.bot_data["repo"] = repo
    app.bot_data["pipeline"] = pipeline

    app.add_handler(CommandHandler("start", public.start))
    app.add_handler(CommandHandler("setinterests", public.set_interests))
    app.add_handler(CommandHandler("myinterests", public.my_interests))
    app.add_handler(CommandHandler("news", public.news))
    app.add_handler(CommandHandler("topics", public.topics))
    app.add_handler(CommandHandler("subscribe", public.subscribe))
    app.add_handler(CommandHandler("unsubscribe", public.unsubscribe))
    app.add_handler(CommandHandler("mysubscriptions", public.mysubscriptions))
    app.add_handler(CommandHandler("latest", public.latest))
    app.add_handler(CommandHandler("digest", public.latest))
    app.add_handler(CommandHandler("language", public.language))
    app.add_handler(CommandHandler("quiettime", public.quiettime))
    app.add_handler(CommandHandler("stop", public.stop))
    app.add_handler(CommandHandler("deleteaccount", public.deleteaccount))

    app.add_handler(CommandHandler("review", editorial.review))
    app.add_handler(CommandHandler("sources", editorial.sources))
    app.add_handler(CommandHandler("context", editorial.article_detail))
    app.add_handler(CommandHandler("angle", editorial.angle))
    app.add_handler(CommandHandler("save", editorial.save))
    app.add_handler(CommandHandler("approve", editorial.approve))
    app.add_handler(CommandHandler("reject", editorial.reject))
    app.add_handler(CommandHandler("breaking", editorial.breaking))

    app.add_handler(CallbackQueryHandler(public.topic_callback, pattern=r"^sub:"))
    app.add_handler(CallbackQueryHandler(editorial.editorial_callback, pattern=r"^ed:"))

    if app.job_queue is None:
        raise RuntimeError("python-telegram-bot job queue extra is required")
    app.job_queue.run_repeating(
        scheduled_ingestion,
        interval=settings.ingestion_interval_minutes * 60,
        first=30,
        name="lenswire-ingestion",
    )
    return app
