# TeleCord Bot

A Discord bot that forwards messages to Telegram channels.

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

1. Copy `config.json.example` to `config.json`
2. Add your Discord bot token (from [Discord Developer Portal](https://discord.com/developers/applications))
3. Add your Telegram bot token (from [@BotFather](https://t.me/BotFather))
4. Add your Telegram bot as admin to the target channel
5. Map Discord channel IDs to Telegram channel IDs in `channel_forward`

## Usage

```bash
python telecord_bot.py
```

Messages from the configured Discord channels will be forwarded to the corresponding Telegram channels. Image attachments and pasted Discord CDN URLs are sent as embedded photos.
