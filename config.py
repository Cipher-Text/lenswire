from app.settings import settings

TELEGRAM_BOT_TOKEN = settings.telegram_bot_token or "YOUR_TELEGRAM_BOT_TOKEN"
NEWSAPI_KEY = settings.newsapi_key or "YOUR_NEWSAPI_KEY"
CHECK_INTERVAL_MINUTES = settings.ingestion_interval_minutes
SIMILARITY_THRESHOLD = settings.similarity_threshold
MAX_ARTICLES_PER_CYCLE = settings.max_articles_per_delivery
DB_PATH = str(settings.database_path)
SOURCE_CONFIG_PATH = str(settings.source_config_path)
EMBEDDING_MODEL = settings.embedding_model_name
RSS_FEEDS: list[str] = []
