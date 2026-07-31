import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from config import TELEGRAM_BOT_TOKEN, CHECK_INTERVAL_MINUTES, MAX_ARTICLES_PER_CYCLE
import db
from news_fetcher import fetch_all_articles
from matcher import match_articles

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.upsert_user(update.effective_chat.id)
    await update.message.reply_text(
        "Welcome! I'll send you news matching your interests.\n\n"
        "Set your interests with, e.g.:\n"
        "/setinterests AI, climate change, football\n\n"
        "Check them anytime with /myinterests\n"
        "Trigger a manual check right now with /news"
    )


async def set_interests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text(
            "Usage: /setinterests AI, climate change, football"
        )
        return
    db.upsert_user(chat_id)
    db.set_interests(chat_id, text)
    await update.message.reply_text(f"Got it. Your interests: {text}")


async def my_interests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    interests = db.get_interests(chat_id)
    if interests:
        await update.message.reply_text(f"Your interests: {interests}")
    else:
        await update.message.reply_text(
            "You haven't set any interests yet. Use /setinterests"
        )


async def send_matches_to_user(context, chat_id, interests_str, articles):
    interests = [i.strip() for i in interests_str.split(",") if i.strip()]
    matches = match_articles(interests, articles)

    sent_count = 0
    for article in matches:
        if db.was_sent(chat_id, article["url"]):
            continue
        message = (
            f"📰 *{article['title']}*\n"
            f"_matched: {article['matched_interest']} ({article['score']})_\n"
            f"{article['source']}\n"
            f"{article['url']}"
        )
        try:
            await context.bot.send_message(
                chat_id=chat_id, text=message, parse_mode="Markdown"
            )
            db.mark_sent(chat_id, article["url"])
            sent_count += 1
        except Exception as e:
            logger.error(f"Failed to send to {chat_id}: {e}")

        if sent_count >= MAX_ARTICLES_PER_CYCLE:
            break

    return sent_count


async def news_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    interests_str = db.get_interests(chat_id)
    if not interests_str:
        await update.message.reply_text("Set interests first with /setinterests")
        return

    await update.message.reply_text("Checking latest news for you...")
    articles = fetch_all_articles()
    sent = await send_matches_to_user(context, chat_id, interests_str, articles)
    if sent == 0:
        await update.message.reply_text(
            "No new matching articles right now. I'll keep watching in the background."
        )


async def scheduled_check(context: ContextTypes.DEFAULT_TYPE):
    users = db.get_all_users()
    if not users:
        return
    logger.info(f"Running scheduled check for {len(users)} user(s)")
    articles = fetch_all_articles()
    for chat_id, interests_str in users:
        await send_matches_to_user(context, chat_id, interests_str, articles)


def main():
    if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        raise SystemExit(
            "Set TELEGRAM_BOT_TOKEN (env var or in config.py) before running."
        )

    db.init_db()
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setinterests", set_interests))
    app.add_handler(CommandHandler("myinterests", my_interests))
    app.add_handler(CommandHandler("news", news_now))

    app.job_queue.run_repeating(
        scheduled_check, interval=CHECK_INTERVAL_MINUTES * 60, first=30
    )

    logger.info("Bot starting (polling)...")
    app.run_polling()


if __name__ == "__main__":
    main()
