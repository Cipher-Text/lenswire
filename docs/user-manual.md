# Lenswire User Manual

Lenswire is a Telegram bot for curated geopolitical news. It helps you follow topics such as South Asia, China, diplomacy, defence, trade, strategic minerals and other FactLens-relevant areas.

Lenswire is not a fact-checking service. Summaries can contain mistakes, and a story from one source should not be treated as independently verified. Use the original article link when accuracy matters.

## What You Can Do

- Subscribe to geopolitical topics.
- See your current subscriptions.
- Get recent stories matched to your topics.
- Change your language preference.
- Pause delivery.
- Delete your subscription data.

## Basic Flow

1. Open the Lenswire bot in Telegram.
2. Send `/start`.
3. Send `/topics`.
4. Tap topics you want to follow.
5. Send `/latest` to see recent stories.

You can also subscribe by typing a topic key manually:

```text
/subscribe china
```

## Story Messages

A Lenswire story usually includes:

- Headline
- Short summary
- Why it matters
- Source
- Publication time
- Original article link

Always open the original article if you need full context.

## Commands

## `/start`

Starts or resumes your Lenswire subscription.

```text
/start
```

## `/topics`

Shows available topics with buttons.

```text
/topics
```

Tap a topic button to subscribe.

## `/subscribe <topic-key>`

Subscribes you to a topic.

Examples:

```text
/subscribe china
/subscribe diplomacy
/subscribe bangladesh-foreign-policy
```

## `/unsubscribe <topic-key>`

Removes a topic from your subscriptions.

Example:

```text
/unsubscribe china
```

## `/mysubscriptions`

Shows the topics you currently follow.

```text
/mysubscriptions
```

## `/latest`

Shows recent stories for your subscribed topics.

```text
/latest
```

If no stories appear, try subscribing to broader topics such as:

```text
/subscribe south-asia
/subscribe middle-east
/subscribe diplomacy
```

## `/digest`

Shows recent stories for your subscribed topics. In the current version, this works like `/latest`.

```text
/digest
```

## Telegram Channel

The public channel does not use each user’s subscriptions. It publishes from the fixed topic list configured in `CHANNEL_TOPIC_KEYS`. If `CHANNEL_OUTPUT_LANGUAGE=bn`, channel labels and fallback text are Bangla; AI summaries should also be configured with `SUMMARY_OUTPUT_LANGUAGE=bn` for full Bangla output.

## `/language en|bn`

Sets your preferred language.

Examples:

```text
/language en
/language bn
```

Bangla support is available as a preference, but some summaries may still be stronger in English depending on the current summarization mode.

## `/quiettime <start> <end>`

Stores your quiet hours preference.

Example:

```text
/quiettime 22:00 07:00
```

## `/stop`

Stops Lenswire delivery for your account.

```text
/stop
```

Use `/start` again if you want to resume.

## `/deleteaccount`

Deletes your Lenswire subscription data.

```text
/deleteaccount
```

## Legacy Commands

These commands are kept for older users of the prototype.

## `/setinterests`

Stores free-text interests. Curated topic subscriptions are preferred now.

Example:

```text
/setinterests India, diplomacy, trade
```

## `/myinterests`

Shows your topic subscriptions and any old free-text interests.

```text
/myinterests
```

## `/news`

Manually asks Lenswire to check for new stories. This may have a cooldown.

```text
/news
```

For normal use, `/latest` is usually enough after you subscribe to topics.

## Topic Keys

You can subscribe through `/topics`, or type these keys manually:

- `south-asia`
- `bangladesh-foreign-policy`
- `india`
- `pakistan`
- `china`
- `myanmar`
- `rohingya-rakhine`
- `middle-east`
- `iran`
- `israel-palestine`
- `turkey`
- `russia-ukraine`
- `united-states`
- `european-union`
- `us-china-relations`
- `global-trade`
- `strategic-minerals`
- `semiconductors`
- `defence-security`
- `diplomacy`
- `borders-nationalism`
- `climate-geopolitics`

## Troubleshooting

## `/latest` Shows No Stories

Possible reasons:

- You have not subscribed to any topics yet.
- Lenswire has not found recent stories for your topics.
- Your topics are too narrow.

Try:

```text
/topics
/subscribe south-asia
/subscribe diplomacy
/latest
```

## I Tapped a Topic and It Says “Subscribed”

That means the topic was added to your subscriptions. Check with:

```text
/mysubscriptions
```

## I Made a Typo in a Command

Send the command again. For example, if `/mysubscriprtions` does not work, use:

```text
/mysubscriptions
```

## Privacy

Lenswire stores the Telegram chat ID needed to deliver messages, your topic subscriptions, language preference, quiet-hours preference and delivery history.

To delete your Lenswire subscription data:

```text
/deleteaccount
```

## Important Notes

- Lenswire summaries are for quick scanning.
- A source being trusted does not mean every claim is independently verified.
- Read the original article before quoting or republishing important information.
