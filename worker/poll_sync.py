import asyncio
import os

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import GetForumTopicsRequest

from common import (
    env,
    configured_groups,
    GitHubJSON,
    video_ids,
    extract_links,
    pick_title,
)


async def topic_names(client, group):
    names = {}
    offset = 0

    while True:
        result = await client(GetForumTopicsRequest(
            peer=group,
            offset_date=None,
            offset_id=0,
            offset_topic=offset,
            limit=100,
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
        env("TELEGRAM_API_HASH"),
    )

    await client.connect()
    if not await client.is_user_authorized():
        await client.disconnect()
        raise RuntimeError(
            "Telegram session is not authorized. Reconnect Telegram."
        )

    entries = []
    try:
        for cfg in configured_groups():
            group = await client.get_entity(cfg["id"])
            topics = await topic_names(client, group)
            print(f"Checking {cfg['name']} ({len(topics)} topics)")

            count = 0
            async for message in client.iter_messages(group, limit=int(os.getenv("SYNC_LIMIT", "500"))):
                message_text = message.message or ""
                ids = video_ids(message_text)
                resources = extract_links(message)

                if not ids and not resources:
                    continue

                top_id = (
                    getattr(message, "reply_to_top_id", None)
                    or getattr(message, "reply_to_msg_id", None)
                )
                topic = topics.get(top_id, "General")
                lines = [
                    line.strip()
                    for line in message_text.splitlines()
                    if line.strip()
                ]
                title = pick_title(message_text, topic) or (lines[0][:140] if lines else "Class materials")

                # One Telegram message can contain more than one YouTube URL.
                video_values = ids or [None]
                for video_id in video_values:
                    entries.append({
                        "group_id": cfg["id"],
                        "group_name": cfg["name"],
                        "topic": topic,
                        "title": title,
                        "video_id": video_id,
                        "resources": resources,
                        "date": message.date,
                        "message_id": message.id,
                    })
                count += 1

            print(
                f"Collected {count} class/resource messages from {cfg['name']}"
            )

        print(f"Prepared {len(entries)} entries from all configured groups.")
        await GitHubJSON().add_many(entries)
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
