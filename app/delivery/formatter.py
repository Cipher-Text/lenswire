from __future__ import annotations

import html
import re
from datetime import datetime

BANGLA_RE = re.compile(r"[\u0980-\u09ff]")


def escape(value: object) -> str:
    return html.escape(html.unescape("" if value is None else str(value)), quote=False)


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


def _has_bangla(value: object) -> bool:
    return bool(BANGLA_RE.search("" if value is None else str(value)))


def format_channel_message(row: dict, language: str = "en") -> str:
    if language != "bn":
        return format_external_message(row)

    topics = row.get("bangla_topics") or row.get("topics") or "ভূরাজনীতি"
    topic = str(topics).split(",")[0]
    source = row.get("source_name") or "অজানা"
    summary = row.get("summary") or row.get("raw_description") or ""
    if not _has_bangla(summary):
        summary = (
            f"{topic} বিষয়ে {source}-এর একটি সাম্প্রতিক প্রতিবেদন। " "বিস্তারিত জানতে মূল প্রতিবেদনটি পড়ুন।"
        )
    why = row.get("why_it_matters") or ""
    if not _has_bangla(why):
        why = (
            "এই খবরটি গুরুত্বপূর্ণ, কারণ এটি সংশ্লিষ্ট অঞ্চলের কূটনীতি, নিরাপত্তা "
            "বা নীতিগত আলোচনায় প্রভাব ফেলতে পারে।"
        )
    url = html.escape(row.get("canonical_url") or row.get("original_url") or "", quote=True)
    return "\n\n".join(
        [
            f"🌍 <b>{escape(topic)}</b>",
            f"<b>সারসংক্ষেপ:</b>\n{escape(summary)}",
            f"<b>কেন গুরুত্বপূর্ণ:</b>\n{escape(why)}",
            f"<b>সূত্র:</b>\n{escape(source)}",
            f"<b>প্রকাশিত:</b>\n{escape(format_time(row.get('publication_time')))}",
            f'<b>মূল প্রতিবেদন:</b>\n<a href="{url}">খবরটি পড়ুন</a>',
        ]
    )
