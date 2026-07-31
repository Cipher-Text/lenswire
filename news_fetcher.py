import feedparser
import requests

from config import RSS_FEEDS, NEWSAPI_KEY


def fetch_rss_articles():
    articles = []
    for feed_url in RSS_FEEDS:
        try:
            parsed = feedparser.parse(feed_url)
            source_name = parsed.feed.get("title", feed_url)
            for entry in parsed.entries[:20]:
                articles.append(
                    {
                        "title": entry.get("title", ""),
                        "description": entry.get("summary", ""),
                        "url": entry.get("link", ""),
                        "source": source_name,
                    }
                )
        except Exception as e:
            print(f"[news_fetcher] Error fetching RSS {feed_url}: {e}")
    return articles


def fetch_newsapi_articles(query=None):
    if not NEWSAPI_KEY or NEWSAPI_KEY == "YOUR_NEWSAPI_KEY":
        return []

    articles = []
    try:
        if query:
            endpoint = "https://newsapi.org/v2/everything"
            params = {
                "apiKey": NEWSAPI_KEY,
                "q": query,
                "language": "en",
                "pageSize": 50,
                "sortBy": "publishedAt",
            }
        else:
            endpoint = "https://newsapi.org/v2/top-headlines"
            params = {"apiKey": NEWSAPI_KEY, "language": "en", "pageSize": 50}

        resp = requests.get(endpoint, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        for a in data.get("articles", []):
            articles.append(
                {
                    "title": a.get("title") or "",
                    "description": a.get("description") or "",
                    "url": a.get("url", ""),
                    "source": (a.get("source") or {}).get("name", "NewsAPI"),
                }
            )
    except Exception as e:
        print(f"[news_fetcher] Error fetching NewsAPI: {e}")
    return articles


def fetch_all_articles(query=None):
    """Combine RSS + NewsAPI results, deduplicated by URL."""
    articles = fetch_rss_articles() + fetch_newsapi_articles(query)
    seen = set()
    unique = []
    for a in articles:
        if a["url"] and a["url"] not in seen and a["title"]:
            seen.add(a["url"])
            unique.append(a)
    return unique
