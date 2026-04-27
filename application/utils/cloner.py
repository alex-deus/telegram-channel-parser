import asyncio
import json
import pathlib
import re
import shutil
from random import uniform
from typing import Literal

import click
from botocore.client import BaseClient
from slugify import slugify
from telethon.sync import TelegramClient
from telethon.tl.custom import Dialog
from telethon.tl.types import Message, MessageMediaDocument
from tenacity import TryAgain, retry, stop_after_attempt, wait_exponential

from application.logger import KwargsLoggerAdapter, get_logger
from application.s3 import get_s3_client
from application.settings import settings

__all__ = ["main"]


async def main(
    phone: str,
    channel_id: int | None = None,
    channel_name: str | None = None,
    skip_exists: bool = True,
    messages_id: tuple[int, ...] = list,
    download_mode: Literal["all", "message", "file"] = "all",
) -> None:
    async with TelegramClient(str(settings.sessions_dir / phone), settings.api_id, settings.api_hash) as client:
        await client.start(phone)

        if channel_id and channel_id > 0:
            channel_id *= -1

        try:
            dialog: Dialog = [d for d in await client.get_dialogs() if d.id == channel_id or d.name == channel_name][0]
        except IndexError:
            return click.echo("Channel was not found", err=True)

        kwargs = {}
        if messages_id:
            kwargs["ids"] = messages_id

        async for message in client.iter_messages(dialog, **kwargs):  # type: Message
            logger = get_logger("main", prefix="", message_id=message.id)

            try:
                logger.info(">>> Processing Telegram message")
                await _process_message(client, dialog, message, skip_exists, download_mode)
                logger.info(">>> Processing Telegram message")
            except Exception as e:
                logger.exception(">>> Error occurred at processing")
                continue

            if settings.s3_needs:
                try:
                    logger.info("<<< Uploading to S3")
                    await _upload_folder(dialog, message)
                    logger.info("<<< Uploading to S3")
                except Exception as e:
                    logger.exception("Error occurred at uploading to S3")
                    continue

            logger.info("[+] Done", message_id=message.id)

            if settings.need_remove_folder:
                try:
                    folder = _get_message_folder(dialog, message)
                    await asyncio.to_thread(shutil.rmtree, folder, True)
                    logger.info(f"Folder {str(folder)} has been removed")
                except Exception as e:
                    logger.exception(f"Error occurred at removing {str(folder)}")

            await asyncio.sleep(settings.delay + uniform(1, 3))  # nosec: B311


async def _process_message(
    client: TelegramClient,
    dialog: Dialog,
    message: Message,
    skip_exists: bool = True,
    download_mode: Literal["all", "message", "file"] = "all",
) -> None:
    logger = get_logger("main", prefix="\t\t", message_id=message.id)

    folder = _get_message_folder(dialog, message)

    if skip_exists and folder.exists():
        return logger.info("Folder already exists, skip")

    folder.mkdir(parents=True, exist_ok=True)

    message_data_path = folder / "meta.json"
    try:
        if message_data_path.exists():
            message_data_path.unlink()

        with open(message_data_path, "w") as f:
            message_data = {"created": message.date.isoformat()}

            if message.edit_date:
                message_data["edit_date"] = message.edit_date.isoformat()

            if isinstance(message.media, (MessageMediaDocument,)):
                message_data["file_size"] = message.media.document.size

            json.dump(message_data, f, indent=4)

    except Exception as e:
        logger.exception("Error occurred at saving message.json")

    if message.message and download_mode in ["all", "message"]:
        message_text_path = folder / "message.txt"
        try:
            if message_text_path.exists():
                message_text_path.unlink()

            with open(message_text_path, "w") as f:
                f.write(message.message or "")

        except Exception as e:
            logger.exception("Error occurred at saving message.txt")

    if isinstance(message.media, (MessageMediaDocument,)) and download_mode in ["all", "file"]:
        await _download_media(folder, client, message)


@retry(stop=stop_after_attempt(settings.downloads_retry), wait=wait_exponential(min=4, max=60))
async def _download_media(current_path: pathlib.Path, client: TelegramClient, message: Message) -> None:
    logger = get_logger("main", prefix="\t\t", message_id=message.id)

    # Refresh media link for long downloading case
    message = await client.get_messages(message.chat_id, ids=message.id)

    file_name = re.sub(r"[^a-zA-Z0-9._\-/]", "_", message.media.document.attributes[0].file_name)
    file = current_path / "files" / file_name

    # Remove exists file
    if file.exists():
        logger.warning(f"{file.name=} already exists, removing")
        file.unlink()

    # Make downlaoding
    callback = lambda cur, total: print(f"{cur / 1024 / 1024:.2f}/{total / 1024 / 1024:.2f} MB", end="\r")
    try:
        logger.info(f"Start downloading {file.name=}")
        await client.download_media(message.media, file, progress_callback=callback)
        print("\n")  # For make output pretty
        logger.info(f"Finish downloading {file.name=}")
    except Exception as e:
        logger.exception(f"Error occurred at saving {file.name=}")

    # Check is file exists
    is_exists: bool = file.exists()
    if not is_exists:
        logger.warning(f"{file.name=} does not exist after download")
        raise TryAgain()

    # Check empty file case
    if file.stat().st_size == 0:
        logger.warning(f"{file.name=} is empty after download")
        raise TryAgain()


async def _upload_folder(dialog: Dialog, message: Message) -> None:
    logger = get_logger("main", prefix="\t\t", message_id=message.id)

    folder = _get_message_folder(dialog, message)

    # Folder does not exist
    if not folder.exists():
        return logger.warning(f"Folder {message.id=} does not exist")

    s3 = get_s3_client()

    for file in folder.rglob("*"):
        if file.is_file():
            _upload_file(logger, s3, file)


@retry(stop=stop_after_attempt(settings.s3_uploading_retry), wait=wait_exponential(min=3, max=60))
def _upload_file(logger: KwargsLoggerAdapter, s3: BaseClient, file) -> None:
    key = file.relative_to(settings.channels_dir).as_posix()

    try:
        logger.info(f"Start uploading {key=}")
        s3.upload_file(str(file), settings.s3_bucket, key)
        logger.info(f"Finish uploading {key=}")
    except Exception as e:
        logger.exception(f"Error occurred at uploading {key=}")


def _get_message_folder(dialog: Dialog, message: Message) -> pathlib.Path:
    folder = settings.channels_dir / f"{dialog.id * -1}_{slugify(dialog.name.strip())}" / f"{message.id}"

    return folder
