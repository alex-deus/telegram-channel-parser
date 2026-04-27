#!/usr/bin/env python3
import asyncio
import logging

import click
import coloredlogs

from application.logger import KwargsFormatter
from application.utils.cloner import main as clone_channel
from application.utils.sign_in import main as sign_in_account


@click.group
def cli() -> None:
    logger = logging.getLogger("main")
    fmt = "[%(asctime)s] %(levelname)s %(message_id)s %(prefix)s%(message)s"
    coloredlogs.install(level="DEBUG", logger=logger, fmt=fmt)
    for handler in logger.handlers:
        handler.setFormatter(KwargsFormatter(fmt))


@cli.command("run")
@click.option("-p", "--phone")
@click.option("-i", "--channel-id", "channel_id", default=None, show_default=True)
@click.option("-n", "--channel-name", "channel_name", default=None, show_default=True)
@click.option("--skip-exists", "skip_exists", is_flag=True, default=False, show_default=True)
@click.option("-m", "--messages-id", "messages_id", type=str, default=None)
@click.option(
    "--download-mode", "download_mode", type=click.Choice(["all", "message", "file"]), default="all", show_default=True
)
def clone(
    phone: str,
    channel_id: int | None,
    channel_name: str | None,
    skip_exists: bool,
    messages_id: str | None,
    download_mode: str,
) -> None:
    if not any([channel_id, channel_name]):
        return click.echo("You need to set at least one of Channel ID or Channel Name", err=True)

    messages_ids = ()

    if messages_id:
        if "-" in messages_id:
            parts = messages_id.split("-")
            if len(parts) != 2:
                return click.echo("Invalid format for messages-id. Use: <number> or <number1>-<number2>", err=True)

            try:
                start = int(parts[0])
                end = int(parts[1])
            except ValueError:
                return click.echo("Invalid format for messages-id. Both parts must be numbers.", err=True)

            if start >= end:
                return click.echo("Invalid range: first number must be less than second number", err=True)

            messages_ids = (i for i in range(start, end))

            coro = clone_channel(phone, channel_id, channel_name, skip_exists, messages_ids, download_mode)
            asyncio.run(coro)
        else:
            try:
                messages_ids = (int(messages_id),)
            except ValueError:
                return click.echo("Invalid format for messages-id. Must be a number or range.", err=True)

    coro = clone_channel(phone, channel_id, channel_name, skip_exists, messages_ids, download_mode)
    asyncio.run(coro)


@cli.command("sign-in")
@click.option("-p", "--phone")
def sign_in(phone: str) -> None:
    coro = sign_in_account(phone)
    asyncio.run(coro)


if __name__ == "__main__":
    cli()
