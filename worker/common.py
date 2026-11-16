import os
import re
import json
import base64
import asyncio
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv

load_dotenv()

YT = re.compile(
    r"(?:https?://)?(?:www\\.|m\\.)?(?:youtube\\.com/(?:watch\\?v=|shorts/|live/)|youtu\\.be/)([A-Za-z0-9_-]{11})",
    re.I,
)
URL = re.compile(r"https?://[^\\s<>\\])}]+", re.I)


def env(key):
    value = os.getenv(key)
    if not value:
        raise RuntimeError("Missing environment variable: " + key)
    return value


def configured_groups():
    groups = json.loads(env("TELEGRAM_GROUPS_JSON"))
    if not isinstance(groups, list) or not groups:
        raise RuntimeError("TELEGRAM_GROUPS_JSON must be a non-empty JSON array")

    clean = []
    for item in groups:
        if not isinstance(item, dict) or "id" not in item:
            raise RuntimeError("Each group needs an id and optional name")
        clean.append({
            "id": int(item["id"]),
            "name": str(item.get("name") or item["id"]),
        })
    return clean


def video_ids(text):
    return list(dict.fromkeys(YT.findall(text or "")))


def extract_links(message):
    text = message.message or ""
    found = []

    for raw in URL.findall(text):
        url = raw.rstrip(".,;:!?")
        if url not in found and not YT.search(url):
            found.append(url)

    for entity in message.entities or []:
        url = getattr(entity, "url", None)
        if url and url not in found and not YT.search(url):
            found.append(url)

    return [{"url": url, "label": resource_label(url)} for url in found]


def resource_label(url):
    host = urlparse(url).netloc.lower()
    if "drive.google.com" in host:
        return "Google Drive"
    if "docs.google.com" in host:
        return "Google Slides / Docs"
    if urlparse(url).path.lower().endswith(".pdf"):
        return "PDF"
    return host or "Resource"


def now():
    return datetime.now(timezone.utc).isoformat()


class GitHubJSON:
    def __init__(self):
        self.token = env("GITHUB_TOKEN")
        self.repo = env("GITHUB_REPOSITORY")
        self.branch = os.getenv("GITHUB_BRANCH", "main")
        self.path = os.getenv("DATA_PATH", "data/classes.json")
        self.url = (
            "https://api.github.com/repos/"
            + self.repo
            + "/contents/"
            + self.path
        )
        self.headers = {
            "Authorization": "Bearer " + self.token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def read(self, client):
        response = await client.get(
            self.url,
            headers=self.headers,
            params={"ref": self.branch},
        )
        if response.status_code == 404:
            return {"version": 2, "updated_at": None, "groups": []}, None

        response.raise_for_status()
        payload = response.json()
        data = json.loads(base64.b64decode(payload["content"]).decode("utf-8"))
        data.setdefault("groups", [])
        return data, payload["sha"]

    @staticmethod
    def _class_item(entry):
        group_id = str(entry["group_id"])
        video_id = entry.get("video_id")
        message_id = entry["message_id"]
        key = group_id + ":" + str(message_id) + ":" + (video_id or "links")
        date = entry.get("date")

        item = {
            "id": "cv-" + re.sub(r"[^a-zA-Z0-9_-]", "-", key),
            "source_key": key,
            "title": entry.get("title") or (
                "Class " + video_id if video_id else "Class materials"
            ),
            "topic": entry["topic"],
            "date": date.isoformat() if date else now(),
            "telegram_message_id": message_id,
            "resources": entry.get("resources") or [],
        }
        if video_id:
            item.update({
                "video_id": video_id,
                "url": "https://www.youtube.com/watch?v=" + video_id,
            })
        return key, item

    async def add_many(self, entries):
        """Add many Telegram messages with one GitHub read and one commit."""
        if not entries:
            print("No class/resource messages found.")
            return 0

        async with httpx.AsyncClient(timeout=60) as client:
            for attempt in range(5):
                data, sha = await self.read(client)
                groups = data.setdefault("groups", [])

                group_map = {str(group.get("id")): group for group in groups}
                topic_maps = {}
                existing_keys = set()

                for group in groups:
                    topic_map = {
                        topic.get("name", "").casefold(): topic
                        for topic in group.setdefault("topics", [])
                    }
                    topic_maps[str(group.get("id"))] = topic_map
                    for topic in group["topics"]:
                        for item in topic.get("classes", []):
                            source_key = item.get("source_key")
                            if source_key:
                                existing_keys.add(source_key)

                added = 0
                for entry in entries:
                    group_id = str(entry["group_id"])
                    group_name = entry["group_name"]
                    topic_name = entry["topic"]

                    key, item = self._class_item(entry)
                    if key in existing_keys:
                        continue

                    group = group_map.get(group_id)
                    if group is None:
                        group = {
                            "id": group_id,
                            "name": group_name,
                            "topics": [],
                        }
                        groups.append(group)
                        group_map[group_id] = group
                        topic_maps[group_id] = {}

                    group["name"] = group_name or group.get("name") or group_id
                    topic_map = topic_maps[group_id]
                    topic_key = topic_name.casefold()
                    topic = topic_map.get(topic_key)
                    if topic is None:
                        topic = {"name": topic_name, "classes": []}
                        group.setdefault("topics", []).append(topic)
                        topic_map[topic_key] = topic

                    topic.setdefault("classes", []).append(item)
                    existing_keys.add(key)
                    added += 1

                if added == 0:
                    print("No new Telegram entries. Existing data is up to date.")
                    return 0

                for group in groups:
                    for topic in group.get("topics", []):
                        topic.setdefault("classes", []).sort(
                            key=lambda item: item.get("date", ""),
                            reverse=True,
                        )
                    group["topics"].sort(
                        key=lambda item: item.get("name", "").casefold()
                    )
                groups.sort(key=lambda item: item.get("name", "").casefold())

                data["version"] = 2
                data["updated_at"] = now()
                body = {
                    "message": "Batch sync Telegram class materials",
                    "content": base64.b64encode(
                        json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
                    ).decode("ascii"),
                    "branch": self.branch,
                }
                if sha:
                    body["sha"] = sha

                response = await client.put(
                    self.url,
                    headers=self.headers,
                    json=body,
                )
                if response.status_code in (409, 422) and attempt < 4:
                    await asyncio.sleep(0.8 * (attempt + 1))
                    continue
                response.raise_for_status()
                print(f"Saved {added} new class/resource entries in one GitHub update.")
                return added

        raise RuntimeError("GitHub JSON batch update failed after retries")

    async def add(self, group_id, group_name, topic, title, vid, resources, date, msgid):
        """Compatibility method for the history importer."""
        return await self.add_many([{
            "group_id": group_id,
            "group_name": group_name,
            "topic": topic,
            "title": title,
            "video_id": vid,
            "resources": resources,
            "date": date,
            "message_id": msgid,
        }])
