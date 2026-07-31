# Editorial Workflow

Editorial review is optional. The default Lenswire flow auto-publishes stories from enabled trusted sources when:

```env
EXTERNAL_DELIVERY_APPROVAL_REQUIRED=false
AUTO_PUBLISH_TRUSTED_SOURCES=true
```

Use this workflow only if you want review-gated delivery. For review gates, set:

```env
EXTERNAL_DELIVERY_APPROVAL_REQUIRED=true
AUTO_PUBLISH_TRUSTED_SOURCES=false
```

Editorial users are authorized by `EDITORIAL_TELEGRAM_IDS` or a database role.

Core commands:

- `/review`: list pending stories with editorial details and inline actions.
- `/context <article_id>`: show one story in the editorial format.
- `/save <article_id>`: mark a story as saved for review.
- `/approve <article_id>`: approve a story and set verification status to `EDITOR_APPROVED`.
- `/reject <article_id>`: reject a story and set verification status to `REJECTED`.
- `/sources`: show the source registry.
- `/breaking`: shortcut to the pending queue.

Approval does not mean the underlying facts are independently verified. It means an editor has approved the item for Lenswire handling.
