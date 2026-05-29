# telegram-channel-parser

CLI tool that downloads messages (text, metadata, and media) from Telegram channels
to the local filesystem, organized by channel and message ID. Optionally uploads
downloaded content to an S3-compatible bucket after each message.

---

## Prerequisites

- Python 3.12+ (local path)
- Docker (Docker path)
- Telegram API credentials — obtain from <https://my.telegram.org>

---

## Configuration

Create a `.env` file in the project root:

```dotenv
# Required
API_ID=123456
API_HASH=your_api_hash_here

# Optional — parser
DELAY=1                       # seconds between messages (default: 1)
CHANNELS_DIR=./data/channels  # where downloaded data is stored
SESSIONS_DIR=./data/sessions  # where session files are stored

# Optional — S3 (leave unset to skip S3 upload)
S3_NEEDS=false
S3_ENDPOINT_URL=
S3_BUCKET=
S3_ACCESS_KEY_ID=
S3_SECRET_ACCESS_KEY=
```

---

## Local Setup

```bash
# Create and activate a virtual environment
pyenv virtualenv 3.12.1 telegram_channel_parser
pyenv activate telegram_channel_parser

# Equivalent manual steps:
pip install poetry
poetry install --no-root

pre-commit install
```

---

## Docker Setup

```bash
docker build -t telegram-channel-parser .  # Build the image
```

---

## Usage

### Step 1 — Sign in (required once per phone number)

**Local:**

```bash
python cli.py sign-in -p +1234567890
```

**Docker:**

```bash
docker run -it --rm \
  --env-file .env \
  -v "$(pwd)/data/sessions:/app/src/data/sessions" \
  telegram-channel-parser cli sign-in -p +1234567890
```

This creates `data/sessions/+1234567890.session`. The session is reused on
subsequent runs. **`run` will fail if no session file exists for the given phone.**

### Step 2 — Run the parser

**Local:**

```bash
python cli.py run -p +1234567890 -n channelname
```

**Docker:**

```bash
docker run -it --rm \
  --env-file .env \
  -v "$(pwd)/data/sessions:/app/src/data/sessions" \
  -v "$(pwd)/data/channels:/app/src/data/channels" \
  telegram-channel-parser cli run -p +1234567890 -n channelname
```
