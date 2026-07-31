# Source Policy

Lenswire distinguishes discovery sources from main publishing sources. Discovery platforms such as Google News must not be displayed as the main source when the article belongs to another publisher.

The editable source registry is:

```text
config/sources.yaml
```

After editing the file, restart the app so Lenswire syncs the file into SQLite:

```bash
docker compose restart lenswire
```

Set `enabled: false` to temporarily stop fetching a source without deleting it.

Credibility tiers:

- Tier 1: primary or official sources, including ministries, international organizations, courts, regulators, central banks and official statements.
- Tier 2: major agencies such as Reuters, Associated Press, AFP and Bloomberg.
- Tier 3: established international, regional and specialist outlets.

When a news article reports on an official announcement, the publisher remains the main source. The official document should be attached separately as the primary source when available.

Example source entry:

```yaml
- name: Reuters
  domain: reuters.com
  source_type: NEWS_AGENCY
  credibility_tier: TIER_2
  language: en
  country_or_region: Global
  rss_url: https://feeds.reuters.com/reuters/worldNews
  enabled: true
```
