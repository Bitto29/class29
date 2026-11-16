# Class 29

Class 29 is a simple public class library for personal use. The website is hosted on GitHub Pages. The class list is stored in `data/classes.json`.

## Free automatic sync

Telegram polling is designed to run through GitHub Actions, not Render:

- Workflow: `.github/workflows/telegram-sync.yml`
- Script: `worker/poll_sync.py`
- Schedule: every 15 minutes
- The workflow checks the latest 500 messages per selected group and deduplicates already imported messages.
- Standard GitHub-hosted runners are free for public repositories.

This is scheduled polling, not a permanently connected listener. New classes appear after the next successful run. GitHub may delay scheduled runs, and scheduled workflows in public repositories can be disabled after 60 days without repository activity.

## Required GitHub Actions secrets

Open the repository's **Settings → Secrets and variables → Actions → New repository secret** and add:

- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`
- `TELEGRAM_SESSION` (Telethon StringSession for the Telegram account)
- `TELEGRAM_GROUPS_JSON` (JSON array such as `[{"id":-1001234567890,"name":"Physics"}]`)

The workflow uses GitHub's automatically provided `GITHUB_TOKEN` with repository Contents write permission. A separate personal access token is not required.

**Important:** Telegram session strings grant access to the Telegram account. Never commit them, paste them into chat, or expose them in workflow logs. Store them only as GitHub Actions secrets. Use a unique Telegram account only if appropriate, and revoke the session from Telegram Settings → Devices if it may have been exposed.

## Current limitation: Telegram session setup

The scheduled workflow is committed, but the Telegram login/session setup and group-ID collection are not yet automated in a browser dashboard. The workflow will not sync until all four secrets above are correctly configured. Do not deploy Render or pay for hosting.

## Data and privacy

- The repository and GitHub Pages website are public. Anyone who finds the URL can browse the website and the class data. An unshared URL is not access control.
- Only YouTube URLs and ordinary resource links in selected group messages are collected.
- Google Drive/Slides/Docs/PDF files are stored as links, not copied. Original sharing permissions still apply.
- Telegram direct file uploads are not downloaded by this version.
