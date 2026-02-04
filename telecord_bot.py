"""
TeleCord Bot - Discord to Telegram bridge
Sends messages from Discord to a Telegram channel using python-telegram-bot.
"""

import html
import json
import logging
import re
from pathlib import Path

# Discord CDN attachment URLs (e.g. pasted in message content)
DISCORD_CDN_URL_PATTERN = re.compile(r"https://cdn\.discordapp\.com/attachments/\d+/\d+/[^\s)]+")

import discord
from telegram import Bot, InputMediaPhoto

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("telecord")


def load_config():
    config_path = Path(__file__).parent / "config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


class TeleCordBot(discord.Client):
    """Discord bot that forwards messages to Telegram via Bot API."""

    def __init__(self, config: dict):
        self.config = config

        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)

        telegram_config = config.get("telegram", config)
        self.telegram_bot = Bot(token=telegram_config["telegram_bot_token"])
        self.telegram_channel = telegram_config.get("telegram_channel", "@your_channel")

        raw_forward = config.get("channel_forward") or {}
        self.channel_forward = {int(k): v for k, v in raw_forward.items()}

    async def on_ready(self):
        logger.info("TeleCordBot logged on as %s", self.user)

    async def on_message(self, message: discord.Message):
        if not self.channel_forward:
            return

        if message.channel.id not in self.channel_forward:
            return

        telegram_target = self.channel_forward[message.channel.id]["telegram_channel_id"]
        author = message.author.display_name
        content = message.content

        if self.channel_forward[message.channel.id].get("show_channel_name"):
            author = f"#{message.channel.name} {author}"

        # Add Discord message URL as clickable link on author name
        author_html = f'<a href="{html.escape(message.jump_url)}">{html.escape(author)}</a>'

        # Get image URLs from attachments
        image_urls = [
            a.url
            for a in message.attachments
            if a.content_type and a.content_type.startswith("image/")
        ]

        # Also search for Discord CDN URLs pasted in message content
        if content:
            content_urls = [
                url.rstrip(".,;:!?)\"'") for url in DISCORD_CDN_URL_PATTERN.findall(content)
            ]
            image_urls.extend(content_urls)
            # Remove found URLs from content so they're not shown twice
            content = DISCORD_CDN_URL_PATTERN.sub("", content).strip()
            content = re.sub(r"\n{3,}", "\n\n", content)  # collapse extra newlines

        formatted = (
            f"<b>{author_html}:</b>\n{html.escape(content)}"
            if content
            else f"<b>{author_html}:</b>"
        )

        if not content and not image_urls:
            return

        try:
            if image_urls:
                # Send first image as embedded photo with caption
                await self.telegram_bot.send_photo(
                    chat_id=telegram_target,
                    photo=image_urls[0],
                    caption=formatted,
                    parse_mode="HTML",
                )
                # Send remaining images as media group (no caption on extras)
                if len(image_urls) > 1:
                    media_group = [InputMediaPhoto(media=url) for url in image_urls[1:]]
                    await self.telegram_bot.send_media_group(
                        chat_id=telegram_target,
                        media=media_group,
                    )
            else:
                await self.telegram_bot.send_message(
                    chat_id=telegram_target,
                    text=formatted,
                    parse_mode="HTML",
                )
            logger.info("Forwarded from #%s to %s", message.channel.name, telegram_target)
        except Exception:
            logger.error("Failed to forward message", exc_info=True)


def main():
    config = load_config()

    discord_token = config.get("discord_bot_token") or config.get("discord", {}).get("bot_token")
    if not discord_token:
        raise ValueError("discord_bot_token required in config.json")

    bot = TeleCordBot(config)
    bot.run(discord_token)


if __name__ == "__main__":
    main()
