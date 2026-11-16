# Class 29

A personal library for class videos and shared slide/PDF links from multiple Telegram groups.

## Setup
1. Enable GitHub Pages from `main` / root.
2. Deploy the two services in `render.yaml` using Render Blueprint.
3. In the `class29-telegram-setup` web service, set `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, and a long random `SETUP_KEY`.
4. In the `class29-telegram-sync` background worker, set `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE`, `TELEGRAM_SESSION`, `TELEGRAM_GROUPS_JSON`, and `GITHUB_TOKEN`. Keep `GITHUB_REPOSITORY=Bitto29/class29`, `GITHUB_BRANCH=main`, and `DATA_PATH=data/classes.json`.
5. Open `https://bitto29.github.io/class29/setup.html`, enter the setup service URL and SETUP_KEY, then complete Telegram login and choose groups. Copy the generated session and group JSON directly into the worker's private Render environment. Never paste them into chat or GitHub.
6. Restart/deploy the worker.

## Security and limitations
- The setup service handles the Telegram login code and optional 2FA password in memory. It returns a Telethon session string to your browser after successful login. The session is a full account credential. Use HTTPS, keep the setup service private with a strong SETUP_KEY, and never share or commit the session.
- Render service logs should not contain secrets. Do not enable request-body logging.
- GitHub Pages and `data/classes.json` are public. Class titles and extracted links are readable by anyone who can access the site/repository.
- The setup page lists groups and forum status. Current importer/listener sync forum-topic messages and messages with supported video/resource links.
- Direct Telegram file uploads are not mirrored. PDF/Drive/Slides links are retained as links and their original sharing permissions still apply.
- The setup web service uses in-memory pending login state. If it restarts during the code-verification step, start login again.
