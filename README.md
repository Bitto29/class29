# Class 29

A personal library for class videos and shared slide/PDF links from multiple Telegram groups.

## Setup service (first)
1. Enable GitHub Pages from `main` / root.
2. In Render, create a Blueprint using this repository and the file `render.yaml`. This creates only the Telegram setup web service.
3. Set `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, and a long random `SETUP_KEY` when Render asks. Keep all three private.
4. Open the deployed service's public URL, then visit `https://bitto29.github.io/class29/setup.html`. Enter that service URL and the same setup key. Complete Telegram login and choose the groups. Copy the generated session and group JSON directly into a private place for the next step. Never paste them into chat or GitHub.

## Sync worker (after Telegram setup)
1. Create a second Render Blueprint from this same repository, selecting the file `render-worker.yaml`.
2. Set `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE`, `TELEGRAM_SESSION`, `TELEGRAM_GROUPS_JSON`, and `GITHUB_TOKEN` as private environment variables. Use the same API ID/hash and phone as the setup login. The GitHub token must have Contents: Read and write access to this repository only.
3. Keep `GITHUB_REPOSITORY=Bitto29/class29`, `GITHUB_BRANCH=main`, and `DATA_PATH=data/classes.json`. Deploy the worker.

## Security and limitations
- The setup service handles the Telegram login code and optional 2FA password in memory. It returns a Telethon session string to your browser after successful login. The session is a full account credential. Use HTTPS, keep the setup service private with a strong `SETUP_KEY`, and never share or commit the session.
- Render service logs should not contain secrets. Do not enable request-body logging.
- GitHub Pages and `data/classes.json` are public. Class titles and extracted links are readable by anyone who can access the site/repository.
- The setup page lists groups and forum status. Current importer/listener sync forum-topic messages and messages with supported video/resource links.
- Direct Telegram file uploads are not mirrored. PDF/Drive/Slides links are retained as links and their original sharing permissions still apply.
- The setup web service uses in-memory pending login state. If it restarts during the code-verification step, start login again.
