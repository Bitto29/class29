# ClassVault 29

A public, database-free library for recorded YouTube classes shared in a Telegram forum.

## Architecture
Telegram forum (your own authorized Telegram user session) → persistent Python listener → GitHub Contents API → data/classes.json → public static website.

- Public static frontend, no database.
- Old visible topic history can be imported once.
- New YouTube links are synced from Telegram message events.
- Only messages containing YouTube links are processed.

## Setup
1. Enable GitHub Pages: Settings → Pages → Deploy from a branch → main → /(root).
2. In Telegram, create API credentials at https://my.telegram.org.
3. Install Python 3.10+ in the worker folder: pip install -r requirements.txt
4. Copy .env.example to .env and configure the values.
5. Run python auth_session.py once and securely store the printed session string as TELEGRAM_SESSION.
6. Run python importer.py once to import accessible old classes.
7. Deploy worker/listener.py as a persistent background worker and add all environment variables as private secrets.

Required secrets: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE, TELEGRAM_GROUP_ID, TELEGRAM_SESSION, GITHUB_TOKEN, GITHUB_REPOSITORY.

The GitHub token needs Contents: Read and write permission on this repository only. Never commit .env or a Telegram session.

## Important
The repository and website are public. Class titles and YouTube links in classes.json are visible to everyone. Other Telegram messages are ignored. Use only videos you have permission to share. Some videos may disable embedding.

Instant sync is event-driven, but GitHub API and Pages/CDN caching may add a short delay. Watch progress is stored locally in each visitor's browser only.
