# Class 29 · Personal Edition

Class 29 is intended for one owner. The website and class data are served through a password-protected Render web service. Telegram messages are read by a separate Render background worker. The worker writes extracted class links to a **private GitHub repository**.

## Before deploying
1. In GitHub, change this repository to **Private**: Settings → General → Danger Zone → Change repository visibility. Confirm the change. This is essential; otherwise the class JSON and source code remain public.
2. Disable GitHub Pages in Settings → Pages. The site is no longer hosted on GitHub Pages.
3. Ensure your fine-grained GitHub token is restricted to this repository and has Contents: Read and write. After changing the repository to private, verify that the token still grants access. If not, create a replacement token for the private repository and store it only in Render.

## Deploy
1. In Render, create a Blueprint from this private repository using `render.yaml`.
2. For the web service, set:
   - `CLASS29_PASSWORD`: a unique password with at least 16 characters.
   - `CLASS29_SECRET_KEY`: a long random secret (at least 32 random bytes).
   - `TELEGRAM_API_ID` and `TELEGRAM_API_HASH`.
   - `GITHUB_TOKEN`: the private-repository token.
3. For the worker, set:
   - `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE`
   - `TELEGRAM_SESSION` and `TELEGRAM_GROUPS_JSON` from the protected setup page.
   - `GITHUB_TOKEN` with Contents: Read and write on this private repo.
4. Deploy both services. Open the Render web service URL. Sign in with your Class 29 password, then open Connect Telegram.

## Security model
- The web app uses a signed, HttpOnly, Secure, SameSite=Strict cookie with a 14-day lifetime. The password is checked server-side and is not stored in the browser.
- All site pages, static assets, class data API, and Telegram setup routes require the owner cookie. Only the login page and health check are public.
- Telegram session, API hash, GitHub token, site password, and cookie-signing key belong only in private Render environment variables. Never commit them or paste them into chat.
- The setup flow returns the Telethon session to the signed-in browser so the owner can copy it directly into the worker's private environment. The session grants account access and must be treated like a password.
- GitHub repo and JSON data must remain private. A private repository is not a substitute for protecting Render credentials.
- Use a unique password and signing key. If you suspect exposure, change the password/signing key and revoke the Telegram session from Telegram Settings → Devices.
- Render hosts the application and processes credentials; only proceed if you accept that hosting trust. Enable MFA on GitHub and Render accounts.

## Data handling
- Only YouTube URLs and ordinary resource links in selected group messages are collected.
- Google Drive/Slides/Docs/PDF links are stored as links, not copied files. Their original sharing permissions still apply.
- Telegram direct file uploads are not mirrored by the current importer.
- The worker does not download all Telegram history; the importer must be run separately to backfill older classes.
