# Data Model

SQLite tables:

- `lenswire_users`: Telegram users, roles, language, quiet hours, stop status and legacy interests.
- `topics`: curated geopolitical topics.
- `user_topic_subscriptions`: user-topic relationships.
- `sources`: source registry and credibility tiers.
- `articles`: article metadata, canonical URL, source, extraction fields and workflow status.
- `article_topics`: article-topic scores.
- `story_clusters`: placeholder for grouped story records.
- `supporting_sources`: article-to-article supporting relationships.
- `summaries`: structured summary fields (`summary`, `editorial_angle`, `verification_status`) and provider metadata. The `why_it_matters` column exists in the schema but is no longer populated.
- `editorial_reviews`: save, approve and reject events.
- `delivery_history`: per-user article delivery deduplication and failures.

Legacy tables `users` and `sent_articles` are preserved for migration compatibility.
