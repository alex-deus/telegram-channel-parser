# telegram-channel-parser

## Project Overview

CLI tool that downloads messages (text, metadata, media) from Telegram channels and optionally uploads them to S3.

**Tech stack**: Python 3.11, Telethon, Click, Pydantic-settings, boto3, Poetry

Entry point: `python cli.py`

---

## CLI Usage

### `run` — Download channel messages

```
python cli.py run [OPTIONS]
```

| Option | Short | Type | Default | Description |
|---|---|---|---|---|
| `--phone` | `-p` | str | — | Phone number for the Telegram session |
| `--channel-id` | `-i` | str | None | Numeric Telegram channel ID |
| `--channel-name` | `-n` | str | None | Channel display name |
| `--skip-exists` | — | flag | False | Skip messages whose local folder already exists |
| `--messages-id` | `-m` | str | None | Single message ID or range (see below) |
| `--download-mode` | — | choice | `all` | What to download: `all`, `message`, `file` |

At least one of `--channel-id` or `--channel-name` must be provided.

**`--messages-id` formats:**
- `<number>` — single message, e.g. `42`
- `<number1>-<number2>` — inclusive range, e.g. `100-200`
- `<number1>-_` — from `number1` to the end of the channel

**`--download-mode` values:**
- `all` — save `meta.json`, `message.txt`, and media files
- `message` — save `meta.json` and `message.txt` only
- `file` — save `meta.json` and media files only

### `sign-in` — Authenticate a phone number

```
python cli.py sign-in -p <phone>
```

Creates a `.session` file in `sessions_dir` for the given phone number.

---

## Configuration

All settings are loaded from environment variables (case-insensitive). Use a `.env` file or export them directly.

### Required

| Variable | Type | Description |
|---|---|---|
| `api_id` | int | Telegram API ID |
| `api_hash` | str | Telegram API hash |

### Optional — Parser

| Variable | Type | Default | Description |
|---|---|---|---|
| `delay` | int | `1` | Seconds to wait between messages |
| `channels_dir` | path | `./data/channels` | Root directory for downloaded channel data |
| `sessions_dir` | path | `./data/sessions` | Directory for Telegram session files |
| `downloads_retry` | int | `5` | Retry attempts for media downloads |
| `need_remove_folder` | bool | `False` | Delete the local message folder after S3 upload |

### Optional — S3

| Variable | Type | Default | Description |
|---|---|---|---|
| `s3_needs` | bool | `False` | Enable S3 upload after each message |
| `s3_endpoint_url` | str | None | S3-compatible endpoint URL |
| `s3_bucket` | str | None | Target bucket name |
| `s3_access_key_id` | str | None | S3 access key |
| `s3_secret_access_key` | str | None | S3 secret key |
| `s3_region` | str | `us-east-1` | S3 region |
| `s3_uploading_retry` | int | `5` | Retry attempts for S3 uploads |

---

## Data Layout

```
data/
  channels/
    {channel_id}_{slug}/          # e.g. 1234567890_my-channel
      {message_id}/               # e.g. 42
        meta.json                 # date, edit_date (if any), file_size (if media)
        message.txt               # message text (if present and mode includes message)
        files/
          {filename}              # downloaded media file
  sessions/
    {phone}.session               # Telethon session file
```

`channel_id` is the positive numeric ID; `slug` is the slugified channel name.

---

## S3 Integration

S3 upload is optional, controlled by `s3_needs=true`.

When enabled, after each message is processed locally, all files in that message's folder are uploaded to S3. The S3 key for each file is its path relative to `channels_dir` (e.g. `1234567890_my-channel/42/meta.json`).

If `need_remove_folder=true`, the local message folder is deleted after a successful S3 upload.

---

## Development Workflow

```bash
# Install dependencies
poetry install

# Format
black .
isort .

# Lint
flake8 .
bandit -r .

# Pre-commit hooks install(autoflake, isort, black, bandit)
pre-commit install

# Run before commit
pre-commit run --all-files
```

**Line length**: 120 characters (enforced by `black` and `isort`).
