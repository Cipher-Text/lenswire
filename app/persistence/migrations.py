from __future__ import annotations

from pathlib import Path

from app.domain.article import ArticleStatus, ExtractionStatus, VerificationStatus
from app.domain.source import CredibilityTier, SourceType
from app.persistence.source_config import load_source_config
from app.persistence.sqlite import sqlite_connection

TOPIC_SEEDS = [
    ("south-asia", "South Asia", "দক্ষিণ এশিয়া", "Regional politics and geopolitics in South Asia"),
    ("bangladesh-foreign-policy", "Bangladesh Foreign Policy", "বাংলাদেশের পররাষ্ট্রনীতি", None),
    ("india", "India", "ভারত", None),
    ("pakistan", "Pakistan", "পাকিস্তান", None),
    ("china", "China", "চীন", None),
    ("myanmar", "Myanmar", "মিয়ানমার", None),
    ("rohingya-rakhine", "Rohingya and Rakhine", "রোহিঙ্গা ও রাখাইন", None),
    ("middle-east", "Middle East", "মধ্যপ্রাচ্য", None),
    ("iran", "Iran", "ইরান", None),
    ("israel-palestine", "Israel-Palestine", "ইসরায়েল-ফিলিস্তিন", None),
    ("turkey", "Turkey", "তুরস্ক", None),
    ("russia-ukraine", "Russia-Ukraine", "রাশিয়া-ইউক্রেন", None),
    ("united-states", "United States", "যুক্তরাষ্ট্র", None),
    ("european-union", "European Union", "ইউরোপীয় ইউনিয়ন", None),
    ("us-china-relations", "US-China Relations", "যুক্তরাষ্ট্র-চীন সম্পর্ক", None),
    ("global-trade", "Global Trade", "বৈশ্বিক বাণিজ্য", None),
    ("strategic-minerals", "Strategic Minerals", "কৌশলগত খনিজ", None),
    ("semiconductors", "Semiconductors", "সেমিকন্ডাক্টর", None),
    ("defence-security", "Defence and Security", "প্রতিরক্ষা ও নিরাপত্তা", None),
    ("diplomacy", "Diplomacy", "কূটনীতি", None),
    ("borders-nationalism", "Borders and Nationalism", "সীমান্ত ও জাতীয়তাবাদ", None),
    ("climate-geopolitics", "Climate Geopolitics", "জলবায়ু ভূরাজনীতি", None),
]


SOURCE_SEEDS = [
    (
        "Reuters",
        "reuters.com",
        SourceType.NEWS_AGENCY,
        CredibilityTier.TIER_2,
        "en",
        "Global",
        "https://feeds.reuters.com/reuters/worldNews",
    ),
    (
        "Associated Press",
        "apnews.com",
        SourceType.NEWS_AGENCY,
        CredibilityTier.TIER_2,
        "en",
        "Global",
        "https://apnews.com/hub/world-news?output=rss",
    ),
    ("AFP", "afp.com", SourceType.NEWS_AGENCY, CredibilityTier.TIER_2, "en", "Global", None),
    (
        "Bloomberg",
        "bloomberg.com",
        SourceType.NEWS_AGENCY,
        CredibilityTier.TIER_2,
        "en",
        "Global",
        None,
    ),
    (
        "Al Jazeera",
        "aljazeera.com",
        SourceType.MAJOR_OUTLET,
        CredibilityTier.TIER_3,
        "en",
        "Global",
        "https://www.aljazeera.com/xml/rss/all.xml",
    ),
    (
        "BBC News",
        "bbc.co.uk",
        SourceType.MAJOR_OUTLET,
        CredibilityTier.TIER_3,
        "en",
        "Global",
        "http://feeds.bbci.co.uk/news/world/rss.xml",
    ),
    (
        "The Diplomat",
        "thediplomat.com",
        SourceType.SPECIALIST_OUTLET,
        CredibilityTier.TIER_3,
        "en",
        "Asia-Pacific",
        "https://thediplomat.com/feed/",
    ),
    (
        "International Crisis Group",
        "crisisgroup.org",
        SourceType.SPECIALIST_OUTLET,
        CredibilityTier.TIER_3,
        "en",
        "Global",
        "https://www.crisisgroup.org/rss.xml",
    ),
    (
        "Google News",
        "news.google.com",
        SourceType.DISCOVERY_ONLY,
        CredibilityTier.DISCOVERY,
        "multi",
        "Global",
        None,
    ),
    (
        "United Nations",
        "un.org",
        SourceType.PRIMARY,
        CredibilityTier.TIER_1,
        "en",
        "Global",
        "https://news.un.org/feed/subscribe/en/news/all/rss.xml",
    ),
]


def migrate(
    database_path: Path | str,
    source_config_path: Path | str = "config/sources.yaml",
) -> None:
    with sqlite_connection(database_path) as conn:
        conn.executescript(
            f"""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER PRIMARY KEY,
                interests TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS sent_articles (
                chat_id INTEGER,
                article_url TEXT,
                PRIMARY KEY (chat_id, article_url)
            );

            CREATE TABLE IF NOT EXISTS lenswire_users (
                chat_id INTEGER PRIMARY KEY,
                role TEXT NOT NULL DEFAULT 'EXTERNAL',
                language TEXT NOT NULL DEFAULT 'en',
                quiet_start TEXT,
                quiet_end TEXT,
                stopped INTEGER NOT NULL DEFAULT 0,
                legacy_interests TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS topics (
                key TEXT PRIMARY KEY,
                english_name TEXT NOT NULL,
                bangla_name TEXT NOT NULL,
                description TEXT,
                enabled INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS user_topic_subscriptions (
                chat_id INTEGER NOT NULL,
                topic_key TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (chat_id, topic_key),
                FOREIGN KEY (chat_id) REFERENCES lenswire_users(chat_id) ON DELETE CASCADE,
                FOREIGN KEY (topic_key) REFERENCES topics(key) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                domain TEXT NOT NULL UNIQUE,
                source_type TEXT NOT NULL,
                credibility_tier TEXT NOT NULL,
                language TEXT NOT NULL,
                country_or_region TEXT NOT NULL,
                rss_url TEXT,
                enabled INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_headline TEXT NOT NULL,
                original_url TEXT NOT NULL,
                canonical_url TEXT NOT NULL UNIQUE,
                source_id INTEGER,
                source_name TEXT NOT NULL DEFAULT '',
                discovery_source TEXT NOT NULL DEFAULT '',
                author TEXT,
                publication_time TEXT,
                fetched_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                language TEXT NOT NULL DEFAULT 'unknown',
                raw_description TEXT NOT NULL DEFAULT '',
                extracted_content TEXT NOT NULL DEFAULT '',
                normalized_title TEXT NOT NULL DEFAULT '',
                content_hash TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT '{ArticleStatus.NEW.value}',
                extraction_status TEXT NOT NULL DEFAULT '{ExtractionStatus.PENDING.value}',
                extraction_error TEXT,
                FOREIGN KEY (source_id) REFERENCES sources(id)
            );

            CREATE TABLE IF NOT EXISTS article_topics (
                article_id INTEGER NOT NULL,
                topic_key TEXT NOT NULL,
                score REAL NOT NULL DEFAULT 0,
                PRIMARY KEY (article_id, topic_key),
                FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
                FOREIGN KEY (topic_key) REFERENCES topics(key) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS story_clusters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                normalized_title TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS supporting_sources (
                article_id INTEGER NOT NULL,
                supporting_article_id INTEGER NOT NULL,
                relationship TEXT NOT NULL DEFAULT 'SUPPORTING',
                score REAL NOT NULL DEFAULT 0,
                PRIMARY KEY (article_id, supporting_article_id),
                FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
                FOREIGN KEY (supporting_article_id) REFERENCES articles(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS summaries (
                article_id INTEGER PRIMARY KEY,
                summary TEXT NOT NULL,
                why_it_matters TEXT NOT NULL,
                editorial_angle TEXT NOT NULL,
                verification_status TEXT NOT NULL DEFAULT '{VerificationStatus.UNREVIEWED.value}',
                language TEXT NOT NULL DEFAULT 'en',
                provider TEXT NOT NULL DEFAULT 'deterministic',
                status TEXT NOT NULL DEFAULT 'SUCCESS',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS editorial_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                reviewer_chat_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS delivery_history (
                chat_id INTEGER NOT NULL,
                article_id INTEGER NOT NULL,
                delivered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'SENT',
                error TEXT,
                PRIMARY KEY (chat_id, article_id),
                FOREIGN KEY (chat_id) REFERENCES lenswire_users(chat_id) ON DELETE CASCADE,
                FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS channel_delivery_history (
                channel_id TEXT NOT NULL,
                article_id INTEGER NOT NULL,
                delivered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'SENT',
                error TEXT,
                PRIMARY KEY (channel_id, article_id),
                FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_articles_canonical_url ON articles(canonical_url);
            CREATE INDEX IF NOT EXISTS idx_articles_content_hash ON articles(content_hash);
            CREATE INDEX IF NOT EXISTS idx_articles_publication_time ON articles(publication_time);
            CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
            CREATE INDEX IF NOT EXISTS idx_user_topic
            ON user_topic_subscriptions(topic_key, chat_id);
            CREATE INDEX IF NOT EXISTS idx_delivery_pair ON delivery_history(chat_id, article_id);
            CREATE INDEX IF NOT EXISTS idx_channel_delivery_pair
            ON channel_delivery_history(channel_id, article_id);
            """
        )

        conn.execute(
            """
            INSERT OR IGNORE INTO lenswire_users (chat_id, legacy_interests)
            SELECT chat_id, COALESCE(interests, '') FROM users
            """
        )

        conn.executemany(
            """
            INSERT OR IGNORE INTO topics (key, english_name, bangla_name, description, enabled)
            VALUES (?, ?, ?, ?, 1)
            """,
            TOPIC_SEEDS,
        )
        source_rows = load_source_config(source_config_path) or [
            {
                "name": n,
                "domain": d,
                "source_type": st.value,
                "credibility_tier": ct.value,
                "language": lang,
                "country_or_region": reg,
                "rss_url": rss,
                "enabled": True,
            }
            for n, d, st, ct, lang, reg, rss in SOURCE_SEEDS
        ]

        conn.executemany(
            """
            INSERT INTO sources
            (
                name, domain, source_type, credibility_tier,
                language, country_or_region, rss_url, enabled
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(domain) DO UPDATE SET
                name=excluded.name,
                source_type=excluded.source_type,
                credibility_tier=excluded.credibility_tier,
                language=excluded.language,
                country_or_region=excluded.country_or_region,
                rss_url=excluded.rss_url,
                enabled=excluded.enabled
            """,
            [
                (
                    row["name"],
                    row["domain"],
                    row["source_type"],
                    row["credibility_tier"],
                    row["language"],
                    row["country_or_region"],
                    row["rss_url"],
                    1 if row["enabled"] else 0,
                )
                for row in source_rows
            ],
        )
