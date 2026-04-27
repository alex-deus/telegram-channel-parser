import logging

from telethon.sync import TelegramClient

from application.settings import settings

__all__ = ["main"]

logger = logging.getLogger("main")


async def main(phone: str) -> None:
    async with TelegramClient(str(settings.sessions_dir / phone), settings.api_id, settings.api_hash) as client:
        await client.start(phone)
        logger.info(f"Sing-in to {phone=}")
