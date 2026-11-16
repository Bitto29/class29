# ClassVault 29

A public, database-free library for class videos and shared slide/PDF links from multiple Telegram forum groups.

## What it collects
- YouTube video links posted in configured group topics.
- Google Drive, Google Slides/Docs, direct PDF, and other ordinary URLs in the same Telegram message.
- Messages containing only a supported resource link are listed as materials-only entries.
- Group → Topic → Class organization, with each class showing its video and available material links.

## Architecture
Telegram groups (your own authorized Telegram user session) → persistent Python listener → GitHub Contents API → data/classes.json → public static website.

No database is used. The public website only displays extracted class titles and links, not the rest of Telegram messages.

## Setup
1. Enable GitHub Pages: Settings → Pages → Deploy from a branch → main → /(root).
2. Create Telegram API credentials at https://my.telegram.org.
3. In the Render background worker environment, set the secrets listed below.
4. Set TELEGRAM_GROUPS_JSON to a one-line JSON array. Example:
   `[{"id":-1001234567890,"name":"PCBD - POWERPLAY 27"},{"id":-1001234567891,"name":"PCBD - ACS FRB 27"}]`
   Include every group the Telegram account has joined and that you want to import. Use each group's numeric Telegram ID, not its display name.
5. Install Python 3.10+ in the worker folder: `pip install -r requirements.txt`.
6. Run `python auth_session.py` once on your own computer and securely store the printed session string as TELEGRAM_SESSION.
7. Run `python list_groups.py` to print the joined group's numeric IDs. Select the 5–10 groups you want and enter their IDs/names in TELEGRAM_GROUPS_JSON.
8. Run `python importer.py` once to import accessible old topic history from every configured group.
9. Deploy `worker/listener.py` as a persistent Render background worker. It watches all configured groups for new messages.

Required private environment variables: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE, TELEGRAM_SESSION, TELEGRAM_GROUPS_JSON, GITHUB_TOKEN, GITHUB_REPOSITORY.

The GitHub token needs Contents: Read and write permission on this repository only. Never commit .env or a Telegram session, and never send tokens/session strings in chat.

## PDF and slide links
The importer captures links present in Telegram message text and hidden URL entities. Google Drive, Google Slides/Docs, direct PDF, and other URLs are displayed under Class materials. This does not copy or host the PDF itself. The original link must be accessible to the website visitor. For private Drive files, change sharing to anyone-with-the-link or the visitor will need permission.

Telegram files uploaded directly (without an external link) are not downloaded or mirrored by this version.

## Important
The repository and website are public. Class titles, YouTube links, and extracted material links in classes.json are visible to everyone. Use only content you have permission to share. Some YouTube videos may disable embedding.

Instant sync is event-driven when Telegram delivers a message, but GitHub API and Pages/CDN caching may add a short delay. Watch progress is stored locally in each visitor's browser only.
