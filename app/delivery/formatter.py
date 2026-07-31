from __future__ import annotations

import html
from datetime import datetime


def escape(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=False)


def format_time(value: str | None) -> str:
    if not value:
        return "Unknown"
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.strftime("%d %B %Y, %-I:%M %p UTC")
    except ValueError:
        return value


def format_editorial_message(row: dict) -> str:
    topics = row.get("topics") or "Unclassified"
    summary = row.get("summary") or row.get("raw_description") or "Summary pending."
    why = row.get("why_it_matters") or "Editorial significance pending."
    angle = row.get("editorial_angle") or "Pending editorial review."
    url = html.escape(row.get("canonical_url") or row.get("original_url") or "", quote=True)
    return "\n\n".join(
        [
            f"🌍 <b>{escape(str(topics).split(' · ')[0].split(',')[0])}</b>",
            f"<b>{escape(row.get('original_headline'))}</b>",
            f"<b>Summary:</b>\n{escape(summary)}",
            f"<b>Why it matters:</b>\n{escape(why)}",
            f"<b>Main source:</b>\n{escape(row.get('source_name') or 'Unknown')}",
            "<b>Primary source:</b>\nNot identified",
            "<b>Supporting sources:</b>\nNot identified",
            f"<b>Published:</b>\n{escape(format_time(row.get('publication_time')))}",
            f"<b>Topics:</b>\n{escape(topics)}",
            f"<b>Verification:</b>\n{escape(row.get('verification_status') or 'UNREVIEWED')}",
            f"<b>Editorial angle:</b>\n{escape(angle)}",
            f'<b>Read original:</b>\n<a href="{url}">Open article</a>',
        ]
    )


def format_external_message(row: dict) -> str:
    topics = row.get("topics") or "Geopolitics"
    summary = row.get("summary") or row.get("raw_description") or "Summary pending."
    why = row.get("why_it_matters") or (
        "This story may affect regional or international policy debates."
    )
    url = html.escape(row.get("canonical_url") or row.get("original_url") or "", quote=True)
    return "\n\n".join(
        [
            f"🌍 <b>{escape(str(topics).split(',')[0])}</b>",
            f"<b>{escape(row.get('original_headline'))}</b>",
            f"<b>Summary:</b>\n{escape(summary)}",
            f"<b>Why it matters:</b>\n{escape(why)}",
            f"<b>Source:</b>\n{escape(row.get('source_name') or 'Unknown')}",
            f"<b>Published:</b>\n{escape(format_time(row.get('publication_time')))}",
            f'<b>Read original:</b>\n<a href="{url}">Open article</a>',
        ]
    )
