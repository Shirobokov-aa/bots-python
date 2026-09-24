#!/usr/bin/env python3
"""One-shot Telethon login → print StringSession for .env TELEGRAM_SESSION.

Usage (from ChannelMirror/):
  python scripts/telethon_login.py
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession


async def main() -> None:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    api_id = int(os.getenv("TELEGRAM_API_ID") or "0")
    api_hash = os.getenv("TELEGRAM_API_HASH") or ""
    if not api_id or not api_hash:
        raise SystemExit("Set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env first")

    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.start()
    session = client.session.save()
    me = await client.get_me()
    print(f"logged in as @{me.username or me.id}")
    print("Put this into .env:")
    print(f"TELEGRAM_SESSION={session}")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
