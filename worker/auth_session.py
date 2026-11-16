import asyncio
import getpass
import json
from telethon import TelegramClient
from telethon.sessions import StringSession

async def main():
    api_id = input("Telegram API ID: ").strip()
    api_hash = getpass.getpass("Telegram API Hash (hidden): ").strip()
    phone = input("Telegram phone number with country code: ").strip()

    client = TelegramClient(StringSession(), int(api_id), api_hash)
    await client.start(phone=phone)

    try:
        print("\\nYour Telegram groups:")
        choices = []
        async for dialog in client.iter_dialogs():
            entity = dialog.entity
            is_group = bool(dialog.is_group) or (
                bool(dialog.is_channel) and bool(getattr(entity, "megagroup", False))
            )
            if is_group:
                choices.append({"id": int(dialog.id), "name": dialog.name})
        if not choices:
            print("No groups found in this Telegram account.")
            return

        for index, group in enumerate(choices, 1):
            print(f"{index}. {group['name']}  (ID: {group['id']})")

        selected = input("\\nEnter the numbers of the groups to sync, separated by commas (example: 1,3,4): ")
        indexes = []
        for part in selected.split(","):
            part = part.strip()
            if part.isdigit() and 1 <= int(part) <= len(choices):
                indexes.append(int(part) - 1)
        indexes = list(dict.fromkeys(indexes))
        if not indexes:
            raise RuntimeError("No valid groups selected.")

        groups_json = json.dumps([choices[i] for i in indexes], ensure_ascii=False)
        session = client.session.save()

        print("\\n================ COPY THESE PRIVATELY ================")
        print("\\nTELEGRAM_SESSION:")
        print(session)
        print("\\nTELEGRAM_GROUPS_JSON:")
        print(groups_json)
        print("\\nKeep both values secret. Add them only as GitHub Actions repository secrets.")
        print("======================================================\\n")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
