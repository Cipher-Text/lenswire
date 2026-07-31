import os

# --- Credentials (set as environment variables, or just paste them here for local use) ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "YOUR_NEWSAPI_KEY")  # get a free key at newsapi.org

# --- RSS sources (free, no key needed). Add/remove as you like. ---
RSS_FEEDS = [
    "http://feeds.bbci.co.uk/news/rss.xml",
    "https://techcrunch.com/feed/",
    "https://www.espn.com/espn/rss/news",
    "https://feeds.reuters.com/reuters/topNews",
    "https://www.theverge.com/rss/index.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
]

# --- Behavior ---
CHECK_INTERVAL_MINUTES = 30          # how often to poll for new articles
SIMILARITY_THRESHOLD = 0.35          # cosine similarity cutoff to count as a "match" (0-1, higher = stricter)
MAX_ARTICLES_PER_CYCLE = 5           # cap messages sent to one user per check, to avoid spam
DB_PATH = "news_bot.db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # small, fast, good enough for this use case
