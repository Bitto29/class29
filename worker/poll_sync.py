import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import GetForumTopicsRequest
from common import env, configured_groups, GitHubJSON, video_ids, extract_links

async def topic_names(client, group):
    names = {}
    offset = 0
    while True:
        result = await client(GetForumTopicsRequest(
            peer=group, offset_date=None, offset_id=0,
            offset_topic=offset, limit=100
        ))
        batch = result.topics or []
        for topic in batch:
            names[topic.id] = topic.title
        if len(batch) < 100:
            break
        offset = batch[-1].id
    return names

async def main():
    client = TelegramClient(
        StringSession(env("TELEGRAM_SESSION")),
        int(env("TELEGRAM_API_ID")),
        env("TELEGRAM_API_HASH")
    )
    await client.connect()
    if not await client.is_user_authorized():
        raise RuntimeError("Telegram session is not authorized. Reconnect Telegram.")
    writer = GitHubJSON()
    try:
        for cfg in configured_groups():
            group = await client.get_entity(cfg["id"])
            topics = await topic_names(client, group)
            print(f"Checking {cfg['name']} ({len(topics)} topics)")
            count = 0
            # A rolling recent-message window makes scheduled runs incremental;
            # GitHubJSON.add() deduplicates messages already imported.
            async for message in client.iter_messages(group, limit=500):
                text = message.message or ""
                ids = video_ids(text)
                resources = extract_links(message)
                if not ids and not resources:
                    continue
                top_id = (
                    getattr(message, "reply_to_top_id", None)
                    or getattr(message, "reply_to_msg_id", None)
                )
                topic = topics.get(top_id, "General")
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                title = lines[0][:140] if lines else "Class materials"
                if ids:
                    for video_id in ids:
                        await writer.add(
                            cfg["id"], cfg["name"], topic, title,
                            video_id, resources, message.date, message.id
                        )
                else:
                    await writer.add(
                        cfg["id"], cfg["name"], topic, title,
                        None, resources, message.date, message.id
                    )
                count += 1
            print(f"Checked {count} class/resource messages in {cfg['name']}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
