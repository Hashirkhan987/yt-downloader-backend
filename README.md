# Render-ready Multi-platform Video Downloader Backend

This backend uses yt-dlp and includes FFmpeg inside the Docker image, so video/audio streams can be merged on Render when a platform provides separate streams.

## Endpoints

- `GET /` — service status
- `GET /api/health` — health check
- `POST /api/info` with `{ "url": "..." }` — metadata and available video formats
- `POST /api/download` with `{ "url": "...", "format_id": "..." }` — server-side file download

## Deploy on Render

Recommended: create a Web Service from this repository and select **Docker**. Render will use the included `Dockerfile`.

If deploying manually, use Docker as the runtime. The container installs FFmpeg automatically.

Auto Deploy is enabled when the Render service is connected to GitHub. Push changes to the connected branch and Render can rebuild/redeploy automatically.

## Frontend requirement

The frontend must use `/api/info` to show formats, but the actual Download button should call `/api/download` and handle the response as a file/blob. Do not use the `download_url` from `/api/info` as the final download mechanism because third-party media URLs can expire or be blocked by browser CORS.

## Limitations

No downloader can guarantee every URL on every platform forever. Platforms can change authentication, anti-bot systems, geo restrictions, or media delivery. Use only content you are authorized to download.
