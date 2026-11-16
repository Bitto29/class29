# Class 29

A personal, database-free library for class videos and shared slide/PDF links from multiple Telegram groups. The site is intentionally simple to open on both phone and PC without creating a separate website account.

## What it collects
- YouTube video links posted in configured group topics.
- Google Drive, Google Slides/Docs, direct PDF, and other ordinary URLs in the same Telegram message.
- Messages containing only a supported resource link are listed as materials-only entries.
- Group → Topic → Class organization, with each class showing its video and available material links.

## Architecture
Telegram groups (your own authorized Telegram user session) → persistent cloud listener → GitHub Contents API → data/classes.json → static website.

No database is used. The public website only displays extracted class titles and links, not the rest of Telegram messages.

## Current setup status
The static library and Telegram listener are in the repository. The current listener still requires its Telegram session, API credentials, selected group IDs, and GitHub token to be configured as private cloud environment variables. A browser-only Telegram connection and group-selection dashboard has not yet been implemented. No Telegram account is connected until you complete that authorization.

## Deployment
1. Enable GitHub Pages: Settings → Pages → Deploy from a branch → main → /(root).
2. Deploy the persistent worker using the included Render configuration.
3. Configure the required private environment variables in Render.

## Private cloud configuration
Required variables: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE, TELEGRAM_SESSION, TELEGRAM_GROUPS_JSON, GITHUB_TOKEN, GITHUB_REPOSITORY.

The GitHub token needs Contents: Read and write permission on this repository only. Never commit .env or a Telegram session, and never send tokens/session strings in chat.

The current setup still expects the Telegram session and selected group IDs to be configured by the service owner. The planned browser setup dashboard is a separate implementation step; do not assume it is available yet.

## PDF and slide links
The importer captures links present in Telegram message text and hidden URL entities. Google Drive, Google Slides/Docs, direct PDF, and other URLs are displayed under Class materials. This does not copy or host the PDF itself. The original link must be accessible to the website visitor. For private Drive files, change sharing to anyone-with-the-link or the visitor will need permission.

Telegram files uploaded directly (without an external link) are not downloaded or mirrored by this version.

## Public access and privacy
GitHub Pages is public. Anyone who has the URL can open the site, and the class titles, YouTube links, and extracted material links in data/classes.json are publicly readable. Not sharing the URL reduces discoverability but does not make it private. Use only content you have permission to share. Never put Telegram credentials, login codes, session strings, or GitHub tokens in the website or repository.

No separate website sign-up is required for the static library. Watch progress is stored locally in each browser, not synchronized across devices.

## Sync
The listener is designed for event-driven updates when Telegram delivers a new message. GitHub API and Pages/CDN caching may add a short delay. The worker is not active until deployed and configured.
