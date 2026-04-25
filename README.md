# Telegram Video Downloader Agent

A production-style FastAPI service for a Telegram bot that accepts shared video links, queues them in FIFO order, downloads each video with `yt-dlp`, sends the result back to Telegram, and removes the downloaded file afterward.

## Features

- Telegram webhook endpoint at `/webhook`
- Single worker thread for strict sequential FIFO processing
- In-memory duplicate prevention
- `/status` command with queue size and worker state
- `/health` endpoint for server checks
- Automatic cleanup after sending videos
- Retry support for Telegram send operations

## Project Structure

```text
.
|-- main.py
|-- downloader.py
|-- queue_worker.py
|-- telegram_handler.py
|-- utils.py
|-- config.py
|-- requirements.txt
`-- README.md
```

## Setup

1. Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

On macOS or Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Install FFmpeg.

For Facebook and many Instagram links, `yt-dlp` often receives video and audio as separate streams. FFmpeg is required to merge them into a single MP4. Without FFmpeg, this project tries to download a ready-made MP4 stream, but some videos will fail until FFmpeg is installed and available in PATH.

On Windows, the simplest option is usually:

```powershell
winget install Gyan.FFmpeg
```

Then close and reopen your terminal and verify:

```bash
ffmpeg -version
```

4. Create a `.env` file:

```env
BOT_TOKEN=123456789:your_telegram_bot_token
BASE_URL=https://your-ngrok-url.ngrok-free.app
DOWNLOAD_FOLDER=downloads
```

## Run Server

Start the FastAPI app:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

For local Telegram webhook testing, expose the server with ngrok:

```bash
ngrok http 8000
```

Copy the HTTPS ngrok URL into `BASE_URL` in your `.env` file, then restart the server.

## Create Telegram Bot

1. Open Telegram and chat with `@BotFather`.
2. Send `/newbot`.
3. Follow the prompts.
4. Copy the bot token into `BOT_TOKEN` in `.env`.

## Set Webhook

Use this command after replacing the token and URL:

```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=<YOUR_BASE_URL>/webhook"
```

Example:

```bash
curl "https://api.telegram.org/bot123456789:ABC/setWebhook?url=https://your-ngrok-url.ngrok-free.app/webhook"
```

Check webhook status:

```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

## Example Usage

Send a supported video link to your Telegram bot:

```text
https://www.facebook.com/watch/?v=123456789
```

The bot will reply:

```text
Added to queue
Download started
Download completed
```

Send `/status` to see:

```text
Queue size: 0
Worker: idle
```

## Health Check

Open:

```text
http://localhost:8000/health
```

Example response:

```json
{
  "status": "running",
  "queue_size": 0
}
```

## Notes

- The queue is in memory. Restarting the server clears queued jobs and duplicate history.
- Only one worker is started, so links are processed sequentially without parallel downloads.
- Downloaded videos are stored in `DOWNLOAD_FOLDER` only while being processed, then deleted.
- Facebook, Instagram, and WhatsApp-shared links can require cookies or extra `yt-dlp` configuration depending on privacy, login, region, and age restrictions.
